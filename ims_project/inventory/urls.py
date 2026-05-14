from django.urls import path
from .views import ProductView, ProductCategoryView, ScenarioSimulationView, AskExpertView

product_views = ProductView()
category_views = ProductCategoryView()
scenario_views = ScenarioSimulationView()
expert_views = AskExpertView()


urlpatterns = [
    path('products/', product_views.product_collection_view, name='product_collection'),

    path('products/<str:product_id>/', product_views.product_detail_view, name='product_detail'),

    path('categories/', category_views.category_collection_view, name='category_collection'),

    path('categories/<str:title>/', category_views.category_detail_view, name='category_detail'),

    path('scenarios/', scenario_views.generate_scenario_view, name = "scenario_collection"),

    path('products/<str:product_id>/similar/', product_views.similar_products_view, name = "similar_products"),

    path('api/chat/', expert_views.chat_view, name='ask-expert-chat')

]