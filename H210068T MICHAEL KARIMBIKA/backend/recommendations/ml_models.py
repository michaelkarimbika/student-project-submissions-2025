import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
import joblib
from datetime import datetime
import logging
from django.conf import settings
from django.db.models import Count, Avg, Q
from products.models import Product, Category, Review
from .models import UserProductInteraction, ProductSimilarity

# Set up logging
logger = logging.getLogger(__name__)

# Create models directory if it doesn't exist
MODELS_DIR = os.path.join(settings.BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

class CollaborativeFilteringModel:
    """
    Collaborative filtering model using matrix factorization (SVD)
    """
    def __init__(self, n_components=10):
        self.n_components = n_components
        self.model = TruncatedSVD(n_components=n_components, random_state=42)
        self.user_item_matrix = None
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_item_mapping = {}
    
    def fit(self, interactions_df):
        """
        Train the model on user-item interactions
        
        Args:
            interactions_df: DataFrame with columns 'user_id', 'product_id', 'value'
        """
        # Create user-item matrix
        self.user_item_matrix = interactions_df.pivot(
            index='user_id', 
            columns='product_id', 
            values='value'
        ).fillna(0)
        
        # Create mappings between original IDs and matrix indices
        self.user_mapping = {user_id: i for i, user_id in enumerate(self.user_item_matrix.index)}
        self.item_mapping = {item_id: i for i, item_id in enumerate(self.user_item_matrix.columns)}
        self.reverse_user_mapping = {i: user_id for user_id, i in self.user_mapping.items()}
        self.reverse_item_mapping = {i: item_id for item_id, i in self.item_mapping.items()}
        
        # Fit the model
        self.model.fit(self.user_item_matrix.values)
        
        # Calculate item-item similarity matrix
        self.item_features = self.model.components_.T
        self.item_similarity = cosine_similarity(self.item_features)
        
        return self
    
    def get_similar_items(self, item_id, n=10):
        """
        Get similar items for a given item
        
        Args:
            item_id: Product ID
            n: Number of similar items to return
            
        Returns:
            List of (item_id, similarity_score) tuples
        """
        if item_id not in self.item_mapping:
            return []
        
        item_idx = self.item_mapping[item_id]
        similar_indices = np.argsort(self.item_similarity[item_idx])[::-1][1:n+1]
        
        return [
            (self.reverse_item_mapping[idx], self.item_similarity[item_idx][idx]) 
            for idx in similar_indices
        ]
    
    def recommend_for_user(self, user_id, n=10, exclude_items=None):
        """
        Get recommendations for a user
        
        Args:
            user_id: User ID
            n: Number of recommendations to return
            exclude_items: List of item IDs to exclude
            
        Returns:
            List of (item_id, score) tuples
        """
        if exclude_items is None:
            exclude_items = []
        
        # If user is not in the training data, return empty list
        if user_id not in self.user_mapping:
            return []
        
        user_idx = self.user_mapping[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx].values.reshape(1, -1)
        
        # Project user vector into latent space and back
        user_preds = user_vector @ self.model.components_.T @ self.model.components_
        
        # Get indices of items to recommend (excluding already interacted items)
        user_interacted = set(self.user_item_matrix.columns[user_vector.flatten() > 0])
        exclude_set = set(exclude_items).union(user_interacted)
        
        # Get all items that are not excluded
        candidate_items = [
            item_id for item_id in self.user_item_matrix.columns 
            if item_id not in exclude_set
        ]
        
        # Get scores for candidate items
        candidate_indices = [self.item_mapping[item_id] for item_id in candidate_items]
        scores = user_preds.flatten()[candidate_indices]
        
        # Sort by score and return top n
        item_scores = list(zip(candidate_items, scores))
        item_scores.sort(key=lambda x: x[1], reverse=True)
        
        return item_scores[:n]
    
    def save(self, filename='collaborative_model.joblib'):
        """Save model to disk"""
        path = os.path.join(MODELS_DIR, filename)
        joblib.dump({
            'n_components': self.n_components,
            'model': self.model,
            'user_mapping': self.user_mapping,
            'item_mapping': self.item_mapping,
            'reverse_user_mapping': self.reverse_user_mapping,
            'reverse_item_mapping': self.reverse_item_mapping,
            'user_item_matrix': self.user_item_matrix,
        }, path)
        logger.info(f"Collaborative filtering model saved to {path}")
    
    @classmethod
    def load(cls, filename='collaborative_model.joblib'):
        """Load model from disk"""
        path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(path):
            logger.warning(f"Model file {path} not found")
            return None
        
        data = joblib.load(path)
        model = cls(n_components=data['n_components'])
        model.model = data['model']
        model.user_mapping = data['user_mapping']
        model.item_mapping = data['item_mapping']
        model.reverse_user_mapping = data['reverse_user_mapping']
        model.reverse_item_mapping = data['reverse_item_mapping']
        model.user_item_matrix = data['user_item_matrix']
        
        # Recalculate item features and similarity
        model.item_features = model.model.components_.T
        model.item_similarity = cosine_similarity(model.item_features)
        
        logger.info(f"Collaborative filtering model loaded from {path}")
        return model


class ContentBasedFilteringModel:
    """
    Content-based filtering model using TF-IDF and cosine similarity
    """
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english')),
            ('svd', TruncatedSVD(n_components=50, random_state=42)),
        ])
        self.product_features = None
        self.product_ids = None
        self.similarity_matrix = None
    
    def fit(self, products_df):
        """
        Train the model on product content
        
        Args:
            products_df: DataFrame with columns 'id', 'name', 'description', 'category'
        """
        # Combine text features
        products_df['content'] = (
            products_df['name'] + ' ' + 
            products_df['description'] + ' ' + 
            products_df['category']
        )
        
        # Fit the pipeline and transform the content
        self.product_features = self.pipeline.fit_transform(products_df['content'])
        self.product_ids = products_df['id'].values
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(self.product_features)
        
        return self
    
    def get_similar_items(self, item_id, n=10):
        """
        Get similar items for a given item based on content
        
        Args:
            item_id: Product ID
            n: Number of similar items to return
            
        Returns:
            List of (item_id, similarity_score) tuples
        """
        # Find index of the item
        try:
            item_idx = list(self.product_ids).index(item_id)
        except ValueError:
            return []
        
        # Get similarity scores
        similarity_scores = self.similarity_matrix[item_idx]
        
        # Get indices of top similar items (excluding the item itself)
        similar_indices = np.argsort(similarity_scores)[::-1][1:n+1]
        
        # Return item IDs and similarity scores
        return [
            (self.product_ids[idx], similarity_scores[idx]) 
            for idx in similar_indices
        ]
    
    def recommend_for_user_profile(self, user_profile, n=10, exclude_items=None):
        """
        Get recommendations based on user profile
        
        Args:
            user_profile: Dictionary with keys 'liked_categories', 'liked_products'
            n: Number of recommendations to return
            exclude_items: List of item IDs to exclude
            
        Returns:
            List of (item_id, score) tuples
        """
        if exclude_items is None:
            exclude_items = []
        
        # If no profile data, return empty list
        if not user_profile.get('liked_categories') and not user_profile.get('liked_products'):
            return []
        
        # Calculate average feature vector for liked products
        liked_product_indices = [
            list(self.product_ids).index(pid) 
            for pid in user_profile.get('liked_products', [])
            if pid in self.product_ids
        ]
        
        if liked_product_indices:
            user_vector = self.product_features[liked_product_indices].mean(axis=0)
        else:
            # If no liked products, use a zero vector
            user_vector = np.zeros((1, self.product_features.shape[1]))
        
        # Calculate similarity between user vector and all products
        similarity_scores = cosine_similarity(user_vector, self.product_features)[0]
        
        # Create list of (item_id, score) tuples
        item_scores = list(zip(self.product_ids, similarity_scores))
        
        # Filter out excluded items
        item_scores = [
            (item_id, score) for item_id, score in item_scores
            if item_id not in exclude_items
        ]
        
        # Sort by score and return top n
        item_scores.sort(key=lambda x: x[1], reverse=True)
        return item_scores[:n]
    
    def save(self, filename='content_model.joblib'):
        """Save model to disk"""
        path = os.path.join(MODELS_DIR, filename)
        joblib.dump({
            'pipeline': self.pipeline,
            'product_features': self.product_features,
            'product_ids': self.product_ids,
            'similarity_matrix': self.similarity_matrix,
        }, path)
        logger.info(f"Content-based filtering model saved to {path}")
    
    @classmethod
    def load(cls, filename='content_model.joblib'):
        """Load model from disk"""
        path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(path):
            logger.warning(f"Model file {path} not found")
            return None
        
        data = joblib.load(path)
        model = cls()
        model.pipeline = data['pipeline']
        model.product_features = data['product_features']
        model.product_ids = data['product_ids']
        model.similarity_matrix = data['similarity_matrix']
        
        logger.info(f"Content-based filtering model loaded from {path}")
        return model


