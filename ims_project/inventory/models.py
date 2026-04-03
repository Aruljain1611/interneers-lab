from __future__ import annotations  
from typing import Optional, Dict, Any
from mongoengine import Document, StringField, IntField, DecimalField, QuerySet, DateTimeField
import datetime

class ProductQuerySet(QuerySet):
    
    def create_product(self, data: Dict[str, Any]) -> Product:
        product: Product = self._document(**data)
        product.save()
        return product
    
    def product_fetch(self, id: str) -> Optional[Product]:
        try:
            return self.get(id=id)
        except (self._document.DoesNotExist, Exception):
            return None 
            
    def get_filtered_products(self, filters: dict, modifiers: dict) -> 'ProductQuerySet':
        queryset = self.filter(**filters)
        if 'order_by' in modifiers:
            queryset = queryset.order_by(modifiers['order_by'])
        if 'offset' in modifiers:
            queryset = queryset.skip(modifiers['offset'])
        if 'limit' in modifiers:
            queryset = queryset.limit(modifiers['limit'])
            
        return queryset
    

    def delete_product(self, id: str) -> bool:
        try:
            product: Product = self.get(id=id)
            product.delete()
            return True
        except self._document.DoesNotExist:
            return False 


class ProductCategoryQuerySet(QuerySet):

    def create_product_category(self, data: Dict[str, Any]) -> ProductCategory:
        product_category: ProductCategory = self._document(**data)
        product_category.save()
        return product_category
    
    def product_category_fetch(self, title: str) -> Optional[ProductCategory]:
        try:
            return self.get(title=title)
        except (self._document.DoesNotExist, Exception):
            return None 

    def fetch_all(self) -> ProductCategoryQuerySet:
        return self.all()
    
    def delete_product_category(self, title: str) -> bool:
        try:
            product_category: ProductCategory = self.get(title=title)
            product_category.delete()
            return True
        except self._document.DoesNotExist:
            return False 


class ProductCategory(Document):
    def __str__(self) -> str:
        return str(self.title)
    
    title = StringField(required=True, max_length=200)
    description = StringField(max_length=400)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'queryset_class': ProductCategoryQuerySet, "collection": "product_categories"}

    def update_fields(self, data: Dict[str, Any]) -> ProductCategory:
        self.updated_at = datetime.datetime.utcnow()
        for field, value in data.items():
            if hasattr(self, field):
                setattr(self, field, value)

        self.save()
        return self


class Product(Document):
    def __str__(self) -> str:
        return str(self.name)

    name = StringField(required=True, max_length=200)
    description = StringField(required=True, max_length=500)
    brand = StringField(required=True, max_length=200)
    price = DecimalField(min_value=0, precision=2)
    quantity = IntField(min_value=0)
    product_category = StringField(max_length=200, required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'products', 'queryset_class': ProductQuerySet}

    def update_fields(self, data: Dict[str, Any]) -> Product:
        self.updated_at = datetime.datetime.utcnow()
        for field, value in data.items():
            if hasattr(self, field):
                setattr(self, field, value)

        self.save()
        return self