"""
Main application file - Rút gọn sau khi chia tách
"""
import os
from app import create_app, db

# Tạo Flask app
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    with app.app_context():
        # Tạo các bảng database nếu chưa tồn tại
        db.create_all()
    
    # Chạy ứng dụng
    app.run(
        debug=app.config.get('DEBUG', True),
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 8000)
    )