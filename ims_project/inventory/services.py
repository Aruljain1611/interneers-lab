from typing import Dict, Any, Optional
from .repositories import ProductRepository, ProductCategoryRepository
from .models import Product, ProductCategory, ProductQuerySet, ProductCategoryQuerySet
from django.conf import settings 
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, Optional
from .repositories import ProductRepository, ProductCategoryRepository
from .models import Product, ProductCategory, ProductQuerySet, ProductCategoryQuerySet
import os
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from .repositories import KnowledgeBaseRepository
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

class QuoteInvoice(BaseModel):
    matched_product: str
    product_id: str
    quantity_requested: int
    inventory_available: int
    unit_price: float
    subtotal: float
    discount_percent: float
    discount_amount: float
    final_price: float
    status: str

class AIProduct(BaseModel):
    name: str
    description: str
    brand: str
    price: float
    quantity: int
    product_category: str

class AIProductResponse(BaseModel):
    products: list[AIProduct]


class ProductService:

    def __init__(self) -> None:
        self.product_repository: ProductRepository = ProductRepository()
        self.category_repository: ProductCategoryRepository = ProductCategoryRepository()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.kb_service = KnowledgeBaseService()
        self.filter_map = {
            'min_price': 'price__gte',
            'max_price': 'price__lte',
            'category': 'product_category',
            'brand': 'brand',
            'is_available': 'quantity__gt',
            'offset': 'offset',
            'limit': 'limit',
            'order_by': 'order_by'
        }

    def _generate_embedding(self, name: str, brand: str, description: str) -> list[float]:
        embedding_string: str = f"Name: {name}\nBrand: {brand}\nDescription: {description}"
        return self.encoder.encode(embedding_string).tolist()
    
    def _convert_to_mql(self, db_filters: Dict[str, Any]) -> Dict[str, Any]:
        mql_filter = {}
        for key, value in db_filters.items():
            if '__' in key:
                field, op = key.split('__')
                if field not in mql_filter:
                    mql_filter[field] = {}
                mql_filter[field][f"${op}"] = value
            else:
                mql_filter[key] = value
        return mql_filter
    
    def create_new_product(self, validated_product_data: Dict[str, Any]) -> Product:
        embedding_string: str = (
            f"Name: {validated_product_data['name']}\n"
            f"Brand: {validated_product_data['brand']}\n"
            f"Description: {validated_product_data['description']}"
        )
        embeddings: list[float] = self.encoder.encode(embedding_string).tolist()

        validated_product_data["embedding"] = embeddings
        return self.product_repository.add(validated_product_data)

    def update_existing_product(self, product_id: str, update_data: Dict[str, Any]) -> Product:
        old_product: Optional[Product] = self.product_repository.get_by_id(product_id=product_id)

        if not old_product:
            raise ValueError(f"Product {product_id} not found.")

        return self.product_repository.update(old_product, update_data)

    def get_products(self, validated_filters: Dict[str, Any], search_text: Optional[str] = None) -> ProductQuerySet:
        
        db_filters = {}
        modifiers = {}

        for frontend_key, value in validated_filters.items():
            db_key = self.filter_map.get(frontend_key)

            if not db_key:
                continue

            if frontend_key in ['limit', 'offset', 'order_by']:
                modifiers[db_key] = value
                
            elif frontend_key == 'is_available':
                if value is True:
                    db_filters['quantity__gt'] = 0
                elif value is False:
                    db_filters['quantity__gte'] = 0 

            else:
                db_filters[db_key] = value

        if search_text and search_text.strip():
            query_embedding = self.encoder.encode(search_text).tolist()
            mql_filters = self._convert_to_mql(db_filters)
            limit = modifiers.get('limit', 10)
            
            return self.product_repository.vector_search_with_filters(
                query_vector=query_embedding, 
                mql_filters=mql_filters, 
                limit=limit
            )
        else:
            return self.product_repository.get_all(filters=db_filters, modifiers=modifiers)

    def delete_product_record(self, product_id: str) -> bool:
        success: bool = self.product_repository.remove(product_id)
        if not success:
            raise ValueError(f"Delete failed: Product {product_id} not found.")
        return True
    
    def generate_scenario_products(self, scenario: str) -> int:
        GEMINI_API_KEY: str = getattr(settings, 'GEMINI_API_KEY', None)
        client = genai.Client(api_key=GEMINI_API_KEY) 
        
        prompt = (
            f"Generate 5 distinct toy store products for the following scenario: '{scenario}'. "
            "If it is a busy season (like Holiday Rush), set high stock quantities (e.g., 100-500). "
            "If it is an off-season, set lower quantities. Ensure diverse categories."
        )
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=1.0,
                    response_json_schema=AIProductResponse.model_json_schema(),
                    response_mime_type="application/json"
                )
            )
        except Exception as e:
            raise ValueError(f"AI Generation failed: {str(e)}")
        
        try:
            ai_data = AIProductResponse.model_validate_json(response.text)
            saved_products: int = 0
            
            for ai_product in ai_data.products:
                product_dict = ai_product.model_dump()
                saved_instance = self.create_new_product(product_dict)
                saved_products += 1
                
            return saved_products
        except Exception as e:
            raise ValueError(f"Failed to save AI generated products: {str(e)}")
        
    def get_similar_products(self, product_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        target_product: Optional[Product] = self.product_repository.get_by_id(product_id)
        
        if not target_product:
            raise ValueError(f"Product {product_id} not found.")
            
        query_embedding = getattr(target_product, 'embedding', None)
        
        if not query_embedding:
            raise ValueError("Target product does not have a vector embedding.")

        mql_filters = {"_id": {"$ne": target_product.id}}

        return self.product_repository.vector_search_with_filters(
            query_vector=query_embedding, 
            mql_filters=mql_filters, 
            limit=limit
        )

    def search_products(self, query: str, limit: int = 3) -> list[dict]:
    
        results = self.get_products(
            validated_filters={"limit": limit},
            search_text=query
        )

        return results

    def get_product_info(self, product_id: str) -> dict:

        product = self.product_repository.get_by_id(product_id)

        if not product:
            raise ValueError(f"Product {product_id} not found.")

        return {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "description": product.description,
            "price": float(product.price),
            "quantity": product.quantity,
            "product_category": product.product_category
        }

    def ask_the_expert_agent(self, user_query: str) -> str:
        GEMINI_API_KEY: str = getattr(settings, 'GEMINI_API_KEY', None)

        @tool(description="""
        MANDATORY FIRST STEP for ALL product and quotation requests.

        This tool:
        - identifies products from natural language
        - returns product IDs
        - returns pricing
        - returns inventory availability

        IMPORTANT:
        You MUST use the returned product_id
        when calling calculate_quote.
        """)

        def query_live_inventory(product_description: str) -> str:

            try:

                results = self.get_products(
                    validated_filters={"limit": 3},
                    search_text=product_description
                )

                if not results:
                    return "No matching products found."

                formatted_results = []

                for item in results:

                    formatted_results.append({
                        "product_id": item.get("_id"),
                        "name": item.get("name"),
                        "price": float(item.get("price")),
                        "available_quantity": item.get("quantity")
                    })

                return json.dumps(formatted_results, indent=2)

            except Exception as e:
                return f"Inventory tool error: {str(e)}"

        @tool(description="MANDATORY for all questions about return policies, shipping, refunds, store rules, and product manuals.")
        def fetch_store_policies_and_manuals(search_query: str) -> str:
            try:
                chunks = self.kb_service.retrieve_relevant_chunks(search_query, top_k=3)
                if not chunks:
                    return "The knowledge base contains no documents related to this search."
                return "Official Store Policy Content:\n\n" + "\n\n".join(chunks)
            except Exception as e:
                return f"Knowledge Base tool error: {str(e)}"
            

        @tool(description="""
        MANDATORY for ALL quotation requests.

        Calculates:
        - subtotal
        - discounts
        - final pricing

        Discount Rules:
        - 5 off above 20 units
        - 10off above 50 units
        - 20 off above 100 units
        """)
        def calculate_quote(product_id: str, quantity: int) -> str:

            try:

                product = self.product_repository.get_by_id(product_id)

                if not product:
                    return f"Product {product_id} not found."

                available_quantity = product.quantity

                if quantity > available_quantity:
                    return (
                        f"Insufficient inventory. "
                        f"Only {available_quantity} units available."
                    )

                unit_price = float(product.price)

                subtotal = unit_price * quantity

                discount_percent = 0

                if quantity > 100:
                    discount_percent = 20

                elif quantity > 50:
                    discount_percent = 10

                elif quantity > 20:
                    discount_percent = 5

                discount_amount = subtotal * (discount_percent / 100)

                final_price = subtotal - discount_amount

                quote = {
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "quantity_requested": quantity,
                    "inventory_available": available_quantity,
                    "unit_price": round(unit_price, 2),
                    "subtotal": round(subtotal, 2),
                    "discount_percent": discount_percent,
                    "discount_amount": round(discount_amount, 2),
                    "final_price": round(final_price, 2),
                    "status": "Quote Generated Successfully"
                }

                return json.dumps(quote, indent=2)

            except Exception as e:
                return f"Quote calculation error: {str(e)}"

        tools = [query_live_inventory, fetch_store_policies_and_manuals, calculate_quote]
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0, 
            google_api_key=GEMINI_API_KEY
        )

        system_instructions = (
            "You are the Official Toy Store AI Manager. "
            "CRITICAL: You have NO internal knowledge of store policies or stock. "
            "You MUST use 'fetch_store_policies_and_manuals' for returns/shipping/manuals. "
            "You MUST use 'query_live_inventory' for stock/prices."
            "You must use query_live_inventory first to find the product requested and then calculate_quote for giving quotes to the consumer."
        )

        agent_executor = create_react_agent(
            llm, 
            tools, 
            prompt=system_instructions,
            debug = True
        )

        try:
            response = agent_executor.invoke(
                {"messages": [HumanMessage(content=user_query)]}
            )
            final_message = response["messages"][-1].content

            if isinstance(final_message, list):

                extracted_text = []

                for item in final_message:

                    if isinstance(item, dict) and item.get("type") == "text":
                        extracted_text.append(item.get("text", ""))

                return "\n".join(extracted_text)

            return str(final_message)
        except Exception as e:

            raise ValueError(f"AI Agent failed: {str(e)}")

