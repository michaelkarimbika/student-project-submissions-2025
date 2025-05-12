from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.conf import settings

class Season(models.Model):
    """Model for seasons to tag products with seasonal relevance"""
    HEMISPHERE_CHOICES = (
        ('N', 'Northern'),
        ('S', 'Southern'),
        ('B', 'Both'),
    )
    
    name = models.CharField(max_length=50)
    start_month = models.PositiveSmallIntegerField()
    end_month = models.PositiveSmallIntegerField()
    hemisphere = models.CharField(max_length=1, choices=HEMISPHERE_CHOICES, default='B')
    
    def __str__(self):
        if self.hemisphere == 'B':
            return self.name
        hemisphere_name = 'Northern' if self.hemisphere == 'N' else 'Southern'
        return f"{self.name} ({hemisphere_name} Hemisphere)"

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='children')
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Seasonal relevance
    seasons = models.ManyToManyField(Season, blank=True, related_name='products')
    
    # Location relevance
    is_location_specific = models.BooleanField(default=False)
    available_countries = models.CharField(max_length=255, blank=True, null=True, 
                                          help_text="Comma-separated list of country codes")
    available_regions = models.CharField(max_length=255, blank=True, null=True,
                                        help_text="Comma-separated list of regions/states")
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    @property
    def review_count(self):
        return self.reviews.count()
    
    @property
    def is_seasonal(self):
        return self.seasons.exists()
    
    def is_in_season(self, month, hemisphere='N'):
        """Check if product is in season for the given month and hemisphere"""
        if not self.is_seasonal:
            return True  # Non-seasonal products are always in season
        
        for season in self.seasons.all():
            if season.hemisphere in [hemisphere, 'B']:
                # Handle seasons that span across year end
                if season.start_month > season.end_month:
                    if month >= season.start_month or month <= season.end_month:
                        return True
                else:
                    if season.start_month <= month <= season.end_month:
                        return True
        return False
    
    def is_available_in_location(self, country=None, region=None):
        """Check if product is available in the given location"""
        if not self.is_location_specific:
            return True  # Non-location-specific products are available everywhere
        
        if country and self.available_countries:
            available_countries = [c.strip() for c in self.available_countries.split(',')]
            if country not in available_countries:
                return False
        
        if region and self.available_regions:
            available_regions = [r.strip() for r in self.available_regions.split(',')]
            if region not in available_regions:
                return False
        
        return True

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # If this image is set as primary, unset primary for other images
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    helpful_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('product', 'user')
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class HelpfulReview(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_marks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
    
    def __str__(self):
        return f"{self.user.username} marked review {self.review.id} as helpful"

