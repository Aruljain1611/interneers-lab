import json
from typing import Dict, Any, List, Optional
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from .services import ProductService, ProductCategoryService
from .serializers import ProductSerializer, ProductCategorySerializer, ProductFilterSerializer
from .models import Product, ProductCategory, ProductQuerySet, ProductCategoryQuerySet

product_service: ProductService = ProductService()
category_service: ProductCategoryService = ProductCategoryService()

def handle_value_error(e: Exception, status_code: int = 400) -> JsonResponse:
    error_detail: str = str(e.args[0]) if e.args else "An error occurred"
    return JsonResponse({"error": error_detail}, status=status_code)


class ProductView:  

    @csrf_exempt
    def product_collection_view(self, request: HttpRequest) -> JsonResponse:
        if request.method == 'POST':
            try:
                data: Dict[str, Any] = json.loads(request.body)
                serializer: ProductSerializer = ProductSerializer(data=data)
                
                if serializer.is_valid():
                    product : Product = product_service.create_new_product(serializer.validated_data)
                    return JsonResponse({"id": str(product.id)}, status=201)
                
                return JsonResponse(serializer.errors, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)
            except ValueError as e:
                return handle_value_error(e)

        elif request.method == 'GET':
            filters_serializer: ProductFilterSerializer = ProductFilterSerializer(data=request.GET)
            
            if filters_serializer.is_valid():
                products: ProductQuerySet = product_service.get_products(filters_serializer.validated_data)
                product_serializer = ProductSerializer(products, many=True)
                return JsonResponse(product_serializer.data, safe=False, status=200)
            return JsonResponse(filters_serializer.errors, status=400)

        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

    @csrf_exempt
    def product_detail_view(self, request: HttpRequest, product_id: str) -> JsonResponse:
        if request.method == "PATCH":
            try:
                data: Dict[str, Any] = json.loads(request.body)
                serializer: ProductSerializer = ProductSerializer(data=data, partial=True)
                
                if serializer.is_valid():
                    product: Product = product_service.update_existing_product(product_id, serializer.validated_data)
                    response_serializer = ProductSerializer(product)
                    return JsonResponse(response_serializer.data, status=200)
                
                return JsonResponse(serializer.errors, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)
            except ValueError as e:
                return handle_value_error(e)

        elif request.method == "DELETE":
            try:
                product_service.delete_product_record(product_id)
                return JsonResponse({"message": "Product deleted successfully."}, status=204)
            except ValueError as e:
                return handle_value_error(e)
            
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
        
    @csrf_exempt
    def bulk_upload_view(self, request: HttpRequest) -> JsonResponse:
        if request.method != 'POST':
            return JsonResponse({"error": "Method not allowed"}, status=405)

        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file uploaded. Please upload a CSV file with the key 'file'."}, status=400)

        csv_file = request.FILES['file']
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({"error": "File is not a CSV"}, status=400)

        try:
            df: pd.DataFrame = pd.read_csv(csv_file)
            df = df.where(pd.notnull(df), None)
            product_list: List[Dict[str, Any]] = df.to_dict('records')
            
            results: Dict[str, Any] = {
                "success_count": 0,
                "errors": []
            }
            
            for row_index, row_data in enumerate(product_list):
                serializer = ProductSerializer(data=row_data)
                
                if serializer.is_valid():
                    try:
                        product_service.create_new_product(serializer.validated_data)
                        results["success_count"] += 1
                    except ValueError as e:
                        error_msg: str = str(e.args[0]) if e.args else "Service error"
                        results["errors"].append({
                            "row": row_index + 1,
                            "data": row_data,
                            "error": error_msg
                        })
                else:
                    results["errors"].append({
                        "row": row_index + 1,
                        "data": row_data,
                        "error": serializer.errors
                    })
                    
            return JsonResponse(results, status=200)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred during pandas processing: {str(e)}"}, status=500)


class ProductCategoryView:
    
    @csrf_exempt
    def category_collection_view(self, request: HttpRequest) -> JsonResponse:
        if request.method == 'GET':
            categories: ProductCategoryQuerySet = category_service.get_all_categories()
            serializer = ProductCategorySerializer(categories, many=True)
            return JsonResponse(serializer.data, safe=False, status=200)

        elif request.method == 'POST':
            try:
                data: Dict[str, Any] = json.loads(request.body)
                serializer: ProductCategorySerializer = ProductCategorySerializer(data=data)
                
                if serializer.is_valid():
                    product_category: ProductCategory = category_service.create_new_category(serializer.validated_data)
                    return JsonResponse({"title": product_category.title}, status=201)
                
                return JsonResponse(serializer.errors, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)
            except ValueError as e:
                return handle_value_error(e)

        return JsonResponse({"error": "Method not allowed"}, status=405)

    @csrf_exempt
    def category_detail_view(self, request: HttpRequest, title: str) -> JsonResponse:
        if request.method == 'GET':
            try:
                products: Optional[ProductQuerySet] = product_service.get_products_by_category(title)
                serializer = ProductSerializer(products, many=True)
                return JsonResponse(serializer.data, safe=False, status=200)
            except ValueError as e:
                return handle_value_error(e)

        elif request.method == 'PATCH':
            try:
                data: Dict[str, Any] = json.loads(request.body)
                serializer: ProductCategorySerializer = ProductCategorySerializer(data=data, partial=True)
                
                if serializer.is_valid():
                    category: ProductCategory = category_service.update_existing_category(title, serializer.validated_data)
                    response_serializer = ProductCategorySerializer(category)
                    return JsonResponse(response_serializer.data, status=200)
                
                return JsonResponse(serializer.errors, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)
            except ValueError as e:
                return handle_value_error(e)

        elif request.method == 'DELETE':
            try:
                category_service.delete_category_record(title)
                return JsonResponse({"message": "Category deleted successfully."}, status=204)
            except ValueError as e:
                return handle_value_error(e)

        return JsonResponse({"error": "Method not allowed"}, status=405)