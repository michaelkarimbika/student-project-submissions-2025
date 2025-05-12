from django.urls import path
from .views import similar_products, recommended_products, featured_products, seasonal_products, model_info, train_models

urlpatterns = [
    path('similar-products/<int:product_id>/', similar_products, name='similar-products'),
    path('recommended-products/', recommended_products, name='recommended-products'),
    path('featured-products/', featured_products, name='featured-products'),
    path('seasonal-products/', seasonal_products, name='seasonal-products'),
    path('recommendation-models/info/', model_info, name='model-info'),
    path('recommendation-models/train/', train_models, name='train-models'),
]

