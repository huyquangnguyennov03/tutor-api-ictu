"""
Cấu hình ứng dụng Flask
"""
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

class Config:
    """Cấu hình cơ bản cho ứng dụng"""
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:17112003@localhost:5432/tutor_ai_v4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000"]
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Machine Learning
    MODEL_PATH = 'rf_model.pkl'
    
    # Logging
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000

class ProductionConfig(Config):
    """Cấu hình cho môi trường production"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8000

# Mapping cấu hình
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}