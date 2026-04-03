from typing import Dict, Any, Optional
from .repositories import ProductRepository, ProductCategoryRepository
from .models import Product, ProductCategory, ProductQuerySet, ProductCategoryQuerySet


from typing import Dict, Any, Optional
from .repositories import ProductRepository, ProductCategoryRepository
from .models import Product, ProductCategory, ProductQuerySet, ProductCategoryQuerySet


class ProductService:

    def __init__(self) -> None:
        self.product_repository: ProductRepository = ProductRepository()
        self.category_repository: ProductCategoryRepository = ProductCategoryRepository()

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

    def create_new_product(self, validated_product_data: Dict[str, Any]) -> Product:
        return self.product_repository.add(validated_product_data)

    def update_existing_product(self, product_id: str, update_data: Dict[str, Any]) -> Product:
        old_product: Optional[Product] = self.product_repository.get_by_id(product_id=product_id)

        if not old_product:
            raise ValueError(f"Product {product_id} not found.")

        return self.product_repository.update(old_product, update_data)

    def get_products(self, validated_filters: Dict[str, Any]) -> ProductQuerySet:
        
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

        return self.product_repository.get_all(filters=db_filters, modifiers=modifiers)

    def delete_product_record(self, product_id: str) -> bool:
        success: bool = self.product_repository.remove(product_id)
        if not success:
            raise ValueError(f"Delete failed: Product {product_id} not found.")
        return True
    

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
    
    