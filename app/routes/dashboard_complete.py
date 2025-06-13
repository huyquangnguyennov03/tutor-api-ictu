"""
Dashboard Complete - TẤT CẢ endpoints từ file app.py gốc
CẬP NHẬT SỬ DỤNG SERVICES
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
                       CommonError, BloomAssessment, Intervention, CourseHistory, Notification)
from app.services.ml_service import MLService
from app.services.warning_service import WarningService
from app.services.intervention_service import InterventionService

dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

# Khởi tạo services
ml_service = MLService()
warning_service = WarningService()
intervention_service = InterventionService()

# Hàm phân loại sinh viên dựa trên GPA
def classify_student(gpa):
    if gpa >= 3.5:
        return 'ĐẠT CHỈ TIÊU'
    elif gpa >= 3.0:
        return 'KHÁ'
    elif gpa >= 2.0:
        return 'CẦN CẢI THIỆN'
    else:
        return 'NGUY HIỂM'

@dashboard_bp.route('/students', methods=['GET'])
def get_students():
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

@dashboard_bp.route('/assignment-status/<int:assignmentid>', methods=['GET'])
def get_assignment_status(assignmentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý trạng thái bài tập cho assignmentid: {assignmentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        assignment = Assignment.query.get(assignmentid)
        if not assignment:
            logger.warning(f"Không tìm thấy bài tập {assignmentid}")
            return jsonify({'error': 'Không tìm thấy bài tập'}), 404

        course_students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == assignment.courseid).all()
        
        if not course_students:
            logger.warning(f"Không tìm thấy sinh viên cho khóa học {assignment.courseid}")
            return jsonify({'error': 'Không tìm thấy sinh viên cho khóa học này'}), 404

        # Logic xử lý assignment submission - GIỐNG HỆT FILE GỐC
        submitted_names = assignment.studentssubmitted.split(', ') if assignment.studentssubmitted else []
        not_submitted_names = assignment.studentsnotsubmitted.split(', ') if assignment.studentsnotsubmitted else []

        result_submitted = []
        result_not_submitted = []

        for student in course_students:
            progress = Progress.query.filter_by(studentid=student.studentid, courseid=assignment.courseid).first()
            bloom = BloomAssessment.query.filter_by(studentid=student.studentid, courseid=assignment.courseid).first()
            current_score = bloom.score if bloom else None

            student_info = {
                'studentid': student.studentid,
                'name': student.name,
                'progress': progress.progressrate if progress else 0,
                'current_score': current_score,
                'status': 'Đã nộp' if student.name in submitted_names else 'Chưa nộp'
            }

            if student.name in submitted_names:
                result_submitted.append(student_info)
            elif student.name in not_submitted_names:
                result_not_submitted.append(student_info)

        response = {
            'assignment_name': assignment.name,
            'deadline': assignment.deadline.isoformat(),
            'total_students': len(course_students),
            'submitted_count': len(submitted_names),
            'not_submitted_count': len(not_submitted_names),
            'submitted_students': result_submitted,
            'not_submitted_students': result_not_submitted
        }
        logger.info(f"Hoàn thành xử lý trạng thái bài tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy trạng thái bài tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy trạng thái bài tập: {str(e)}'}), 500

@dashboard_bp.route('/students/excellent', methods=['GET'])
def get_excellent_students():
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

@dashboard_bp.route('/student-report/<string:studentid>', methods=['GET'])
def get_student_report(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý báo cáo sinh viên cho studentid: {studentid}")
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

        progress = Progress.query.filter_by(studentid=studentid).all()
        warnings = Warning.query.filter_by(studentid=studentid, isresolved=False).all()
        bloom_assessments = BloomAssessment.query.filter_by(studentid=studentid).all()
        course_id = progress[0].courseid if progress else None
        assignments = Assignment.query.filter_by(courseid=course_id).all() if course_id else []
        chapters = Chapter.query.filter_by(courseid=course_id).all() if course_id else []
        interventions = Intervention.query.filter_by(studentid=studentid).all()

        suggestions_from_warnings = [{
            'id': w.warningid,
            'title': 'Đề xuất cải thiện',
            'content': w.message,
            'type': 'info'
        } for w in warnings if w.warningtype == 'THÔNG TIN']

        suggestions_from_interventions = [{
            'id': i.interventionid,
            'title': 'Đề xuất can thiệp',
            'content': i.recommendation,
            'type': 'info'
        } for i in interventions]

        all_suggestions = suggestions_from_warnings + suggestions_from_interventions

        response = {
            'student': {
                'studentid': student.studentid,
                'name': student.name,
                'totalgpa': student.totalgpa,
                'class': student.class_,
                'status': classify_student(student.totalgpa)
            },
            'progress': [{
                'progressid': p.progressid,
                'progressrate': p.progressrate,
                'completionrate': p.completionrate,
                'lastupdated': p.lastupdated.isoformat(),
                'courseid': p.courseid
            } for p in progress],
            'bloom_assessments': [{
                'assessmentid': b.assessmentid,
                'bloomlevel': b.bloomlevel,
                'status': b.status,
                'score': b.score,
                'lastupdated': b.lastupdated.isoformat()
            } for b in bloom_assessments],
            'warnings': [{
                'warningid': w.warningid,
                'class': w.class_,
                'warningtype': w.warningtype,
                'message': w.message,
                'severity': w.severity,
                'priority': w.priority
            } for w in warnings],
            'assignments': [{
                'assignmentid': a.assignmentid,
                'name': a.name,
                'deadline': a.deadline.isoformat(),
                'submitted': a.submitted,
                'completionrate': a.completionrate,
                'status': a.status
            } for a in assignments],
            'chapters': [{
                'chapterid': c.chapterid,
                'name': c.name,
                'completionrate': c.completionrate,
                'averagescore': c.averagescore,
                'estimatedtime': c.estimatedtime
            } for c in chapters],
            'suggestions': all_suggestions
        }
        logger.info(f"Hoàn thành xử lý báo cáo sinh viên trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy báo cáo sinh viên: {str(e)}")
        return jsonify({'error': f'Không thể lấy báo cáo sinh viên: {str(e)}'}), 500

@dashboard_bp.route('/predict-intervention/<string:studentid>', methods=['GET'])
def predict_intervention(studentid):
    """
    Dự đoán can thiệp cho sinh viên - Sử dụng InterventionService
    """
    start_time = datetime.now()
    logger.info(f"Dự đoán can thiệp cho sinh viên: {studentid}")

    user = get_current_user()
    if not user:
        logger.error("Lỗi: Thiếu dữ liệu người dùng")
        return jsonify({'error': 'Unauthorized: Thiếu dữ liệu người dùng'}), 401

    role, user_studentid = user.get('role'), user.get('studentId')

    # Kiểm tra quyền truy cập
    if not studentid or not isinstance(studentid, str):
        logger.error("ID sinh viên không hợp lệ")
        return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400

    if role == 'user':
        if not user_studentid or user_studentid != studentid:
            logger.error("Lỗi: Sinh viên chỉ truy cập dữ liệu của mình")
            return jsonify({'error': 'Unauthorized: Sinh viên chỉ truy cập dữ liệu của mình'}), 403
    elif role != 'admin':
        logger.error("Lỗi: Vai trò không hợp lệ")
        return jsonify({'error': 'Unauthorized: Vai trò không hợp lệ'}), 403

    try:
        # Truy vấn dữ liệu
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()

        if not progress or not bloom:
            logger.warning(f"Thiếu dữ liệu tiến độ hoặc Bloom cho {studentid}")
            return jsonify({'error': 'Thiếu dữ liệu tiến độ hoặc Bloom'}), 404

        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        warnings = Warning.query.filter_by(studentid=studentid).all()

        # Sử dụng service để dự đoán can thiệp
        result = intervention_service.predict_intervention(
            studentid, student, progress, bloom, assignments, errors, warnings
        )
        
        logger.info(f"Hoàn thành dự đoán trong {datetime.now() - start_time}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Lỗi dự đoán: {str(e)}")
        return jsonify({'error': f'Lỗi dự đoán: {str(e)}'}), 500

@dashboard_bp.route('/student-errors/<string:studentid>', methods=['GET'])
def get_student_errors(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý danh sách lỗi cho studentid: {studentid}")
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
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        warnings = Warning.query.filter_by(studentid=studentid).all()
        progress = Progress.query.filter_by(studentid=studentid).first()
        common_errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        
        response = {
            'studentid': studentid,
            'student_name': student.name,
            'personal_errors': [{
                'warningid': w.warningid,
                'message': w.message,
                'createddate': w.createddate.isoformat() if w.createddate else None,
                'severity': getattr(w, 'severity', 'medium')
            } for w in warnings],
            'common_errors': [{
                'errorid': e.errorid,
                'type': e.type,
                'description': e.description,
                'courseid': e.courseid
            } for e in common_errors],
            'total_personal_errors': len(warnings),
            'total_common_errors': len(common_errors)
        }
        logger.info(f"Hoàn thành xử lý danh sách lỗi trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách lỗi: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách lỗi: {str(e)}'}), 500

@dashboard_bp.route('/create-warning/<string:studentid>', methods=['POST'])
def create_warning(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu tạo thông báo cho studentid: {studentid}")
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
            
        # Sử dụng warning service để tạo cảnh báo
        success, message, data = warning_service.create_warning_for_student(studentid)
        
        if success:
            # Lưu thông báo vào bảng Notification
            new_notification = Notification(
                studentid=studentid,
                message=data['content'],
                createddate=datetime.utcnow().date(),
                isread=False
            )
            db.session.add(new_notification)
            db.session.commit()
            
            logger.info(f"Thông báo đã được tạo cho sinh viên {studentid} trong {datetime.now() - start_time}")
            return jsonify({
                'message': 'Thông báo đã được tạo cho sinh viên',
                'notificationid': new_notification.notificationid,
                'content': data['content'],
                'risk': data['risk']
            }), 201
        else:
            logger.error(f"Không thể tạo thông báo: {message}")
            return jsonify({'error': message}), 400 if 'không tìm thấy' in message.lower() else 500
    
    except Exception as e:
        logger.error(f"Không thể tạo thông báo: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Không thể tạo thông báo: {str(e)}'}), 500

@dashboard_bp.route('/class-progress/<int:courseid>', methods=['GET'])
def get_class_progress(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tiến độ lớp học cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        course = Course.query.filter_by(courseid=courseid).first()
        if not course:
            logger.warning(f"Không tìm thấy khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy khóa học'}), 404

        students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == courseid).all()
        total_students = len(students)
        
        if total_students == 0:
            logger.warning(f"Không tìm thấy sinh viên cho khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy sinh viên cho khóa học này'}), 404

        progress_data = Progress.query.filter_by(courseid=courseid).all()
        total_completion = sum(p.completionrate for p in progress_data) / total_students if progress_data else 0
        avg_gpa = sum(s.totalgpa for s in students) / total_students if students else 0

        active_students = sum(1 for p in progress_data if p.completionrate == 100)
        activity_rate = (active_students / total_students) * 100 if total_students > 0 else 0

        students_list = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'progress': next((p.progressrate for p in progress_data if p.studentid == s.studentid), 0),
            'status': classify_student(s.totalgpa)
        } for s in students]

        response = {
            'courseid': courseid,
            'coursename': course.coursename,
            'semester': course.semester,
            'total_students': total_students,
            'activity_rate': round(activity_rate, 2),
            'average_gpa': round(avg_gpa, 2),
            'completion_rate': round(total_completion, 2),
            'students': students_list
        }
        logger.info(f"Hoàn thành xử lý tiến độ lớp học trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tiến độ lớp học: {str(e)}")
        return jsonify({'error': f'Không thể lấy tiến độ lớp học: {str(e)}'}), 500

@dashboard_bp.route('/chapter-details/<string:studentid>/<int:courseid>', methods=['GET'])
def get_chapter_details(studentid, courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý chi tiết chương cho studentid: {studentid}, courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        chapters = Chapter.query.filter_by(courseid=courseid).all()
        progress = Progress.query.filter_by(studentid=studentid, courseid=courseid).first()
        
        if not progress or not chapters:
            logger.warning(f"Không tìm thấy dữ liệu chương hoặc tiến độ cho sinh viên {studentid}, khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu chương hoặc tiến độ sinh viên'}), 404

        chapter_details = [{
            'chapterid': chapter.chapterid,
            'name': chapter.name,
            'completion_rate': chapter.completionrate,
            'average_score': chapter.averagescore,
            'estimated_time': chapter.estimatedtime
        } for chapter in chapters]

        response = {
            'studentid': studentid,
            'courseid': courseid,
            'chapters': chapter_details
        }
        logger.info(f"Hoàn thành xử lý chi tiết chương trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy chi tiết chương: {str(e)}")
        return jsonify({'error': f'Không thể lấy chi tiết chương: {str(e)}'}), 500

@dashboard_bp.route('/common/courses/<int:courseid>', methods=['GET'])
def get_course_common_errors(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý lỗi chung cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        errors = CommonError.query.filter_by(courseid=courseid).all()
        if not errors:
            logger.warning(f"Không tìm thấy lỗi chung cho khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy lỗi chung nào cho khóa học này'}), 404

        response = [{
            'errorid': e.errorid,
            'type': e.type,
            'description': e.description,
            'occurrences': e.occurrences,
            'studentsaffected': e.studentsaffected,
            'relatedchapters': e.relatedchapters
        } for e in errors]
        logger.info(f"Hoàn thành xử lý lỗi chung trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy các lỗi chung cho khóa học: {str(e)}")
        return jsonify({'error': f'Không thể lấy các lỗi chung cho khóa học: {str(e)}'}), 500

@dashboard_bp.route('/update-status', methods=['POST'])
def update_status():
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

@dashboard_bp.route('/activity-rate/<int:courseid>', methods=['GET'])
def get_activity_rate(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tỷ lệ hoạt động cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        total_students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == courseid).distinct().count()
        
        if total_students == 0:
            logger.info(f"Tỷ lệ hoạt động cho khóa học {courseid}: 0.0 trong {datetime.now() - start_time}")
            return jsonify({'activity_rate': 0.0}), 200

        active_students = Progress.query.filter(
            Progress.courseid == courseid,
            Progress.completionrate >= 80
        ).count()

        activity_rate = (active_students / total_students) * 100 if total_students > 0 else 0
        response = {'activity_rate': round(activity_rate, 2)}
        logger.info(f"Hoàn thành xử lý tỷ lệ hoạt động trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tỷ lệ hoạt động: {str(e)}")
        return jsonify({'error': f'Không thể lấy tỷ lệ hoạt động cho khóa học {courseid}: {str(e)}'}), 500

@dashboard_bp.route('/learning-path/<string:studentid>', methods=['GET'])
def get_learning_path(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý lộ trình học tập cho studentid: {studentid}")
    
    # Kiểm tra quyền truy cập
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Kiểm tra quyền: Sinh viên chỉ xem được dữ liệu của mình
        if role == 'user' and user_studentid != studentid:
            logger.error("Unauthorized: Students can only access their own data")
            return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        
        # Sử dụng warning service để lấy lộ trình học tập
        success, message, data = warning_service.get_learning_path_for_student(studentid)
        
        if success:
            logger.info(f"Hoàn thành xử lý lộ trình học tập trong {datetime.now() - start_time}")
            return jsonify(data), 200
        else:
            logger.error(f"Không thể lấy lộ trình học tập: {message}")
            status_code = 404 if 'không tìm thấy' in message.lower() else 500
            return jsonify({'error': message}), status_code
    
    except Exception as e:
        logger.error(f"Không thể lấy lộ trình học tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy lộ trình học tập: {str(e)}'}), 500

@dashboard_bp.route('/evaluate-model', methods=['GET'])
def evaluate_model():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý đánh giá mô hình")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        # Sử dụng ML service để lấy metrics
        metrics = ml_service.get_model_metrics()
        response = {'metrics': metrics}
        logger.info(f"Hoàn thành xử lý đánh giá mô hình trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể đánh giá mô hình: {str(e)}")
        return jsonify({'error': f'Không thể đánh giá mô hình: {str(e)}'}), 500

@dashboard_bp.route('/evaluate-llm/<string:studentid>', methods=['GET'])
def evaluate_llm(studentid):
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

        # Lấy dữ liệu sinh viên - GIỐNG HỆT FILE GỐC
        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []

        if not progress or not bloom:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ hoặc Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ hoặc Bloom'}), 404

        def count_submissions():
            count = 0
            for assignment in assignments:
                if assignment.studentssubmitted:
                    submitted_students = assignment.studentssubmitted.split(', ')
                    if student.name in submitted_students:
                        count += 1
            return count

        num_submissions = count_submissions()
        num_errors = len(errors)

        # Định nghĩa các kịch bản test - GIỐNG HỆT FILE GỐC
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

        # Đánh giá LLM với các kịch bản - GIỐNG HỆT FILE GỐC
        results = []
        for scenario in scenarios:
            prompt = f"""
            Sinh viên có GPA là {scenario['gpa']}, tiến độ học tập là {scenario['progressrate']}%, điểm Bloom là {scenario['bloomscore']}, số lần nộp bài là {scenario['num_submissions']}.
            Các lỗi của sinh viên: {', '.join(scenario['errors']) if scenario['errors'] else 'Không có lỗi'}.
            Dựa trên thông tin này, hãy đưa ra các đề xuất cải thiện chi tiết, bao gồm giải thích lỗi, cách khắc phục, và ví dụ minh họa nếu có.
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp các đề xuất cải thiện học tập chi tiết và dễ hiểu."},
                    {"role": "user", "content": prompt}
                ]
            )
            recommendation = response.choices[0].message.content
            results.append({
                'scenario': scenario['name'],
                'recommendation': recommendation
            })

        # Thêm kịch bản thực tế của sinh viên - GIỐNG HỆT FILE GỐC
        warnings = Warning.query.filter(
            Warning.studentid == studentid,
            Warning.message.ilike('%Lỗi%')
        ).all()
        error_messages = [w.message for w in warnings]
        common_error_types = [e.type for e in errors]
        prompt = f"""
        Sinh viên có GPA là {student.totalgpa}, tiến độ học tập là {progress.progressrate}%, điểm Bloom là {bloom.score}, số lần nộp bài là {num_submissions}.
        Các lỗi của sinh viên: {', '.join(error_messages) if error_messages else 'Không có lỗi cụ thể'}.
        Các lỗi chung trong khóa học: {', '.join(common_error_types) if common_error_types else 'Không có lỗi chung'}.
        Dựa trên thông tin này, hãy đưa ra các đề xuất cải thiện chi tiết, bao gồm giải thích lỗi, cách khắc phục, và ví dụ minh họa nếu có.
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp các đề xuất cải thiện học tập chi tiết và dễ hiểu."},
                {"role": "user", "content": prompt}
            ]
        )
        actual_recommendation = response.choices[0].message.content
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

@dashboard_bp.route('/extend-deadline/<int:assignmentid>', methods=['POST'])
@require_auth
def extend_deadline(assignmentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý gia hạn deadline cho assignmentid: {assignmentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    if user.get('role') != 'admin':
        logger.error("Unauthorized: Only admins can extend deadlines")
        return jsonify({'error': 'Unauthorized: Only admins can extend deadlines'}), 403
    
    try:
        data = request.json
        new_deadline = data.get('new_deadline')  # Định dạng: YYYY-MM-DD
        if not new_deadline:
            logger.error("Missing new_deadline in request body")
            return jsonify({'error': 'Missing new_deadline in request body'}), 400

        # Chuyển đổi new_deadline thành đối tượng datetime.date
        try:
            new_deadline_date = datetime.strptime(new_deadline, '%Y-%m-%d').date()
        except ValueError:
            logger.error("Invalid date format for new_deadline. Use YYYY-MM-DD")
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        assignment = Assignment.query.get(assignmentid)
        if not assignment:
            logger.warning(f"Không tìm thấy bài tập {assignmentid}")
            return jsonify({'error': 'Không tìm thấy bài tập'}), 404

        # Kiểm tra nếu deadline mới hợp lệ (ví dụ: không sớm hơn ngày hiện tại)
        if new_deadline_date < datetime.utcnow().date():
            logger.error("New deadline cannot be in the past")
            return jsonify({'error': 'New deadline cannot be in the past'}), 400

        # Cập nhật deadline
        assignment.deadline = new_deadline_date
        db.session.commit()
        
        logger.info(f"Gia hạn deadline cho bài tập {assignmentid} thành công trong {datetime.now() - start_time}")
        return jsonify({
            'message': 'Gia hạn deadline thành công',
            'assignmentid': assignmentid,
            'new_deadline': assignment.deadline.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Không thể gia hạn deadline: {str(e)}")
        return jsonify({'error': f'Không thể gia hạn deadline: {str(e)}'}), 500