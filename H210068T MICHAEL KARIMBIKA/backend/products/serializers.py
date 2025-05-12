from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, HelpfulReview, Season

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ('id', 'name', 'start_month', 'end_month', 'hemisphere')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'parent')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary')

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    date_posted = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ('id', 'product', 'user', 'user_name', 'user_avatar', 'rating', 'comment', 'created_at', 'updated_at', 'helpful_count', 'date_posted')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'helpful_count', 'user_name', 'user_avatar', 'date_posted')
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_user_avatar(self, obj):
        if obj.user.profile_image:
            return obj.user.profile_image.url
        return None
    
    def get_date_posted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    seasons = SeasonSerializer(many=True, read_only=True)
    is_in_season = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'discount_price', 'category', 'category_name', 
                  'stock', 'featured', 'created_at', 'updated_at', 'images', 'primary_image', 'rating', 
                  'review_count', 'seasons', 'is_in_season', 'is_location_specific', 'available_countries', 
                  'available_regions')
        read_only_fields = ('id', 'created_at', 'updated_at', 'rating', 'review_count', 'is_in_season')
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        # Return first image if no primary image
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return None
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_rating(self, obj):
        return obj.average_rating
    
    def get_review_count(self, obj):
        return obj.review_count
    
    def get_is_in_season(self, obj):
        # Get current month from request context if available
        request = self.context.get('request')
        if request and hasattr(request, 'current_month') and hasattr(request, 'hemisphere'):
            return obj.is_in_season(request.current_month, request.hemisphere)
        
        # Default to current month and Northern hemisphere
        import datetime
        current_month = datetime.datetime.now().month
        return obj.is_in_season(current_month)

class ProductDetailSerializer(ProductSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('reviews',)