class HybridRecommender:
    """
    Hybrid recommender that combines collaborative filtering and content-based filtering
    """
    def __init__(self, cf_weight=0.7, cb_weight=0.3):
        self.cf_model = None
        self.cb_model = None
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        self.seasonal_boost = 0.2
        self.location_boost = 0.1
    
    def fit(self, interactions_df, products_df):
        """
        Train both models
        
        Args:
            interactions_df: DataFrame for collaborative filtering
            products_df: DataFrame for content-based filtering
        """
        # Train collaborative filtering model
        self.cf_model = CollaborativeFilteringModel()
        self.cf_model.fit(interactions_df)
        
        # Train content-based filtering model
        self.cb_model = ContentBasedFilteringModel()
        self.cb_model.fit(products_df)
        
        return self
    
    def get_similar_items(self, item_id, n=10):
        """
        Get similar items using both models
        
        Args:
            item_id: Product ID
            n: Number of similar items to return
            
        Returns:
            List of (item_id, similarity_score) tuples
        """
        # Get recommendations from both models
        cf_recs = dict(self.cf_model.get_similar_items(item_id, n=n))
        cb_recs = dict(self.cb_model.get_similar_items(item_id, n=n))
        
        # Combine recommendations
        combined_recs = {}
        
        # Add collaborative filtering recommendations
        for item_id, score in cf_recs.items():
            combined_recs[item_id] = score * self.cf_weight
        
        # Add content-based recommendations
        for item_id, score in cb_recs.items():
            if item_id in combined_recs:
                combined_recs[item_id] += score * self.cb_weight
            else:
                combined_recs[item_id] = score * self.cb_weight
        
        # Sort by score and return top n
        sorted_recs = sorted(combined_recs.items(), key=lambda x: x[1], reverse=True)
        return sorted_recs[:n]
    
    def recommend_for_user(self, user_id, user_profile=None, n=10, exclude_items=None, 
                          current_month=None, hemisphere=None, user_location=None):
        """
        Get recommendations for a user using both models and considering seasonal and location factors
        
        Args:
            user_id: User ID
            user_profile: Dictionary with user profile for content-based filtering
            n: Number of recommendations to return
            exclude_items: List of item IDs to exclude
            current_month: Current month (1-12)
            hemisphere: User's hemisphere ('N' or 'S')
            user_location: Dictionary with 'country' and 'region' keys
            
        Returns:
            List of (item_id, score) tuples
        """
        if exclude_items is None:
            exclude_items = []
        if user_profile is None:
            user_profile = {}
        
        # Get recommendations from collaborative filtering
        cf_recs = dict(self.cf_model.recommend_for_user(user_id, n=n*2, exclude_items=exclude_items))
        
        # Get recommendations from content-based filtering
        cb_recs = dict(self.cb_model.recommend_for_user_profile(user_profile, n=n*2, exclude_items=exclude_items))
        
        # Combine recommendations
        combined_recs = {}
        
        # Add collaborative filtering recommendations
        for item_id, score in cf_recs.items():
            combined_recs[item_id] = score * self.cf_weight
        
        # Add content-based recommendations
        for item_id, score in cb_recs.items():
            if item_id in combined_recs:
                combined_recs[item_id] += score * self.cb_weight
            else:
                combined_recs[item_id] = score * self.cb_weight
        
        # Apply seasonal and location boosts if applicable
        if current_month and hemisphere:
            # Get products from database to check seasonal relevance
            product_ids = list(combined_recs.keys())
            products = Product.objects.filter(id__in=product_ids)
            
            for product in products:
                if product.id in combined_recs:
                    # Apply seasonal boost
                    if product.is_in_season(current_month, hemisphere):
                        combined_recs[product.id] *= (1 + self.seasonal_boost)
                    
                    # Apply location boost
                    if user_location and product.is_location_specific:
                        country = user_location.get('country')
                        region = user_location.get('region')
                        
                        if country and country in (product.available_countries or ''):
                            combined_recs[product.id] *= (1 + self.location_boost)
                        
                        if region and region in (product.available_regions or ''):
                            combined_recs[product.id] *= (1 + self.location_boost / 2)
        
        # Sort by score and return top n
        sorted_recs = sorted(combined_recs.items(), key=lambda x: x[1], reverse=True)
        return sorted_recs[:n]
    
    def save(self, cf_filename='collaborative_model.joblib', cb_filename='content_model.joblib'):
        """Save both models to disk"""
        if self.cf_model:
            self.cf_model.save(cf_filename)
        if self.cb_model:
            self.cb_model.save(cb_filename)
        
        # Save hybrid model parameters
        path = os.path.join(MODELS_DIR, 'hybrid_params.joblib')
        joblib.dump({
            'cf_weight': self.cf_weight,
            'cb_weight': self.cb_weight,
            'seasonal_boost': self.seasonal_boost,
            'location_boost': self.location_boost,
        }, path)
        logger.info(f"Hybrid recommender parameters saved to {path}")
    
    @classmethod
    def load(cls, cf_filename='collaborative_model.joblib', cb_filename='content_model.joblib'):
        """Load both models from disk"""
        # Load hybrid model parameters
        params_path = os.path.join(MODELS_DIR, 'hybrid_params.joblib')
        if os.path.exists(params_path):
            params = joblib.load(params_path)
            model = cls(cf_weight=params['cf_weight'], cb_weight=params['cb_weight'])
            model.seasonal_boost = params['seasonal_boost']
            model.location_boost = params['location_boost']
        else:
            model = cls()
        
        # Load collaborative filtering model
        model.cf_model = CollaborativeFilteringModel.load(cf_filename)
        
        # Load content-based filtering model
        model.cb_model = ContentBasedFilteringModel.load(cb_filename)
        
        # Check if both models were loaded successfully
        if model.cf_model is None or model.cb_model is None:
            logger.warning("One or both models failed to load")
            return None
        
        logger.info("Hybrid recommender loaded successfully")
        return model


