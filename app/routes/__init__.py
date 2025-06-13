"""
Routes package - Đăng ký tất cả blueprints
QUAN TRỌNG: Trong file gốc, TẤT CẢ endpoints đều bắt đầu bằng /api/dashboard/
Vì vậy tôi sẽ gộp tất cả vào dashboard_bp để giữ nguyên URL
"""
from .dashboard_complete import dashboard_bp
from .notification import notification_bp
from .intervention import intervention_bp

def register_blueprints(app):
    """
    Đăng ký blueprint với Flask app
    GIỐNG HỆT FILE GỐC - TẤT CẢ ENDPOINTS ĐỀU BẮT ĐẦU BẰNG /api/dashboard/
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(notification_bp)
    app.register_blueprint(intervention_bp)