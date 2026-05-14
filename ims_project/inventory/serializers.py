from typing import Dict, Any
from rest_framework import serializers
from .repositories import ProductRepository, ProductCategoryRepository
from .models import Product, ProductCategory  

class ProductSerializer(serializers.Serializer):
    id = serializers.CharField(read_only= True)
    name = serializers.CharField(required=True, max_length=200)
    description = serializers.CharField(required=True, max_length=500)
    brand = serializers.CharField(required=True, max_length=200)
    price = serializers.DecimalField(required = True, min_value=0, max_digits=8, decimal_places=2)
    quantity = serializers.IntegerField(required = True, min_value=0)
    product_category = serializers.CharField(required = True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductCategorySerializer(serializers.Serializer):

    title = serializers.CharField(required=True, max_length=200)
    description = serializers.CharField(max_length=400)

class ProductFilterSerializer(serializers.Serializer):
    
    category = serializers.CharField(required= False, max_length = 200)
    brand = serializers.CharField(required = False, max_length = 200)
    min_price = serializers.DecimalField(required = False, min_value=0, max_digits=8, decimal_places=2)
    max_price = serializers.DecimalField(required = False, min_value=0, max_digits=8, decimal_places=2)
    is_available = serializers.BooleanField(required = False)
    offset = serializers.IntegerField(required = True, min_value = 0)
    limit = serializers.IntegerField(required = True, min_value = 10, max_value = 50)
    order_by = serializers.CharField(required = False, max_length = 200)
    q = serializers.CharField(required = False, max_length = 200)