def prepare_data_for_training():
    """
    Prepare data for training the recommendation models
    
    Returns:
        Tuple of (interactions_df, products_df)
    """
    # Get all interactions
    interactions = UserProductInteraction.objects.all()
    
    # Convert to DataFrame
    interactions_data = []
    for interaction in interactions:
        interactions_data.append({
            'user_id': interaction.user.id,
            'product_id': interaction.product.id,
            'interaction_type': interaction.interaction_type,
            'value': interaction.value
        })
    
    if not interactions_data:
        logger.warning("No interaction data found")
        return None, None
    
    interactions_df = pd.DataFrame(interactions_data)
    
    # Weight interactions: reviews (5x), purchases (3x), cart additions (2x), views (1x)
    interactions_df['weighted_value'] = interactions_df.apply(
        lambda row: row['value'] * (
            5 if row['interaction_type'] == 'review' else
            3 if row['interaction_type'] == 'purchase' else
            2 if row['interaction_type'] == 'cart' else 1
        ), axis=1
    )
    
    # Aggregate by user and product
    interactions_df = interactions_df.groupby(['user_id', 'product_id'])['weighted_value'].sum().reset_index()
    
    # Get all products
    products = Product.objects.all().select_related('category')
    
    # Convert to DataFrame
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category.name,
            'price': float(product.price),
            'featured': product.featured,
        })
    
    if not products_data:
        logger.warning("No product data found")
        return interactions_df, None
    
    products_df = pd.DataFrame(products_data)
    
    return interactions_df, products_df


