from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from products.models import Product
from products.serializers import ProductSerializer
from .recommendation_engine import RecommendationEngine
from .ml_models import get_recommendations_for_user, get_similar_products
import datetime

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def similar_products(request, product_id):
    """
    Get similar products for a given product
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Pass user context if authenticated for better recommendations
    user = request.user if request.user.is_authenticated else None
    similar_products = RecommendationEngine.get_similar_products(product, user=user)
    
    serializer = ProductSerializer(similar_products, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recommended_products(request):
    """
    Get recommended products for the authenticated user
    """
    user = request.user
    
    # Generate recommendations if none exist
    if not hasattr(user, 'product_recommendations') or user.product_recommendations.count() == 0:
        RecommendationEngine.generate_recommendations_for_user(user)
    
    # Get recommendations
    recommended_products = RecommendationEngine.get_recommendations_for_user(user)
    serializer = ProductSerializer(recommended_products, many=True, context={'request': request})
    
    # Add match score to each product
    for i, product in enumerate(serializer.data):
        recommendation = user.product_recommendations.filter(product_id=product['id']).first()
        if recommendation:
            product['matchScore'] = int(recommendation.score * 100)
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_products(request):
    """
    Get featured products with seasonal and location relevance
    """
    featured_products = Product.objects.filter(featured=True)
    
    # Apply location filtering if user is authenticated
    if request.user.is_authenticated and hasattr(request.user, 'country') and request.user.country:
        featured_products = featured_products.filter(
            Q(is_location_specific=False) | 
            Q(available_countries__icontains=request.user.country)
        )
    
    # Get current month and hemisphere for seasonal filtering
    current_month = datetime.datetime.now().month
    
    # Determine hemisphere based on user's country or query param
    hemisphere = request.query_params.get('hemisphere')
    if not hemisphere and request.user.is_authenticated and hasattr(request.user, 'country') and request.user.country:
        northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
        southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA','ZW']
        
        if request.user.country in northern_countries:
            hemisphere = 'N'
        elif request.user.country in southern_countries:
            hemisphere = 'S'
        else:
            hemisphere = 'N'  # Default to Northern hemisphere
    else:
        hemisphere = hemisphere or 'N'  # Default to Northern hemisphere
    
    # Prioritize products that are in season
    in_season_products = []
    out_of_season_products = []
    
    for product in featured_products:
        if product.is_seasonal:
            if product.is_in_season(current_month, hemisphere):
                in_season_products.append(product.id)
            else:
                out_of_season_products.append(product.id)
        else:
            # Non-seasonal products are always considered in season
            in_season_products.append(product.id)
    
    # Combine in-season and out-of-season products, prioritizing in-season
    product_ids = in_season_products + out_of_season_products
    
    # Use Case() to preserve the order
    from django.db.models import Case, When
    preserved_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(product_ids)])
    
    featured_products = Product.objects.filter(id__in=product_ids).order_by(preserved_order)[:8]
    
    serializer = ProductSerializer(featured_products, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def seasonal_products(request):
    """
    Get products that are in season for the current month and user's hemisphere
    """
    user = request.user if request.user.is_authenticated else None
    seasonal_products = RecommendationEngine.get_seasonal_recommendations(user=user)
    
    serializer = ProductSerializer(seasonal_products, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def model_info(request):
    """
    Get information about the recommendation models
    """
    import os
    from django.conf import settings
    
    MODELS_DIR = os.path.join(settings.BASE_DIR, 'models')
    
    # Check if models exist
    cf_model_path = os.path.join(MODELS_DIR, 'collaborative_model.joblib')
    cb_model_path = os.path.join(MODELS_DIR, 'content_model.joblib')
    hybrid_params_path = os.path.join(MODELS_DIR, 'hybrid_params.joblib')
    
    cf_model_exists = os.path.exists(cf_model_path)
    cb_model_exists = os.path.exists(cb_model_path)
    hybrid_params_exist = os.path.exists(hybrid_params_path)
    
    # Get model file sizes and modification times
    model_info = {}
    
    if cf_model_exists:
        cf_size = os.path.getsize(cf_model_path) / (1024 * 1024)  # Size in MB
        cf_modified = datetime.datetime.fromtimestamp(os.path.getmtime(cf_model_path))
        model_info['collaborative_model'] = {
            'exists': True,
            'size_mb': round(cf_size, 2),
            'last_modified': cf_modified.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        model_info['collaborative_model'] = {'exists': False}
    
    if cb_model_exists:
        cb_size = os.path.getsize(cb_model_path) / (1024 * 1024)  # Size in MB
        cb_modified = datetime.datetime.fromtimestamp(os.path.getmtime(cb_model_path))
        model_info['content_model'] = {
            'exists': True,
            'size_mb': round(cb_size, 2),
            'last_modified': cb_modified.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        model_info['content_model'] = {'exists': False}
    
    if hybrid_params_exist:
        hybrid_size = os.path.getsize(hybrid_params_path) / 1024  # Size in KB
        hybrid_modified = datetime.datetime.fromtimestamp(os.path.getmtime(hybrid_params_path))
        model_info['hybrid_params'] = {
            'exists': True,
            'size_kb': round(hybrid_size, 2),
            'last_modified': hybrid_modified.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        model_info['hybrid_params'] = {'exists': False}
    
    # Get database stats
    model_info['database_stats'] = {
        'products': Product.objects.count(),
        'interactions': UserProductInteraction.objects.count(),
        'similarities': ProductSimilarity.objects.count(),
        'recommendations': UserProductRecommendation.objects.count()
    }
    
    return Response(model_info)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def train_models(request):
    """
    Trigger training of recommendation models (admin only)
    """
    from .ml_models import train_recommendation_models
    
    success = train_recommendation_models()
    
    if success:
        return Response({'status': 'success', 'message': 'Models trained successfully'})
    else:
        return Response({'status': 'error', 'message': 'Failed to train models'}, status=500)

