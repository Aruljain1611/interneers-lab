from typing import Dict, Any, Optional
from .models import Product, ProductCategory, ProductCategoryQuerySet, ProductQuerySet, KnowledgeDocumentQuerySet, KnowledgeDocument
from mongoengine.errors import InvalidQueryError, OperationError

class ProductRepository:

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return Product.objects.product_fetch(id=product_id)

    def get_all(self, filters: Dict[str, Any] = None, modifiers: Dict[str, Any] = None) -> ProductQuerySet:
        filters = filters or {}
        modifiers = modifiers or {}
        
        try:
            return Product.objects.get_filtered_products(filters, modifiers)
            
        except InvalidQueryError as e:
            raise ValueError(f"Invalid query parameters: {str(e)}")

        except Exception as e:
            raise ValueError(f"An unexpected error occurred while fetching products: {str(e)}")
        


    def vector_search_with_filters(self, query_vector: list[float], mql_filters: Dict[str, Any], limit: int = 10) -> list[Dict[str, Any]]:
        try:
            return Product.objects.vector_search_with_filters(
                query_vector=query_vector, 
                mql_filters=mql_filters, 
                limit=limit
            )
        except Exception as e:
            raise ValueError(f"Vector search failed: {str(e)}")

    def add(self, data: Dict[str, Any]) -> Product:
        try:
            return Product.objects.create_product(data)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Repository Error: {str(e)}")

    def update(self, instance: Product, data: Dict[str, Any]) -> Product:        
        return instance.update_fields(data)

    def remove(self, product_id: str) -> bool:
        return Product.objects.delete_product(id=product_id)
    

class ProductCategoryRepository:

    def get_by_title(self, title: str) -> Optional[ProductCategory]:
        return ProductCategory.objects.product_category_fetch(title=title)

    def get_all(self) -> ProductCategoryQuerySet:
        return ProductCategory.objects.fetch_all()

    def add(self, data: Dict[str, Any]) -> ProductCategory:
        try:
            return ProductCategory.objects.create_product_category(data)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Repository Error: {str(e)}")

    def update(self, instance: ProductCategory, data: Dict[str, Any]) -> ProductCategory:
        return instance.update_fields(data)

    def remove(self, title: str) -> bool:
        return ProductCategory.objects.delete_product_category(title=title)
    

class KnowledgeBaseRepository:

    def add(self, data: Dict[str, Any]) -> KnowledgeDocument:
        try:
            return KnowledgeDocument.objects.add_chunk(data)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Repository Error saving document chunk: {str(e)}")

    def vector_search(self, query_vector: list[float], limit: int = 3) -> list[Dict[str, Any]]:
        try:
            return KnowledgeDocument.objects.vector_search(
                query_vector=query_vector, 
                limit=limit
            )
        except Exception as e:
            raise ValueError(f"Knowledge Base Vector search failed: {str(e)}")

    def remove_all(self) -> bool:
        try:
            KnowledgeDocument.objects.clear_all_chunks()
            return True
        except Exception as e:
            raise ValueError(f"Failed to clear knowledge base: {str(e)}")