def train_recommendation_models():
    """
    Train and save recommendation models
    """
    logger.info("Starting recommendation model training")
    
    # Prepare data
    interactions_df, products_df = prepare_data_for_training()
    
    if interactions_df is None or products_df is None:
        logger.error("Failed to prepare training data")
        return False
    
    # Train hybrid recommender
    try:
        recommender = HybridRecommender()
        recommender.fit(interactions_df, products_df)
        recommender.save()
        logger.info("Recommendation models trained and saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error training recommendation models: {e}")
        return False


def get_user_profile(user_id):
    """
    Get user profile for content-based recommendations
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with user profile data
    """
    # Get user's interactions
    interactions = UserProductInteraction.objects.filter(user_id=user_id)
    
    if not interactions:
        return {'liked_categories': [], 'liked_products': []}
    
    # Get products the user has interacted with
    product_ids = interactions.values_list('product_id', flat=True)
    products = Product.objects.filter(id__in=product_ids)
    
    # Get categories the user has shown interest in
    category_counts = {}
    for product in products:
        category_id = product.category_id
        if category_id in category_counts:
            category_counts[category_id] += 1
        else:
            category_counts[category_id] = 1
    
    # Get top categories
    liked_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    liked_categories = [cat_id for cat_id, count in liked_categories]
    
    # Get products with high ratings or multiple interactions
    liked_products = []
    for product_id in product_ids:
        product_interactions = interactions.filter(product_id=product_id)
        
        # Check if user rated the product highly
        reviews = product_interactions.filter(interaction_type='review')
        if reviews.exists() and reviews.first().value >= 4:
            liked_products.append(product_id)
            continue
        
        # Check if user purchased the product
        purchases = product_interactions.filter(interaction_type='purchase')
        if purchases.exists():
            liked_products.append(product_id)
            continue
        
        # Check if user has multiple interactions with the product
        if product_interactions.count() >= 2:
            liked_products.append(product_id)
    
    return {
        'liked_categories': liked_categories,
        'liked_products': liked_products
    }


