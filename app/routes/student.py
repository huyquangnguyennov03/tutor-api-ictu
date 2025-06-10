"""
Student routes - Các endpoint liên quan đến sinh viên
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
from app.models import (Student, Progress, BloomAssessment, Warning, Assignment, 
                       Chapter, Intervention, CommonError, Course, CourseHistory)
from app.services import MLService, LLMService, StudentService
from app.utils import classify_student

student_bp = Blueprint('student', __name__)
logger = logging.getLogger(__name__)

@student_bp.route('/report/<string:studentid>', methods=['GET'])
def get_student_report(studentid):
    """Lấy báo cáo chi tiết của sinh viên"""
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

@student_bp.route('/predict-intervention/<string:studentid>', methods=['GET'])
def predict_intervention(studentid):
    """Dự đoán can thiệp cho sinh viên"""
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
        
        # Lấy dữ liệu sinh viên
        student_data = StudentService.get_student_data_for_prediction(studentid)
        if not student_data:
            logger.warning(f"Không tìm thấy dữ liệu cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu sinh viên'}), 404

        # Lấy danh sách lỗi
        warnings = Warning.query.filter_by(studentid=studentid).all()
        error_messages = [w.message for w in warnings]
        common_error_types = [e.type for e in student_data['errors']]

        # Tạo đề xuất can thiệp bằng LLM
        llm_service = LLMService()
        recommendation = llm_service.generate_intervention_recommendation(
            student_data, error_messages, common_error_types
        )

        # Phân tích đề xuất thành suggestions
        parsed_suggestions = llm_service.parse_intervention_suggestions(
            recommendation, studentid, error_messages
        )

        # Lưu intervention vào database
        new_intervention = Intervention(
            studentid=studentid,
            recommendation=recommendation,
            createddate=datetime.utcnow().date(),
            isapplied=False
        )
        db.session.add(new_intervention)
        db.session.commit()

        response = {
            'studentid': studentid,
            'suggestions': parsed_suggestions,
            'interventionid': new_intervention.interventionid
        }
        logger.info(f"Hoàn thành xử lý dự đoán can thiệp trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể dự đoán can thiệp: {str(e)}")
        return jsonify({'error': f'Không thể dự đoán can thiệp: {str(e)}'}), 500

@student_bp.route('/errors/<string:studentid>', methods=['GET'])
def get_student_errors(studentid):
    """Lấy danh sách lỗi của sinh viên"""
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

@student_bp.route('/create-warning/<string:studentid>', methods=['POST'])
def create_warning(studentid):
    """Tạo cảnh báo cho sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tạo cảnh báo cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Lấy dữ liệu sinh viên
        student_data = StudentService.get_student_data_for_prediction(studentid)
        if not student_data:
            logger.warning(f"Không tìm thấy dữ liệu cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu sinh viên'}), 404

        # Dự đoán nguy cơ
        ml_service = MLService()
        risk_prediction = ml_service.predict_risk(
            student_data['gpa'],
            student_data['progressrate'],
            student_data['bloomscore'],
            student_data['num_submissions'],
            student_data['num_errors']
        )

        # Tạo cảnh báo nếu cần
        warning_result = StudentService.create_warning_for_student(
            studentid, student_data, risk_prediction
        )

        if warning_result:
            logger.info(f"Cảnh báo đã được tạo cho sinh viên {studentid} trong {datetime.now() - start_time}")
            return jsonify(warning_result), 201

        logger.info(f"Không tạo cảnh báo, sinh viên {studentid} an toàn trong {datetime.now() - start_time}")
        return jsonify({'message': 'Không tạo cảnh báo, sinh viên an toàn'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Không thể tạo cảnh báo: {str(e)}")
        return jsonify({'error': f'Không thể tạo cảnh báo: {str(e)}'}), 500

@student_bp.route('/learning-path/<string:studentid>', methods=['GET'])
def get_learning_path(studentid):
    """Lấy lộ trình học tập cho sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý lộ trình học tập cho studentid: {studentid}")
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
        
        if role == 'user' and user_studentid != studentid:
            logger.error("Unauthorized: Students can only access their own data")
            return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        # Lấy khóa học hiện tại
        current_course = Course.query.select_from(Course).join(
            Progress, Progress.courseid == Course.courseid
        ).filter(
            Progress.studentid == studentid,
            Course.status == 'ACTIVE'
        ).first()

        current_course_data = {
            'courseid': current_course.courseid,
            'coursename': current_course.coursename,
            'credits': current_course.credits,
            'semester': current_course.semester,
            'difficulty': current_course.difficulty,
            'category': current_course.category
        } if current_course else {}

        # Lấy khóa học đã hoàn thành
        completed_courses = CourseHistory.query.filter_by(studentid=studentid).with_entities(CourseHistory.courseid).all()
        completed_course_ids = [c.courseid for c in completed_courses]
        
        # Lấy tất cả khóa học chưa học
        all_courses = Course.query.filter(
            Course.courseid != (current_course.courseid if current_course else 0),
            ~Course.courseid.in_(completed_course_ids)
        ).all()
        all_courses_data = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in all_courses]

        # Đề xuất khóa học dựa trên ML
        student_data = StudentService.get_student_data_for_prediction(studentid)
        recommended_courses = []
        
        if student_data:
            ml_service = MLService()
            risk_prediction = ml_service.predict_risk(
                student_data['gpa'],
                student_data['progressrate'],
                student_data['bloomscore'],
                student_data['num_submissions'],
                student_data['num_errors']
            )

            if risk_prediction == 1 or student.totalgpa < 2.0:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'BASIC',
                    Course.courseid != (current_course.courseid if current_course else 0),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
            elif student_data['bloom'].bloomlevel in ['Sáng tạo', 'Đánh giá']:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'ADVANCED',
                    Course.courseid != (current_course.courseid if current_course else 0),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
            else:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'INTERMEDIATE',
                    Course.courseid != (current_course.courseid if current_course else 0),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
        else:
            recommended_courses = Course.query.filter(
                Course.difficulty == 'BASIC',
                ~Course.courseid.in_(completed_course_ids)
            ).limit(2).all()

        recommended_courses_data = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in recommended_courses]

        response = {
            'studentid': studentid,
            'current_course': current_course_data,
            'recommended_courses': recommended_courses_data,
            'all_courses': all_courses_data
        }
        logger.info(f"Hoàn thành xử lý lộ trình học tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy lộ trình học tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy lộ trình học tập: {str(e)}'}), 500