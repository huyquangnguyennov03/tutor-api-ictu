"""
Course routes - Các endpoint liên quan đến khóa học
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
from app.models import (Course, Student, Progress, Assignment, Chapter, 
                       CommonError, BloomAssessment)
from app.services import StudentService
from app.utils import classify_student

course_bp = Blueprint('course', __name__)
logger = logging.getLogger(__name__)

@course_bp.route('/assignment-status/<int:assignmentid>', methods=['GET'])
def get_assignment_status(assignmentid):
    """Lấy trạng thái nộp bài của assignment"""
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

        response = StudentService.get_assignment_submission_details(assignment, course_students)
        logger.info(f"Hoàn thành xử lý trạng thái bài tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy trạng thái bài tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy trạng thái bài tập: {str(e)}'}), 500

@course_bp.route('/class-progress/<int:courseid>', methods=['GET'])
def get_class_progress(courseid):
    """Lấy tiến độ của cả lớp học"""
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

@course_bp.route('/chapter-details/<string:studentid>/<int:courseid>', methods=['GET'])
def get_chapter_details(studentid, courseid):
    """Lấy chi tiết chương học của sinh viên trong khóa học"""
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

@course_bp.route('/common-errors/<int:courseid>', methods=['GET'])
def get_course_common_errors(courseid):
    """Lấy danh sách lỗi thường gặp trong khóa học"""
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

@course_bp.route('/activity-rate/<int:courseid>', methods=['GET'])
def get_activity_rate(courseid):
    """Lấy tỷ lệ hoạt động của khóa học"""
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