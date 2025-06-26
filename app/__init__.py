"""
Factory pattern cho Flask application
"""
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

# Khởi tạo extensions
db = SQLAlchemy()

def create_app(config_name='default'):
    """
    Application factory pattern
    
    Args:
        config_name (str): Tên cấu hình ('development', 'production', 'default')
    
    Returns:
        Flask: Flask application instance
    """
    app = Flask(__name__)
    
    # Load cấu hình
    app.config.from_object(config[config_name])
    
    # Thiết lập logging
    logging.basicConfig(level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Khởi tạo extensions
    db.init_app(app)
    
    # Cấu hình CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Import và đăng ký blueprints
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # Import models để SQLAlchemy nhận diện
    from app.models import (Student, Course, Progress, Warning, Assignment, 
                           Chapter, CommonError, BloomAssessment, Intervention, 
                           CourseHistory, Teacher, Notification)
    
    # Thêm endpoint ping để kiểm tra uptime
    @app.route('/ping', methods=['GET'])
    def ping_service():
        from flask import jsonify
        return jsonify({'success': 'true'}), 200
    
    return app