def get_recommendations_for_user(user_id, limit=8):
    """
    Get recommended products for a user using the hybrid recommender
    
    Args:
        user_id: User ID
        limit: Number of recommendations to return
        
    Returns:
        List of Product objects
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
        return []
    
    # Load hybrid recommender
    recommender = HybridRecommender.load()
    if recommender is None:
        logger.warning("Failed to load hybrid recommender, training new models")
        if not train_recommendation_models():
            logger.error("Failed to train recommendation models")
            return []
        recommender = HybridRecommender.load()
        if recommender is None:
            logger.error("Failed to load newly trained models")
            return []
    
    # Get user profile for content-based recommendations
    user_profile = get_user_profile(user_id)
    
    # Get products the user has interacted with
    interacted_products = UserProductInteraction.objects.filter(user_id=user_id).values_list('product_id', flat=True)
    
    # Get current month and user's location for seasonal and location filtering
    current_month = datetime.now().month
    
    # Determine user's hemisphere based on country
    hemisphere = 'N'  # Default to Northern hemisphere
    user_location = None
    
    if hasattr(user, 'country') and user.country:
        northern_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'RU']
        southern_countries = ['AU', 'NZ', 'AR', 'BR', 'CL', 'ZA']
        
        if user.country in northern_countries:
            hemisphere = 'N'
        elif user.country in southern_countries:
            hemisphere = 'S'
        
        user_location = {
            'country': user.country,
            'region': user.state if hasattr(user, 'state') else None
        }
    
    # Get recommendations
    recommendations = recommender.recommend_for_user(
        user_id, 
        user_profile=user_profile,
        n=limit*2,
        exclude_items=list(interacted_products),
        current_month=current_month,
        hemisphere=hemisphere,
        user_location=user_location
    )
    
    if not recommendations:
        logger.warning(f"No recommendations generated for user {user_id}")
        return []
    
    # Get recommended product IDs
    product_ids = [product_id for product_id, _ in recommendations]
    
    # Get product objects
    products = list(Product.objects.filter(id__in=product_ids))
    
    # Sort products according to recommendation order
    product_dict = {product.id: product for product in products}
    sorted_products = [product_dict[product_id] for product_id in product_ids if product_id in product_dict]
    
    return sorted_products[:limit]


def get_similar_products(product_id, limit=4):
    """
    Get similar products for a given product using the hybrid recommender
    
    Args:
        product_id: Product ID
        limit: Number of similar products to return
        
    Returns:
        List of Product objects
    """
    # Load hybrid recommender
    recommender = HybridRecommender.load()
    if recommender is None:
        logger.warning("Failed to load hybrid recommender, training new models")
        if not train_recommendation_models():
            logger.error("Failed to train recommendation models")
            return []
        recommender = HybridRecommender.load()
        if recommender is None:
            logger.error("Failed to load newly trained models")
            return []
    
    # Get similar products
    similar_products = recommender.get_similar_items(product_id, n=limit)
    
    if not similar_products:
        logger.warning(f"No similar products found for product {product_id}")
        return []
    
    # Get similar product IDs
    product_ids = [product_id for product_id, _ in similar_products]
    
    # Get product objects
    products = list(Product.objects.filter(id__in=product_ids))
    
    # Sort products according to similarity order
    product_dict = {product.id: product for product in products}
    sorted_products = [product_dict[product_id] for product_id in product_ids if product_id in product_dict]
    
    return sorted_products
