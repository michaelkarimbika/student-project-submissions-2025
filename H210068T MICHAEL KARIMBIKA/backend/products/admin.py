from django.contrib import admin
from .models import Category, Product, ProductImage, Review, HelpfulReview, Season

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_month', 'end_month', 'hemisphere')
    list_filter = ('hemisphere',)
    search_fields = ('name',)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at', 'updated_at', 'helpful_count')
    can_delete = False

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'stock', 'featured', 'average_rating', 'review_count', 'is_seasonal', 'is_location_specific')
    list_filter = ('category', 'featured', 'seasons', 'is_location_specific')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ReviewInline]
    filter_horizontal = ('seasons',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'price', 'discount_price', 'category', 'stock', 'featured')
        }),
        ('Seasonal Availability', {
            'fields': ('seasons',),
        }),
        ('Location Availability', {
            'fields': ('is_location_specific', 'available_countries', 'available_regions'),
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'helpful_count')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(HelpfulReview)

