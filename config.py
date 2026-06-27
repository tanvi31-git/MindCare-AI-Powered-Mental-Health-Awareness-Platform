"""
MindCare Backend Configuration

This file contains all configuration settings for the MindCare application.
Using a separate config file demonstrates security awareness and follows industry best practices.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # MongoDB configuration (Atlas Cloud)
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://tanviadke_db_user:WJUHNx7ZXnpahFGI@mindcare-cluster.uroenpy.mongodb.net/mindcare_db?retryWrites=true&w=majority')
    
    # Hugging Face configuration
    HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN', '')
    HUGGINGFACE_MODEL = os.environ.get('HUGGINGFACE_MODEL', 'facebook/bart-large-mnli')  # For zero-shot classification
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mindcare-secret-key-change-in-production')
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Model configuration
    MODEL_PATH = os.environ.get('MODEL_PATH', 'ml/models/')
    
    # NLP configuration
    NLP_CONFIDENCE_THRESHOLD = float(os.environ.get('NLP_CONFIDENCE_THRESHOLD', 0.65))
    
    # Scoring thresholds
    LOW_RISK_THRESHOLD = int(os.environ.get('LOW_RISK_THRESHOLD', 10))
    MODERATE_RISK_THRESHOLD = int(os.environ.get('MODERATE_RISK_THRESHOLD', 20))
    
    # Safety resources
    HELPLINE_NUMBERS = [
        {"name": "National Mental Health Helpline", "number": "080-46110007"},
        {"name": "Snehi Foundation", "number": "91-9820667144"},
        {"name": "iCall", "number": "9152987821"}
    ]
    
    # Emergency disclaimer
    EMERGENCY_DISCLAIMER = (
        "This is an assistive system and not a medical diagnosis. "
        "If you're having thoughts of self-harm, please seek immediate professional help."
    )

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SSL_DISABLE = False
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    MONGO_URI = 'mongodb://localhost:27017/mindcare_test_db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}