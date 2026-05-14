import streamlit as st
import requests
import pandas as pd 

def highlight_low_stock(row):
    if row['quantity'] < 5:
        return ['background-color: rgba(255, 75, 75, 0.2); color: white;'] * len(row)
    return [''] * len(row) 

def format_category(category):
    return f"{category['title']} - {category['description'][:30]}..."

@st.cache_data(ttl=300)
def get_categories():
    api_url = "http://127.0.0.1:8000/inventory/categories/"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: Status code {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while connecting to the API: {e}")
        return []

def add_request(payload, section):
    api_url = f"http://127.0.0.1:8000/inventory/{section}/"
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 201:
            st.success("Item Added Successfully")
        else:
            st.error(f"Failed (Status {response.status_code}): {response.json()}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while connecting to the API: {e}")
        return []

def get_products(filters=None):
    api_url = "http://127.0.0.1:8000/inventory/products/"
    try:
        response = requests.get(api_url, params=filters)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch products: Status code {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return None

def add_product_page():
    st.header("Add a New Product")
    
    fetched_categories = get_categories()

    with st.form("add_product_form"):
        name = st.text_input(label="Product Name", max_chars=200)
        description = st.text_area(label="Product Description", max_chars=500)
        brand = st.text_input(label="Brand", max_chars=200)
        price = st.number_input(label="Price", min_value=0.0, step=0.01, format="%.2f", value=0.0)
        quantity = st.number_input(label="Quantity", min_value=0, step=1)
        selected_category = None
        
        if fetched_categories:
            selected_category = st.selectbox(
                label="Product Category", 
                options=fetched_categories, 
                format_func=format_category
            )
        else:
            st.warning("No categories available. Please check the API.")

        submitted = st.form_submit_button("Save Product")
        
        if submitted:
            if not name or not brand or not selected_category:
                st.error("Please fill out all required fields (Name, Brand, Category).")
            else:
                payload = {
                    "name": name,
                    "description": description,
                    "brand": brand,
                    "price": price, 
                    "quantity": quantity,
                    "product_category": selected_category['title'] 
                }
                add_request(payload=payload, section="products")


def add_category_page():
    st.header("Add a New Product Category")

    with st.form("add_product_category_form"):
        title = st.text_input(label="Product Category Name", max_chars=200)
        description = st.text_area(label="Product Description", max_chars=500)

        submitted = st.form_submit_button("Save Product Category")
        
        if submitted:
            if not title or not description:
                st.error("Please fill out all required fields (Name, Description).")
            else:
                payload = {
                    "title": title,
                    "description": description,
                }
                add_request(payload=payload, section="categories")
                

def view_products_page():
    st.header("📦 Product Inventory")

    if 'similar_view_id' not in st.session_state:
        st.session_state.similar_view_id = None
        st.session_state.similar_view_name = None

    if st.session_state.similar_view_id is not None:
        st.subheader(f"🧩 Products similar to: {st.session_state.similar_view_name}")
        
        if st.button("⬅️ Back to All Products"):
            st.session_state.similar_view_id = None
            st.session_state.similar_view_name = None
            st.rerun()

        with st.spinner("Calculating vector embeddings..."):

            similar_url = f"http://127.0.0.1:8000/inventory/products/{st.session_state.similar_view_id}/similar/?limit=5"
            try:
                sim_response = requests.get(similar_url)
                if sim_response.status_code == 200:
                    sim_data = sim_response.json().get("results", [])
                    if sim_data:
                        sim_df = pd.DataFrame(sim_data)
                        st.success(f"Found {len(sim_df)} similar products!")
                        st.dataframe(
                            sim_df[['name', 'brand', 'product_category', 'price', 'quantity']], 
                            use_container_width=True, 
                            hide_index=True
                        )
                    else:
                        st.info("No similar products found in the database.")
                else:
                    st.error(f"Error fetching similar products: {sim_response.text}")
            except Exception as e:
                st.error(f"API connection failed: {str(e)}")

        return


    search_query = st.text_input("🔍 Semantic Search (e.g., 'durable hiking boots for winter')", value="")

    st.sidebar.header("Filter Products")

    fetched_categories = get_categories()
    category_options = ["All"] + [cat['title'] for cat in fetched_categories] if fetched_categories else ["All"]
    selected_category = st.sidebar.selectbox("Category", options=category_options)

    rows_per_page = st.sidebar.selectbox("No of Items Per Page", options=[10, 20, 50])
    page_number = st.sidebar.number_input("Page", min_value=1, value=1, step=1)
    calculated_offset = (page_number - 1) * rows_per_page

    is_available = st.sidebar.checkbox("In Stock")
    
    col1, col2 = st.sidebar.columns(2)
    min_price = col1.number_input("Min Price", value=0.0, step=10.0)
    max_price = col2.number_input("Max Price", value=0.0, step=10.0)

    order_by = st.sidebar.selectbox("Sort By", options=["price", "quantity"])
    sort_direction = st.sidebar.radio("Direction", ["Ascending", "Descending"])
    final_order_by = f"-{order_by}" if sort_direction == "Descending" else order_by

    st.sidebar.markdown("---")
    st.sidebar.header("🤖 AI Data Generator")
    
    scenarios = [
        "Holiday Rush (High Demand, Winter Toys)",
        "Summer Vacation (Outdoor Toys)",
        "Back to School (STEM Toys)",
        "Clearance (Low Stock, Random Assortment)"
    ]
    
    with st.sidebar.form("scenario_form"):
        st.caption("Generate synthetic products directly into the database.")
        selected_scenario = st.selectbox("Scenario", scenarios)
        custom_scenario = st.text_input("Or custom scenario:")
        
        generate_btn = st.form_submit_button("Populate Data")
        
        if generate_btn:
            final_scenario = custom_scenario if custom_scenario.strip() else selected_scenario
            
            with st.spinner(f"Gemini is generating '{final_scenario}'..."):
                api_url = "http://127.0.0.1:8000/inventory/scenarios/"
                payload = {"scenario": final_scenario}
                
                try:
                    response = requests.post(api_url, json=payload)
                    if response.status_code == 201:
                        st.sidebar.success("✅ Products added!")
                        st.rerun() 
                    else:
                        st.sidebar.error(f"Failed: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.sidebar.error("API Connection Error.")

    active_filters = {
        "limit": rows_per_page,
        "offset": calculated_offset, 
        "order_by": final_order_by   
    }
    
    if search_query.strip():
        active_filters['q'] = search_query.strip()
    if selected_category != "All":
        active_filters['category'] = selected_category
    if min_price > 0:
        active_filters['min_price'] = min_price
    if max_price > 0:
        active_filters['max_price'] = max_price
    if is_available:
        active_filters['is_available'] = is_available

    response_data = get_products(filters=active_filters)
    
    if not response_data:
        return 

    products = response_data.get("results", []) if isinstance(response_data, dict) else response_data
    
    if not products:
        st.info("No products found matching those filters.")
        return

    st.markdown("### Quick Stats")
    total_count = response_data.get("count", len(products)) if isinstance(response_data, dict) else len(products)
    st.metric("Products Found", total_count)

    st.markdown("### Product Catalog")

    header_cols = st.columns([3, 2, 2, 1, 1, 2])
    header_cols[0].markdown("**Name**")
    header_cols[1].markdown("**Brand**")
    header_cols[2].markdown("**Category**")
    header_cols[3].markdown("**Price**")
    header_cols[4].markdown("**Stock**")
    header_cols[5].markdown("**Action**")
    st.divider()

    for index, p in enumerate(products):
        cols = st.columns([3, 2, 2, 1, 1, 2])
        cols[0].write(p.get('name', 'N/A'))
        cols[1].write(p.get('brand', 'N/A'))
        cols[2].write(p.get('product_category', 'N/A'))
        cols[3].write(f"${p.get('price', 0.0)}")
        
        qty = int(p.get('quantity', 0))
        if qty < 5:
            cols[4].error(f"{qty}")
        else:
            cols[4].write(f"{qty}")

        p_id = p.get('id') or p.get('_id')

        button_key = f"sim_{p_id}_{index}"
        
        if cols[5].button("Find Similar", key=button_key, use_container_width=True):
            if p_id: 
                st.session_state.similar_view_id = p_id
                st.session_state.similar_view_name = p.get('name', 'Product')
                st.rerun()
            else:
                st.error("Cannot search: Product ID is missing from the API.")

    st.divider()

def remove_product_page():
    st.header("Remove Product")
    st.write("Second page content goes here.")

def ask_expert_page():
    st.header("🤖 Ask the Expert")
    st.write("Ask me anything about our products, live inventory, return policies, or vendor FAQs!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your AI store manager. How can I help you today?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("E.g., What is the warranty on the Lego Castle, and is it in stock?"):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Searching database and documents..."):
                chat_url = "http://127.0.0.1:8000/inventory/api/chat/"
                try:
                    response = requests.post(chat_url, json={"query": prompt})
                    if response.status_code == 200:
                        bot_response = response.json().get("response", "No response found.")
                    else:
                        error_json = response.json()
                        error_msg = error_json.get('error', 'Unknown Error')
                        bot_response = f"🚨 **Agent Error:** {error_msg}"
                except Exception as e:
                    bot_response = f"API Connection Error: Could not reach the chatbot endpoint. ({str(e)})"
            
            message_placeholder.markdown(bot_response)
            
        st.session_state.messages.append({"role": "assistant", "content": bot_response})


view_products = st.Page(view_products_page, title="View Products", icon="📦") 
add_product = st.Page(add_product_page, title="Add Product", icon="➕")
add_category = st.Page(add_category_page, title="Add Category", icon="📁")
remove_product = st.Page(remove_product_page, title="Remove Product", icon="🗑️")
ask_expert = st.Page(ask_expert_page, title="Ask the Expert", icon="💬") 

pages = [view_products, ask_expert, add_product, add_category, remove_product]
pg = st.navigation(pages)

pg.run()