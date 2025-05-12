from django.db import models
from django.conf import settings
from products.models import Product

class UserProductInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_interactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    value = models.FloatField(default=1.0)  # Strength of interaction (e.g., rating value)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product', 'interaction_type')
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.product.name}"

class ProductSimilarity(models.Model):
    product1 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_as_first')
    product2 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_as_second')
    similarity_score = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product1', 'product2')
    
    def __str__(self):
        return f"Similarity between {self.product1.name} and {self.product2.name}: {self.similarity_score}"

class UserProductRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_recommendations')
    score = models.FloatField()  # Recommendation score
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-score']
    
    def __str__(self):
        return f"Recommendation of {self.product.name} for {self.user.username}: {self.score}"

