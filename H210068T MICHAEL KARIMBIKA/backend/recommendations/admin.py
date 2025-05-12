from django.contrib import admin
from .models import UserProductInteraction, ProductSimilarity, UserProductRecommendation

@admin.register(UserProductInteraction)
class UserProductInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'interaction_type', 'value', 'created_at')
    list_filter = ('interaction_type',)
    search_fields = ('user__username', 'product__name')

@admin.register(ProductSimilarity)
class ProductSimilarityAdmin(admin.ModelAdmin):
    list_display = ('product1', 'product2', 'similarity_score', 'updated_at')
    search_fields = ('product1__name', 'product2__name')

@admin.register(UserProductRecommendation)
class UserProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'score', 'created_at')
    search_fields = ('user__username', 'product__name')

