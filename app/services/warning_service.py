"""
Warning Service - Xử lý tạo cảnh báo và lộ trình học tập
"""
from datetime import datetime
from app.models import Student, Progress, Warning, BloomAssessment, Course, CourseHistory, Assignment, CommonError
from app.services.ml_service import MLService

class WarningService:
    """Service xử lý cảnh báo và lộ trình học tập"""
    
    def __init__(self):
        self.ml_service = MLService()
    
    def encode_priority(self, priority):
        """Mã hóa priority"""
        mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        return mapping.get(priority, 1)

    def encode_severity(self, severity):
        """Mã hóa severity"""
        mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        return mapping.get(severity, 1)

    def encode_bloomlevel(self, bloomlevel):
        """Mã hóa bloom level"""
        mapping = {'Nhớ': 0, 'Hiểu': 1, 'Áp dụng': 2, 'Phân tích': 3, 'Đánh giá': 4, 'Sáng tạo': 5}
        return mapping.get(bloomlevel, 0)
    
    def generate_warning_message(self, student, progressrate, bloomscore, count_errors, priority, severity, bloomlevel, risk):
        """
        Tạo thông báo cảnh báo tùy chỉnh
        
        Args:
            student: Đối tượng Student
            progressrate (float): Tỷ lệ tiến độ
            bloomscore (float): Điểm Bloom
            count_errors (int): Số lỗi
            priority (float): Mức độ ưu tiên (đã mã hóa)
            severity (float): Mức độ nghiêm trọng (đã mã hóa)
            bloomlevel (int): Mức độ Bloom (đã mã hóa)
            risk (int): Dự đoán nguy cơ
            
        Returns:
            str: Thông báo cảnh báo
        """
        name = student.name
        gpa = student.totalgpa
        bloom_levels = ['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo']
        
        # Ưu tiên đánh giá tích cực nếu GPA và tiến độ cao
        if gpa >= 3.5 and progressrate >= 80 and count_errors <= 5 and severity <= 1:
            return f"Sinh viên {name} đang học tập tốt (GPA: {gpa}, Tiến độ: {progressrate}%, Lỗi: {count_errors}, Mức Bloom: {bloom_levels[bloomlevel]}). Hãy tiếp tục duy trì!"
        
        # Đánh giá nguy cơ cao nếu risk == 1 hoặc GPA thấp
        if risk == 1 or gpa < 2.0:
            reasons = []
            if gpa < 2.0:
                reasons.append(f"GPA thấp ({gpa})")
            if progressrate < 30:
                reasons.append(f"tiến độ học tập chậm ({progressrate}%)")
            if count_errors > 5:
                reasons.append(f"nhiều lỗi học thuật ({count_errors})")
            if severity >= 1.5:  # Ngưỡng severity cao hơn
                reasons.append("các cảnh báo có mức độ nghiêm trọng cao")
            if bloomscore < 5:
                reasons.append(f"điểm Bloom thấp ({bloomscore})")
            if bloomlevel <= 1:
                reasons.append(f"mức độ tư duy thấp ({bloom_levels[bloomlevel]})")
            if priority >= 1.5:
                reasons.append("các cảnh báo có ưu tiên cao")
            reasons_str = ", ".join(reasons) if reasons else "một số yếu tố cần cải thiện"
            return f"Sinh viên {name} có nguy cơ học vụ cao do {reasons_str}. Vui lòng tập trung cải thiện."
        
        # Trường hợp trung gian
        suggestions = []
        if gpa < 3.0:
            suggestions.append("nâng cao GPA")
        if progressrate < 60:
            suggestions.append("tăng tốc độ học tập")
        if count_errors >= 3:
            suggestions.append("giảm số lỗi học thuật")
        if bloomlevel <= 2:
            suggestions.append(f"phát triển tư duy ở mức cao hơn ({bloom_levels[bloomlevel]})")
        if bloomscore < 6:
            suggestions.append("cải thiện điểm Bloom")
        suggestions_str = ", ".join(suggestions) or "tiếp tục cải thiện tổng thể"
        return f"Sinh viên {name} cần {suggestions_str} để đạt kết quả tốt hơn (GPA: {gpa}, Tiến độ: {progressrate}%, Lỗi: {count_errors}, Mức Bloom: {bloom_levels[bloomlevel]})."
    
    def generate_learning_path(self, student, progressrate, bloomscore, count_errors, priority, severity, bloomlevel, risk):
        """
        Đề xuất lộ trình học tập
        
        Args:
            student: Đối tượng Student
            progressrate (float): Tỷ lệ tiến độ
            bloomscore (float): Điểm Bloom
            count_errors (int): Số lỗi
            priority (float): Mức độ ưu tiên (đã mã hóa)
            severity (float): Mức độ nghiêm trọng (đã mã hóa)
            bloomlevel (int): Mức độ Bloom (đã mã hóa)
            risk (int): Dự đoán nguy cơ
            
        Returns:
            dict: Thông tin lộ trình học tập
        """
        name = student.name
        gpa = student.totalgpa
        bloom_levels = ['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo']
        recommendations = []

        if risk == 1 or gpa < 2.0:
            recommendations.append("Tham gia các lớp bổ trợ để cải thiện kiến thức cơ bản.")
            if gpa < 2.0:
                recommendations.append("Tập trung nâng cao điểm GPA qua các bài tập và kỳ thi.")
            if progressrate < 30:
                recommendations.append("Tăng cường thời gian học tập để cải thiện tiến độ.")
            if count_errors > 5:
                recommendations.append("Xem lại các lỗi học thuật và tham gia hướng dẫn khắc phục.")
            if severity >= 1.5:
                recommendations.append("Ưu tiên giải quyết các cảnh báo nghiêm trọng.")
            if bloomscore < 5:
                recommendations.append("Luyện tập các bài tập Bloom để nâng cao điểm số.")
            if bloomlevel <= 1:
                recommendations.append(f"Tập trung phát triển kỹ năng tư duy {bloom_levels[bloomlevel + 1]}.")
        else:
            if gpa < 3.0:
                recommendations.append("Cải thiện GPA bằng cách hoàn thành tốt các bài tập và kỳ thi.")
            if progressrate < 60:
                recommendations.append("Tăng tốc độ học tập để đạt tiến độ tốt hơn.")
            if count_errors >= 3:
                recommendations.append("Giảm số lỗi học thuật bằng cách kiểm tra kỹ trước khi nộp.")
            if bloomlevel <= 2:
                recommendations.append(f"Phát triển kỹ năng tư duy ở mức {bloom_levels[bloomlevel + 1]} hoặc cao hơn.")
            if not recommendations:
                recommendations.append(f"Duy trì hiệu suất học tập tốt và thử thách với các bài tập {bloom_levels[min(bloomlevel + 1, 5)]}.")

        return {
            "studentid": student.studentid,
            "name": name,
            "gpa": gpa,
            "progressrate": progressrate,
            "bloomscore": bloomscore,
            "count_errors": count_errors,
            "priority": priority,
            "severity": severity,
            "bloomlevel": bloom_levels[bloomlevel],
            "risk": int(risk),
            "recommendations": recommendations
        }
    
    def create_warning_for_student(self, studentid):
        """
        Tạo cảnh báo cho sinh viên
        
        Args:
            studentid (str): ID sinh viên
            
        Returns:
            tuple: (success, message, data)
        """
        try:
            # Kiểm tra sinh viên tồn tại
            student = Student.query.get(studentid)
            if not student:
                return False, 'Không tìm thấy sinh viên', None
            
            # Kiểm tra tiến độ
            progress = Progress.query.filter_by(studentid=studentid).first()
            if not progress:
                return False, 'Không tìm thấy dữ liệu tiến độ', None
            
            # Kiểm tra đánh giá Bloom
            bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
            if not bloom:
                return False, 'Không tìm thấy đánh giá Bloom', None
            
            # Đếm tổng số lỗi và lấy priority, severity
            warnings = Warning.query.filter_by(studentid=studentid).all()
            count_errors = len(warnings)
            priority = sum([self.encode_priority(w.priority) for w in warnings]) / len(warnings) if warnings else self.encode_priority('LOW')
            severity = sum([self.encode_severity(w.severity) for w in warnings]) / len(warnings) if warnings else self.encode_severity('LOW')
            bloomlevel = self.encode_bloomlevel(bloom.bloomlevel)
            
            # Dự đoán rủi ro
            risk_prediction = self.ml_service.predict_risk(
                student.totalgpa, progress.progressrate, bloom.score, 
                count_errors, priority, severity, bloomlevel
            )
            
            # Tạo thông báo tùy chỉnh
            message = self.generate_warning_message(
                student, progress.progressrate, bloom.score, count_errors, 
                priority, severity, bloomlevel, risk_prediction
            )
            
            return True, 'Thông báo đã được tạo thành công', {
                'content': message,
                'risk': int(risk_prediction)
            }
            
        except Exception as e:
            return False, f'Không thể tạo thông báo: {str(e)}', None
    
    def get_learning_path_for_student(self, studentid):
        """
        Lấy lộ trình học tập cho sinh viên
        
        Args:
            studentid (str): ID sinh viên
            
        Returns:
            tuple: (success, message, data)
        """
        try:
            # Kiểm tra sinh viên tồn tại
            student = Student.query.get(studentid)
            if not student:
                return False, 'Không tìm thấy sinh viên', None
            
            # Lấy khóa học hiện tại
            current_course = Course.query.join(
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
                'category': current_course.category,
                'progressrate': Progress.query.filter_by(studentid=studentid, courseid=current_course.courseid).first().progressrate if current_course else 0.0
            } if current_course else {}
            
            # Lấy danh sách khóa học đã hoàn thành
            completed_courses = CourseHistory.query.filter_by(studentid=studentid).with_entities(CourseHistory.courseid).all()
            completed_course_ids = [c.courseid for c in completed_courses]
            
            # Lấy tất cả khóa học chưa hoàn thành (trừ khóa học hiện tại)
            all_courses = Course.query.filter(
                Course.courseid != (current_course.courseid if current_course else None),
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
            
            # Lấy dữ liệu tiến độ, Bloom, và cảnh báo
            progress = Progress.query.filter_by(studentid=studentid).first()
            bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
            
            if not progress:
                return False, 'Không tìm thấy dữ liệu tiến độ', None
            
            if not bloom:
                return False, 'Không tìm thấy đánh giá Bloom', None
            
            # Đếm số lỗi và lấy priority, severity
            warnings = Warning.query.filter_by(studentid=studentid).all()
            count_errors = min(len(warnings), 10)  # Giới hạn tối đa 10 lỗi
            priority = sum([self.encode_priority(w.priority) for w in warnings]) / len(warnings) if warnings else self.encode_priority('LOW')
            severity = sum([self.encode_severity(w.severity) for w in warnings]) / len(warnings) if warnings else self.encode_severity('LOW')
            bloomlevel = self.encode_bloomlevel(bloom.bloomlevel)
            
            # Dự đoán rủi ro
            risk_prediction = self.ml_service.predict_risk(
                student.totalgpa, progress.progressrate, bloom.score, 
                count_errors, priority, severity, bloomlevel
            )
            
            # Đề xuất khóa học
            recommended_courses = []
            if progress and bloom:
                if risk_prediction == 1 or student.totalgpa < 2.0:
                    recommended_courses = Course.query.filter(
                        Course.difficulty == 'BASIC',
                        Course.courseid != (current_course.courseid if current_course else None),
                        ~Course.courseid.in_(completed_course_ids)
                    ).limit(2).all()
                elif bloom.bloomlevel in ['Sáng tạo', 'Đánh giá']:
                    recommended_courses = Course.query.filter(
                        Course.difficulty == 'ADVANCED',
                        Course.courseid != (current_course.courseid if current_course else None),
                        ~Course.courseid.in_(completed_course_ids)
                    ).limit(2).all()
                else:
                    recommended_courses = Course.query.filter(
                        Course.difficulty == 'INTERMEDIATE',
                        Course.courseid != (current_course.courseid if current_course else None),
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
            
            # Phản hồi
            response = {
                'studentid': studentid,
                'current_course': current_course_data,
                'recommended_courses': recommended_courses_data,
                'all_courses': all_courses_data
            }
            
            return True, 'Lấy lộ trình học tập thành công', response
            
        except Exception as e:
            return False, f'Không thể lấy lộ trình học tập: {str(e)}', None