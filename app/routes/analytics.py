"""
Analytics routes - Các endpoint cho phân tích và đánh giá
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify
try:
    from flask_auth import get_current_user
except ImportError:
    # Fallback function nếu flask_auth không có
    def get_current_user():
        return {'role': 'admin', 'studentId': None}
from app.models import Student, Progress, BloomAssessment, Assignment, CommonError, Warning
from app.services import MLService, LLMService, StudentService

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/evaluate-model', methods=['GET'])
def evaluate_model():
    """Đánh giá hiệu suất mô hình Machine Learning"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý đánh giá mô hình")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        ml_service = MLService()
        metrics = ml_service.get_model_metrics()
        response = {'metrics': metrics}
        logger.info(f"Hoàn thành xử lý đánh giá mô hình trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể đánh giá mô hình: {str(e)}")
        return jsonify({'error': f'Không thể đánh giá mô hình: {str(e)}'}), 500

@analytics_bp.route('/evaluate-llm/<string:studentid>', methods=['GET'])
def evaluate_llm(studentid):
    """Đánh giá hiệu suất LLM với các kịch bản khác nhau"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý đánh giá LLM cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        # Lấy dữ liệu sinh viên
        student_data = StudentService.get_student_data_for_prediction(studentid)
        if not student_data:
            logger.warning(f"Không tìm thấy dữ liệu cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu sinh viên'}), 404

        # Định nghĩa các kịch bản test
        scenarios = [
            {
                'name': 'Sinh viên nguy hiểm',
                'gpa': 1.8,
                'progressrate': 20,
                'bloomscore': 3,
                'num_submissions': 2,
                'num_errors': 5,
                'errors': ['Lỗi hàm: Truyền tham số không đúng kiểu', 'Lỗi cú pháp: Sai định dạng printf']
            },
            {
                'name': 'Sinh viên trung bình',
                'gpa': 3.0,
                'progressrate': 60,
                'bloomscore': 6,
                'num_submissions': 6,
                'num_errors': 2,
                'errors': ['Lỗi logic: Sai điều kiện if']
            },
            {
                'name': 'Sinh viên xuất sắc',
                'gpa': 3.8,
                'progressrate': 90,
                'bloomscore': 9,
                'num_submissions': 10,
                'num_errors': 0,
                'errors': []
            }
        ]

        # Đánh giá LLM với các kịch bản
        llm_service = LLMService()
        results = llm_service.evaluate_llm_scenarios(scenarios)

        # Thêm kịch bản thực tế của sinh viên
        warnings = Warning.query.filter(
            Warning.studentid == studentid,
            Warning.message.ilike('%Lỗi%')
        ).all()
        error_messages = [w.message for w in warnings]
        common_error_types = [e.type for e in student_data['errors']]
        
        actual_recommendation = llm_service.generate_intervention_recommendation({
            'gpa': student.totalgpa,
            'progressrate': student_data['progressrate'],
            'bloomscore': student_data['bloomscore'],
            'num_submissions': student_data['num_submissions']
        }, error_messages, common_error_types)
        
        results.append({
            'scenario': 'Thực tế',
            'recommendation': actual_recommendation
        })

        response = {
            'studentid': studentid,
            'evaluation_results': results
        }
        logger.info(f"Hoàn thành xử lý đánh giá LLM trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể đánh giá LLM: {str(e)}")
        return jsonify({'error': f'Không thể đánh giá LLM: {str(e)}'}), 500