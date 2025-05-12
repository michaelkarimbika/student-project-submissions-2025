from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Category, Product, Review, HelpfulReview, Season
from .serializers import CategorySerializer, ProductSerializer, ProductDetailSerializer, ReviewSerializer, SeasonSerializer
from .filters import ProductFilter
import datetime

class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [permissions.AllowAny]

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'rating']
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get user country from query params
        user_country = self.request.query_params.get('user_country')
        
        # If user country is provided, prioritize products from that country
        if user_country:
            # Use Case/When to add a priority field for ordering
            # Products from user's country get priority 1, others get priority 2
            queryset = queryset.annotate(
                country_priority=Case(
                    # Check if the product's available_countries contains the user's country
                    When(available_countries__icontains=user_country, then=Value(1)),
                    # All other products get lower priority
                    default=Value(2),
                    output_field=IntegerField()
                )
            ).order_by('country_priority', *queryset.query.order_by or ['-created_at'])
            
            # Log for debugging
            print(f"Prioritizing products for country: {user_country}")
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        
        # Add current month and hemisphere to context for seasonal filtering
        context['current_month'] = datetime.datetime.now().month
        
        # Get hemisphere from query params or user location
        hemisphere = self.request.query_params.get('hemisphere')
        if not hemisphere and self.request.user.is_authenticated:
            # Determine hemisphere based on user's country
            # This is a simplified approach - in a real app, you'd use a more comprehensive mapping
            northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
            southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
            
            user_country = self.request.user.country
            if user_country in northern_countries:
                hemisphere = 'N'
            elif user_country in southern_countries:
                hemisphere = 'S'
            else:
                hemisphere = 'N'  # Default to Northern hemisphere
        else:
            hemisphere = hemisphere or 'N'  # Default to Northern hemisphere
        
        context['hemisphere'] = hemisphere
        return context
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = self.get_queryset().filter(featured=True)
        
        # Apply location filtering if user is authenticated
        if request.user.is_authenticated and request.user.country:
            featured_products = featured_products.filter(
                Q(is_location_specific=False) | 
                Q(available_countries__icontains=request.user.country)
            )
        
        # Apply seasonal filtering
        current_month = datetime.datetime.now().month
        hemisphere = request.query_params.get('hemisphere', 'N')
        
        # Get products that are in season
        in_season_products = []
        for product in featured_products:
            if product.is_in_season(current_month, hemisphere):
                in_season_products.append(product.id)
        
        featured_products = featured_products.filter(id__in=in_season_products)
        
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seasonal(self, request):
        """Get products that are in season for the current month and user's hemisphere"""
        current_month = datetime.datetime.now().month
        
        # Get hemisphere from query params or user location
        hemisphere = request.query_params.get('hemisphere')
        if not hemisphere and request.user.is_authenticated:
            # Determine hemisphere based on user's country
            northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
            southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
            
            user_country = request.user.country
            if user_country in northern_countries:
                hemisphere = 'N'
            elif user_country in southern_countries:
                hemisphere = 'S'
            else:
                hemisphere = 'N'  # Default to Northern hemisphere
        else:
            hemisphere = hemisphere or 'N'  # Default to Northern hemisphere
        
        # Get all products with seasonal tags
        seasonal_products = self.get_queryset().filter(seasons__isnull=False).distinct()
        
        # Filter products that are in season
        in_season_products = []
        for product in seasonal_products:
            if product.is_in_season(current_month, hemisphere):
                in_season_products.append(product.id)
        
        seasonal_products = Product.objects.filter(id__in=in_season_products)
        
        # Apply location filtering if user is authenticated
        if request.user.is_authenticated and request.user.country:
            seasonal_products = seasonal_products.filter(
                Q(is_location_specific=False) | 
                Q(available_countries__icontains=request.user.country)
            )
        
        serializer = self.get_serializer(seasonal_products, many=True)
        return Response(serializer.data)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Review.objects.all()
        
        # Filter by product if product_id is provided
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        return queryset
    
    def perform_create(self, serializer):
        # Set the user to the current authenticated user
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        review = self.get_object()
        user = request.user
        
        # Check if user already marked this review as helpful
        helpful_mark, created = HelpfulReview.objects.get_or_create(review=review, user=user)
        
        if created:
            # Increment helpful count
            review.helpful_count += 1
            review.save()
            return Response({'status': 'review marked as helpful'})
        else:
            # User already marked this review as helpful
            return Response({'status': 'already marked as helpful'}, status=status.HTTP_400_BAD_REQUEST)
