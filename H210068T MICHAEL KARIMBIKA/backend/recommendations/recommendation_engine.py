import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model
from products.models import Product, Review
from orders.models import OrderItem
from .models import UserProductInteraction, ProductSimilarity, UserProductRecommendation
from .ml_models import train_recommendation_models, get_recommendations_for_user, get_similar_products
import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()


class RecommendationEngine:
    """
    Recommendation engine using collaborative filtering with seasonal and location awareness
    """
    
    @staticmethod
    def update_user_product_interactions():
        """
        Update user-product interactions based on views, cart additions, purchases, and reviews
        """
        # Clear existing interactions
        UserProductInteraction.objects.all().delete()
        
        # Add interactions from reviews
        reviews = Review.objects.all()
        for review in reviews:
            UserProductInteraction.objects.create(
                user=review.user,
                product=review.product,
                interaction_type='review',
                value=review.rating
            )
        
        # Add interactions from purchases
        order_items = OrderItem.objects.all()
        for item in order_items:
            UserProductInteraction.objects.create(
                user=item.order.user,
                product=item.product,
                interaction_type='purchase',
                value=item.quantity
            )
        
        # Note: In a real application, you would also track views and cart additions
        
        logger.info(f"Updated user-product interactions: {UserProductInteraction.objects.count()} interactions")
    
    @staticmethod
    def calculate_product_similarities():
        """
        Calculate product similarities based on user interactions
        """
        # Train recommendation models
        success = train_recommendation_models()
        
        if not success:
            logger.error("Failed to train recommendation models, falling back to simple similarity calculation")
            
            # Get all interactions
            interactions = UserProductInteraction.objects.all()
            
            if not interactions:
                logger.warning("No interactions found, skipping similarity calculation")
                return
            
            # Convert to DataFrame
            interaction_data = []
            for interaction in interactions:
                interaction_data.append({
                    'user_id': interaction.user.id,
                    'product_id': interaction.product.id,
                    'interaction_type': interaction.interaction_type,
                    'value': interaction.value
                })
            
            if not interaction_data:
                logger.warning("No interaction data found, skipping similarity calculation")
                return
            
            df = pd.DataFrame(interaction_data)
            
            # Create user-item matrix
            # Weight interactions: reviews (5x), purchases (3x), cart additions (2x), views (1x)
            df['weighted_value'] = df.apply(
                lambda row: row['value'] * (
                    5 if row['interaction_type'] == 'review' else
                    3 if row['interaction_type'] == 'purchase' else
                    2 if row['interaction_type'] == 'cart' else 1
                ), axis=1
            )
            
            # Aggregate by user and product
            user_item_df = df.groupby(['user_id', 'product_id'])['weighted_value'].sum().unstack().fillna(0)
            
            # Calculate item-item similarity matrix
            item_similarity = cosine_similarity(user_item_df.T)
            
            # Convert to DataFrame with product IDs
            item_similarity_df = pd.DataFrame(
                item_similarity,
                index=user_item_df.columns,
                columns=user_item_df.columns
            )
            
            # Clear existing similarities
            ProductSimilarity.objects.all().delete()
            
            # Save similarities to database
            products = Product.objects.all()
            product_ids = [p.id for p in products]
            
            for i, product1_id in enumerate(item_similarity_df.index):
                if product1_id not in product_ids:
                    continue
                    
                for product2_id in item_similarity_df.columns[i+1:]:
                    if product2_id not in product_ids:
                        continue
                        
                    similarity = item_similarity_df.loc[product1_id, product2_id]
                    
                    # Skip if similarity is too low
                    if similarity < 0.1:
                        continue
                    
                    # Get product objects
                    product1 = Product.objects.get(id=product1_id)
                    product2 = Product.objects.get(id=product2_id)
                    
                    # Save similarity
                    ProductSimilarity.objects.create(
                        product1=product1,
                        product2=product2,
                        similarity_score=similarity
                    )
                    
                    # Save reverse similarity
                    ProductSimilarity.objects.create(
                        product1=product2,
                        product2=product1,
                        similarity_score=similarity
                    )
            
            logger.info(f"Calculated product similarities: {ProductSimilarity.objects.count()} similarity pairs")
    
    @staticmethod
    def generate_recommendations_for_user(user):
        """
        Generate product recommendations for a user based on collaborative filtering,
        seasonal relevance, and location
        """
        # Clear existing recommendations for this user
        UserProductRecommendation.objects.filter(user=user).delete()
        
        # Use ML model to generate recommendations
        recommended_products = get_recommendations_for_user(user.id)
        
        if not recommended_products:
            logger.warning(f"No recommendations generated for user {user.id}, falling back to simple method")
            
            # Get products the user has interacted with
            interacted_products = UserProductInteraction.objects.filter(user=user).values_list('product_id', flat=True)
            
            # Get all products
            all_products = Product.objects.all()
            
            # Get current month and user's location for seasonal and location filtering
            current_month = datetime.datetime.now().month
            user_country = user.country if hasattr(user, 'country') else None
            user_region = user.state if hasattr(user, 'state') else None
            
            # Determine user's hemisphere based on country
            northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
            southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
            
            if user_country in northern_countries:
                hemisphere = 'N'
            elif user_country in southern_countries:
                hemisphere = 'S'
            else:
                hemisphere = 'N'  # Default to Northern hemisphere
            
            # Products the user hasn't interacted with
            new_products = all_products.exclude(id__in=interacted_products)
            
            # Filter by location if user has location data
            if user_country:
                new_products = new_products.filter(
                    Q(is_location_specific=False) | 
                    Q(available_countries__icontains=user_country)
                )
                
                if user_region:
                    new_products = new_products.filter(
                        Q(is_location_specific=False) | 
                        Q(available_regions__icontains=user_region)
                    )
            
            # If user has no interactions, recommend popular products that are in season and location-relevant
            if not interacted_products:
                popular_products = new_products.annotate(
                    review_count=Count('reviews'),
                    avg_rating=Avg('reviews__rating')
                ).filter(review_count__gt=0).order_by('-avg_rating', '-review_count')[:20]
                
                # Filter for seasonal relevance
                in_season_products = []
                for product in popular_products:
                    if product.is_in_season(current_month, hemisphere):
                        in_season_products.append(product)
                
                # Create recommendations with seasonal boost
                for i, product in enumerate(in_season_products[:20]):
                    # Base score decreases with position
                    base_score = 1.0 - (i * 0.05)
                    
                    # Seasonal boost: products in season get a 20% boost
                    seasonal_boost = 0.2 if product.is_in_season(current_month, hemisphere) else 0
                    
                    # Location boost: products specific to user's location get a 15% boost
                    location_boost = 0
                    if product.is_location_specific and user_country:
                        if user_country in (product.available_countries or ''):
                            location_boost += 0.1
                        if user_region and user_region in (product.available_regions or ''):
                            location_boost += 0.05
                    
                    # Final score
                    final_score = base_score + seasonal_boost + location_boost
                    
                    UserProductRecommendation.objects.create(
                        user=user,
                        product=product,
                        score=final_score
                    )
                
                return
            
            # Calculate recommendation scores based on similar products
            recommendations = {}
            
            for product_id in interacted_products:
                # Get user's interaction value for this product
                interactions = UserProductInteraction.objects.filter(user=user, product_id=product_id)
                interaction_value = sum(
                    i.value * (
                        5 if i.interaction_type == 'review' else
                        3 if i.interaction_type == 'purchase' else
                        2 if i.interaction_type == 'cart' else 1
                    ) for i in interactions
                )
                
                # Get similar products
                similarities = ProductSimilarity.objects.filter(product1_id=product_id)
                
                for similarity in similarities:
                    similar_product = similarity.product2
                    
                    # Skip if user has already interacted with this product
                    if similar_product.id in interacted_products:
                        continue
                    
                    # Skip if product is not available in user's location
                    if user_country and similar_product.is_location_specific:
                        if user_country not in (similar_product.available_countries or ''):
                            continue
                        if user_region and user_region not in (similar_product.available_regions or ''):
                            continue
                    
                    # Calculate base recommendation score
                    base_score = similarity.similarity_score * interaction_value
                    
                    # Apply seasonal boost
                    seasonal_boost = 0.2 if similar_product.is_in_season(current_month, hemisphere) else 0
                    
                    # Final score
                    final_score = base_score * (1 + seasonal_boost)
                    
                    # Add to recommendations
                    if similar_product.id in recommendations:
                        recommendations[similar_product.id] += final_score
                    else:
                        recommendations[similar_product.id] = final_score
            
            # Normalize scores
            if recommendations:
                max_score = max(recommendations.values())
                for product_id in recommendations:
                    recommendations[product_id] /= max_score
            
            # Save recommendations
            for product_id, score in sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:20]:
                product = Product.objects.get(id=product_id)
                UserProductRecommendation.objects.create(
                    user=user,
                    product=product,
                    score=score
                )
            
            # If not enough recommendations, add popular products that are in season and location-relevant
            recommendation_count = UserProductRecommendation.objects.filter(user=user).count()
            if recommendation_count < 10:
                popular_products = new_products.annotate(
                    review_count=Count('reviews'),
                    avg_rating=Avg('reviews__rating')
                ).filter(
                    review_count__gt=0
                ).exclude(
                    id__in=list(recommendations.keys()) + list(interacted_products)
                ).order_by('-avg_rating', '-review_count')[:20-recommendation_count]
                
                # Filter for seasonal and location relevance
                relevant_products = []
                for product in popular_products:
                    if product.is_in_season(current_month, hemisphere):
                        relevant_products.append(product)
                
                for i, product in enumerate(relevant_products):
                    # Lower scores than collaborative recommendations
                    base_score = 0.5 - (i * 0.02)
                    
                    # Seasonal boost
                    seasonal_boost = 0.1 if product.is_in_season(current_month, hemisphere) else 0
                    
                    # Final score
                    final_score = base_score + seasonal_boost
                    
                    UserProductRecommendation.objects.create(
                        user=user,
                        product=product,
                        score=final_score
                    )
        else:
            # Save recommendations from ML model
            for i, product in enumerate(recommended_products):
                # Score decreases with position
                score = 1.0 - (i * 0.05)
                
                UserProductRecommendation.objects.create(
                    user=user,
                    product=product,
                    score=score
                )
        
        logger.info(f"Generated recommendations for user {user.id}: {UserProductRecommendation.objects.filter(user=user).count()} recommendations")
    
    @staticmethod
    def get_similar_products(product, limit=4, user=None):
        """
        Get similar products for a given product, with optional user context for
        seasonal and location relevance
        """
        # Use ML model to get similar products
        similar_products = get_similar_products(product.id, limit=limit)
        
        if not similar_products:
            logger.warning(f"No similar products found for product {product.id} using ML model, falling back to simple method")
            
            similar_products = ProductSimilarity.objects.filter(
                product1=product
            ).order_by('-similarity_score').values_list('product2', flat=True)
            
            products = Product.objects.filter(id__in=similar_products)
            
            # Apply seasonal and location filtering if user is provided
            if user:
                # Get current month and user's location
                current_month = datetime.datetime.now().month
                user_country = user.country if hasattr(user, 'country') else None
                user_region = user.state if hasattr(user, 'state') else None
                
                # Determine user's hemisphere
                northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
                southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
                
                if user_country in northern_countries:
                    hemisphere = 'N'
                elif user_country in southern_countries:
                    hemisphere = 'S'
                else:
                    hemisphere = 'N'  # Default to Northern hemisphere
                
                # Filter by season and location
                filtered_products = []
                for p in products:
                    # Check seasonal relevance
                    if p.is_seasonal and not p.is_in_season(current_month, hemisphere):
                        continue
                    
                    # Check location relevance
                    if p.is_location_specific and user_country:
                        if user_country not in (p.available_countries or ''):
                            continue
                        if user_region and user_region not in (p.available_regions or ''):
                            continue
                    
                    filtered_products.append(p.id)
                
                products = Product.objects.filter(id__in=filtered_products)
            
            return products[:limit]
        
        return similar_products
    
    @staticmethod
    def get_recommendations_for_user(user, limit=8):
        """
        Get recommended products for a user
        """
        recommendations = UserProductRecommendation.objects.filter(
            user=user
        ).order_by('-score').values_list('product', flat=True)[:limit]
        
        return Product.objects.filter(id__in=recommendations)
    
    @staticmethod
    def get_seasonal_recommendations(user=None, limit=8):
        """
        Get products that are in season for the current month and user's hemisphere
        """
        current_month = datetime.datetime.now().month
        
        # Determine hemisphere based on user's country or default to Northern
        hemisphere = 'N'
        if user and hasattr(user, 'country') and user.country:
            northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
            southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
            
            if user.country in northern_countries:
                hemisphere = 'N'
            elif user.country in southern_countries:
                hemisphere = 'S'
        
        # Get all products with seasonal tags
        seasonal_products = Product.objects.filter(seasons__isnull=False).distinct()
        
        # Filter products that are in season
        in_season_products = []
        for product in seasonal_products:
            if product.is_in_season(current_month, hemisphere):
                in_season_products.append(product.id)
        
        seasonal_products = Product.objects.filter(id__in=in_season_products)
        
        # Apply location filtering if user is provided
        if user and hasattr(user, 'country') and user.country:
            seasonal_products = seasonal_products.filter(
                Q(is_location_specific=False) | 
                Q(available_countries__icontains=user.country)
            )
            
            if hasattr(user, 'state') and user.state:
                seasonal_products = seasonal_products.filter(
                    Q(is_location_specific=False) | 
                    Q(available_regions__icontains=user.state)
                )
        
        # Order by rating and return limited number
        return seasonal_products.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating', '-featured')[:limit]

