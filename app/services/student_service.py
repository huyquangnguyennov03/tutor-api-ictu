"""
Student Service - Business logic cho sinh viên
"""
from datetime import datetime
from app import db
from app.models import Student, Progress, Assignment, BloomAssessment, Warning, CommonError
from app.utils import classify_student

class StudentService:
    """Service xử lý logic nghiệp vụ cho sinh viên"""
    
    @staticmethod
    def count_student_submissions(student_name, assignments):
        """
        Đếm số lần nộp bài của sinh viên
        
        Args:
            student_name (str): Tên sinh viên
            assignments (list): Danh sách bài tập
            
        Returns:
            int: Số lần nộp bài
        """
        count = 0
        for assignment in assignments:
            if assignment.studentssubmitted:
                submitted_students = assignment.studentssubmitted.split(', ')
                if student_name in submitted_students:
                    count += 1
        return count
    
    @staticmethod
    def get_student_data_for_prediction(studentid):
        """
        Lấy dữ liệu sinh viên để dự đoán
        
        Args:
            studentid (str): ID sinh viên
            
        Returns:
            dict: Dữ liệu sinh viên hoặc None nếu không tìm thấy
        """
        student = Student.query.get(studentid)
        if not student:
            return None
            
        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        
        if not progress or not bloom:
            return None
            
        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        
        num_submissions = StudentService.count_student_submissions(student.name, assignments)
        num_errors = len(errors)
        
        return {
            'student': student,
            'progress': progress,
            'bloom': bloom,
            'assignments': assignments,
            'errors': errors,
            'num_submissions': num_submissions,
            'num_errors': num_errors,
            'gpa': student.totalgpa,
            'progressrate': progress.progressrate,
            'bloomscore': bloom.score
        }
    
    @staticmethod
    def create_warning_for_student(studentid, student_data, risk_prediction):
        """
        Tạo cảnh báo cho sinh viên nếu cần
        
        Args:
            studentid (str): ID sinh viên
            student_data (dict): Dữ liệu sinh viên
            risk_prediction (int): Kết quả dự đoán nguy cơ
            
        Returns:
            dict: Thông tin cảnh báo đã tạo hoặc None
        """
        student = student_data['student']
        progress = student_data['progress']
        num_submissions = student_data['num_submissions']
        num_errors = student_data['num_errors']
        
        if risk_prediction == 1 or student.totalgpa < 2.0:
            new_warning = Warning(
                studentid=studentid,
                class_=student.class_,
                warningtype='KHẨN CẤP',
                message=f'Sinh viên {student.name} có nguy cơ học vụ cao (GPA: {student.totalgpa}, Progress: {progress.progressrate}%, Số lần nộp bài: {num_submissions}, Số lỗi: {num_errors})',
                severity='HIGH',
                priority='HIGH',
                createddate=datetime.utcnow().date(),
                isnotified=True,
                notificationsentdate=datetime.utcnow().date()
            )
            db.session.add(new_warning)
            db.session.commit()
            return {
                'warningid': new_warning.warningid,
                'message': 'Cảnh báo đã được tạo và thông báo cho sinh viên'
            }
        
        return None
    
    @staticmethod
    def get_assignment_submission_details(assignment, course_students):
        """
        Lấy chi tiết nộp bài của assignment
        
        Args:
            assignment: Assignment object
            course_students: Danh sách sinh viên trong khóa học
            
        Returns:
            dict: Chi tiết submission
        """
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

        return {
            'assignment_name': assignment.name,
            'deadline': assignment.deadline.isoformat(),
            'total_students': len(course_students),
            'submitted_count': len(submitted_names),
            'not_submitted_count': len(not_submitted_names),
            'submitted_students': result_submitted,
            'not_submitted_students': result_not_submitted
        }