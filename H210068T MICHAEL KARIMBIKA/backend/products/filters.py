import django_filters
from django.db.models import Q
from .models import Product
import datetime

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    category = django_filters.CharFilter(field_name="category__slug")
    min_rating = django_filters.NumberFilter(method='filter_by_rating')
    in_season = django_filters.BooleanFilter(method='filter_by_season')
    country = django_filters.CharFilter(method='filter_by_country')
    region = django_filters.CharFilter(method='filter_by_region')
    
    class Meta:
        model = Product
        fields = ['category', 'featured', 'min_price', 'max_price', 'min_rating', 'in_season', 'country', 'region']
    
    def filter_by_rating(self, queryset, name, value):
        # Filter products with average rating >= value
        products = []
        for product in queryset:
            if product.average_rating >= value:
                products.append(product.id)
        return queryset.filter(id__in=products)
    
    def filter_by_season(self, queryset, name, value):
        if not value:  # If not filtering by season, return all products
            return queryset
        
        # Get current month and hemisphere
        current_month = datetime.datetime.now().month
        hemisphere = self.request.GET.get('hemisphere', 'N')  # Default to Northern hemisphere
        
        # Filter products that are in season
        in_season_products = []
        for product in queryset:
            if product.is_in_season(current_month, hemisphere):
                in_season_products.append(product.id)
        
        return queryset.filter(id__in=in_season_products)
    
    def filter_by_country(self, queryset, name, value):
        if not value:
            return queryset
        
        # Filter products available in the specified country
        return queryset.filter(
            Q(is_location_specific=False) | 
            Q(available_countries__icontains=value)
        )
    
    def filter_by_region(self, queryset, name, value):
        if not value:
            return queryset
        
        # Filter products available in the specified region
        return queryset.filter(
            Q(is_location_specific=False) | 
            Q(available_regions__icontains=value)
        )

