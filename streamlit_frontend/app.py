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
            st.error(f"Failed to fetch products: Status code {response.status_code}, {response.json()}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return []

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
                st.write("Payload ready to send:", payload)
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
                st.write("Payload ready to send:", payload)
                add_request(payload=payload, section="categories")
                

def view_products_page():
    st.header("📦 Product Inventory")

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


    active_filters = {
        "limit": rows_per_page,
        "offset": calculated_offset, 
        "order_by": final_order_by   
    }
    
    if selected_category != "All":
        active_filters['category'] = selected_category
    if min_price > 0:
        active_filters['min_price'] = min_price
    if max_price > 0:
        active_filters['max_price'] = max_price
    if is_available:
        active_filters['is_available'] = is_available

    products = get_products(filters=active_filters)
    
    if not products:
        st.info("No products found matching those filters.")
        return
        
    df = pd.DataFrame(products)

    st.markdown("### Quick Stats")

    total_items = len(df)
    st.metric("Products on this page", total_items)

    st.markdown("### Product Catalog")

    column_order = ['name', 'brand', 'product_category', 'price', 'quantity']
    display_columns = [col for col in column_order if col in df.columns]

    df['quantity'] = df['quantity'].astype(int)
    styled_df = df[display_columns].style.apply(highlight_low_stock, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True 
    )


def remove_product_page():
    st.header("Remove Product")
    st.write("Second page content goes here.")



view_products = st.Page(view_products_page, title="View Products", icon="📦") 
add_product = st.Page(add_product_page, title="Add Product", icon="➕")
add_category = st.Page(add_category_page, title="Add Category", icon="📁")
remove_product = st.Page(remove_product_page, title="Remove Product", icon="🗑️")

pages = [view_products, add_product, add_category, remove_product]
pg = st.navigation(pages)

pg.run()