class ProductCategoryService:
    def __init__(self) -> None:
        self.category_repository: ProductCategoryRepository = ProductCategoryRepository()

    def create_new_category(self, validated_category_data: Dict[str, Any]) -> ProductCategory:
        return self.category_repository.add(validated_category_data)

    def update_existing_category(self, title: str, update_data: Dict[str, Any]) -> ProductCategory:
        old_category: Optional[ProductCategory] = self.category_repository.get_by_title(title=title)
        
        if not old_category:
            raise ValueError(f"Category '{title}' not found.")

        return self.category_repository.update(old_category, update_data)

    def get_all_categories(self) -> ProductCategoryQuerySet:
        return self.category_repository.get_all()

    def delete_category_record(self, title: str) -> bool:
        success: bool = self.category_repository.remove(title)
        if not success:
            raise ValueError(f"Delete failed: Category '{title}' not found.")
        return True
    

class KnowledgeBaseService:
    def __init__(self) -> None:
        self.repository = KnowledgeBaseRepository()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

    def ingest_documents_to_mongodb(self, folder_path: str = "docs") -> int:
        file_paths = [
            f"{folder_path}/product_manual.txt",
            f"{folder_path}/return_policy.txt",
            f"{folder_path}/vendor_faq.txt"
        ]
        
        self.repository.remove_all()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        total_saved = 0
        
        for path in file_paths:
            if not os.path.exists(path):
                continue
                
            loader = TextLoader(path)
            chunks = text_splitter.split_documents(loader.load())
            
            for chunk in chunks:
                embedding = self.encoder.encode(chunk.page_content).tolist()
                data = {
                    "source_file": chunk.metadata.get("source", "Unknown"),
                    "content": chunk.page_content,
                    "embedding": embedding
                }
                self.repository.add(data)
                total_saved += 1
                
        return total_saved

    def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> list[str]:
        query_embedding = self.encoder.encode(query).tolist()
        results = self.repository.vector_search(query_embedding, limit=top_k)
        return [item.get('content', '') for item in results] 