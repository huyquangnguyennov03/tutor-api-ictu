"""
Intervention routes - Các endpoint cho can thiệp và đề xuất
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

try:
    from flask_auth import get_current_user, require_auth
except ImportError:
    # Fallback function nếu flask_auth không có
    def get_current_user():
        return {'role': 'admin', 'studentId': None}
    
    def require_auth(f):
        """Fallback decorator"""
        return f

from app import db
from app.models import (Student, Course, Progress, Warning, Assignment, Chapter, 
                       CommonError, BloomAssessment, Intervention)
from app.services.intervention_service import InterventionService

intervention_bp = Blueprint('intervention', __name__)
logger = logging.getLogger(__name__)

# Khởi tạo service
intervention_service = InterventionService()

@intervention_bp.route('/api/dashboard/predict-intervention/<string:studentid>', methods=['GET'])
def predict_intervention(studentid):
    """
    Dự đoán can thiệp cho sinh viên
    
    Args:
        studentid (str): ID sinh viên
        
    Returns:
        JSON: Kết quả dự đoán can thiệp
    """
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý dự đoán can thiệp cho studentid: {studentid}")
    
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        elif role != 'admin':
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Truy vấn dữ liệu
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()

        if not progress or not bloom:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ hoặc Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ hoặc Bloom'}), 404

        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        warnings = Warning.query.filter_by(studentid=studentid).all()

        # Sử dụng service để dự đoán can thiệp
        result = intervention_service.predict_intervention(
            studentid, student, progress, bloom, assignments, errors, warnings
        )
        
        logger.info(f"Hoàn thành xử lý dự đoán can thiệp trong {datetime.now() - start_time}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Không thể dự đoán can thiệp: {str(e)}")
        return jsonify({'error': f'Không thể dự đoán can thiệp: {str(e)}'}), 500