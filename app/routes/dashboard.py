"""
Dashboard routes - Các endpoint cho dashboard
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
try:
    from flask_auth import get_current_user
except ImportError:
    # Fallback function nếu flask_auth không có
    def get_current_user():
        return {'role': 'admin', 'studentId': None}
from app import db
from app.models import Student, Course, Progress, Warning, Assignment, Chapter, CommonError
from app.utils import classify_student

dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

@dashboard_bp.route('/students', methods=['GET'])
def get_students():
    """Lấy danh sách tất cả sinh viên"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        students = Student.query.all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên: {str(e)}'}), 500

@dashboard_bp.route('/courses', methods=['GET'])
def get_courses():
    """Lấy danh sách tất cả khóa học"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách khóa học")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        courses = Course.query.all()
        response = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'status': c.status,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in courses]
        logger.info(f"Hoàn thành xử lý danh sách khóa học trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách khóa học: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách khóa học: {str(e)}'}), 500

@dashboard_bp.route('/progress/<string:studentid>', methods=['GET'])
def get_progress(studentid):
    """Lấy tiến độ học tập của sinh viên cụ thể"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tiến độ cho studentid: {studentid}")
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
            progress = Progress.query.filter_by(studentid=user_studentid).all()
        elif role == 'admin':
            progress = Progress.query.filter_by(studentid=studentid).all()
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403

        if not progress:
            logger.warning(f"Không tìm thấy tiến độ cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy tiến độ cho sinh viên này'}), 404
        
        response = [{
            'progressid': p.progressid,
            'progressrate': p.progressrate,
            'completionrate': p.completionrate,
            'lastupdated': p.lastupdated.isoformat(),
            'courseid': p.courseid
        } for p in progress]
        logger.info(f"Hoàn thành xử lý tiến độ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tiến độ: {str(e)}")
        return jsonify({'error': f'Không thể lấy tiến độ: {str(e)}'}), 500

@dashboard_bp.route('/progress', methods=['GET'])
def get_all_progress():
    """Lấy toàn bộ tiến độ học tập"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý toàn bộ tiến độ")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        progress = Progress.query.all()
        response = [{
            'progressid': p.progressid,
            'studentid': p.studentid,
            'courseid': p.courseid,
            'progressrate': p.progressrate,
            'completionrate': p.completionrate,
            'lastupdated': p.lastupdated.isoformat()
        } for p in progress]
        logger.info(f"Hoàn thành xử lý toàn bộ tiến độ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy toàn bộ tiến độ: {str(e)}")
        return jsonify({'error': f'Không thể lấy toàn bộ tiến độ: {str(e)}'}), 500

@dashboard_bp.route('/students/excellent', methods=['GET'])
def get_excellent_students():
    """Lấy danh sách sinh viên xuất sắc"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên xuất sắc")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        excellent_students = Student.query.filter(Student.totalgpa >= 3.5).all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in excellent_students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên xuất sắc trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên xuất sắc: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên xuất sắc: {str(e)}'}), 500

@dashboard_bp.route('/students/needs-support', methods=['GET'])
def get_needs_support_students():
    """Lấy danh sách sinh viên cần hỗ trợ"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên cần hỗ trợ")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        needs_support_students = Student.query.filter(Student.totalgpa < 2.0).all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in needs_support_students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên cần hỗ trợ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên cần hỗ trợ: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên cần hỗ trợ: {str(e)}'}), 500

@dashboard_bp.route('/warnings', methods=['GET'])
def get_warnings():
    """Lấy danh sách cảnh báo chưa giải quyết"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách cảnh báo")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        warnings = Warning.query.filter_by(isresolved=False).all()
        response = [{
            'warningid': w.warningid,
            'studentid': w.studentid,
            'class': w.class_,
            'warningtype': w.warningtype,
            'message': w.message,
            'severity': w.severity,
            'priority': w.priority,
            'isnotified': w.isnotified
        } for w in warnings]
        logger.info(f"Hoàn thành xử lý danh sách cảnh báo trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách cảnh báo: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách cảnh báo: {str(e)}'}), 500

@dashboard_bp.route('/assignments', methods=['GET'])
def get_assignments():
    """Lấy danh sách tất cả bài tập"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách bài tập")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        assignments = Assignment.query.all()
        response = [{
            'assignmentid': a.assignmentid,
            'courseid': a.courseid,
            'name': a.name,
            'deadline': a.deadline.isoformat(),
            'submitted': a.submitted,
            'completionrate': a.completionrate,
            'status': a.status
        } for a in assignments]
        logger.info(f"Hoàn thành xử lý danh sách bài tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách bài tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách bài tập: {str(e)}'}), 500

@dashboard_bp.route('/chapters', methods=['GET'])
def get_chapters():
    """Lấy danh sách tất cả chương học"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách chương")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        chapters = Chapter.query.all()
        response = [{
            'chapterid': c.chapterid,
            'courseid': c.courseid,
            'name': c.name,
            'totalstudents': c.totalstudents,
            'completionrate': c.completionrate,
            'averagescore': c.averagescore,
            'studentscompleted': c.studentscompleted,
            'estimatedtime': c.estimatedtime
        } for c in chapters]
        logger.info(f"Hoàn thành xử lý danh sách chương trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách chương: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách chương: {str(e)}'}), 500

@dashboard_bp.route('/common-errors', methods=['GET'])
def get_common_errors():
    """Lấy danh sách lỗi thường gặp"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách lỗi thường gặp")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        errors = CommonError.query.all()
        response = [{
            'errorid': e.errorid,
            'courseid': e.courseid,
            'type': e.type,
            'description': e.description,
            'occurrences': e.occurrences,
            'studentsaffected': e.studentsaffected,
            'relatedchapters': e.relatedchapters
        } for e in errors]
        logger.info(f"Hoàn thành xử lý danh sách lỗi thường gặp trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách lỗi thường gặp: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách lỗi thường gặp: {str(e)}'}), 500

@dashboard_bp.route('/update-status', methods=['POST'])
def update_status():
    """Cập nhật trạng thái cảnh báo"""
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý cập nhật trạng thái cảnh báo")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        data = request.json
        warningid = data.get('warningid')
        status = data.get('status')

        warning = Warning.query.get(warningid)
        if not warning:
            logger.warning(f"Không tìm thấy cảnh báo {warningid}")
            return jsonify({'error': 'Không tìm thấy cảnh báo'}), 404

        if status == 'contacted':
            warning.isresolved = True
            warning.resolveddate = datetime.utcnow().date()
        else:
            logger.error(f"Trạng thái không hợp lệ: {status}")
            return jsonify({'error': 'Trạng thái không hợp lệ'}), 400

        db.session.commit()
        logger.info(f"Cập nhật trạng thái cảnh báo {warningid} thành công trong {datetime.now() - start_time}")
        return jsonify({'message': 'Cập nhật trạng thái thành công', 'warningid': warningid})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Không thể cập nhật trạng thái: {str(e)}")
        return jsonify({'error': f'Không thể cập nhật trạng thái: {str(e)}'}), 500