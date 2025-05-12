# E-commerce Recommendation System Backend

This is the Django backend for the E-commerce Recommendation System. It provides a RESTful API for the Angular frontend.

## Features

- User authentication and registration
- Product catalog with categories
- Shopping cart functionality
- Order processing with PesePay integration
- Advanced product recommendations using machine learning
  - Collaborative filtering using matrix factorization (SVD)
  - Content-based filtering using TF-IDF and cosine similarity
  - Hybrid recommendation approach combining both methods
  - Seasonal product recommendations
  - Location-based product filtering
- Product reviews and ratings
- Similar product suggestions

## Installation Instructions
1, Install Python 3.9+
2. Install the requirements using python package manager
pip install -r requirements.txt
3. start the django development server using manage.py
py manage.py runserver
4. Open frontend folder
5. install angular cli
6. run npm install
7. start development server using 
ng s -o
or simply navigate to https://e-recomandationsys.vercel.app makesure the backend is running first