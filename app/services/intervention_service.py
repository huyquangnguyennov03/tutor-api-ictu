"""
Intervention Service - Xử lý logic can thiệp và đề xuất
"""
import logging
from datetime import datetime
from app import db
from app.models import Intervention
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class InterventionService:
    """Service xử lý can thiệp và đề xuất"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def predict_intervention(self, studentid, student, progress, bloom, assignments, errors, warnings):
        """
        Dự đoán can thiệp cho sinh viên
        
        Args:
            studentid (str): ID sinh viên
            student (Student): Thông tin sinh viên
            progress (Progress): Tiến độ học tập
            bloom (BloomAssessment): Đánh giá Bloom
            assignments (list): Danh sách bài tập
            errors (list): Danh sách lỗi phổ biến
            warnings (list): Danh sách cảnh báo
            
        Returns:
            dict: Kết quả dự đoán can thiệp
        """
        start_time = datetime.now()
        logger.info(f"Bắt đầu xử lý dự đoán can thiệp cho studentid: {studentid}")
        
        try:
            # Chuẩn bị dữ liệu
            error_messages = [w.message for w in warnings]
            common_error_types = [e.type for e in errors]
            
            # Đếm số bài nộp
            num_submissions = sum(1 for a in assignments if a.studentssubmitted and student.name in a.studentssubmitted.split(', '))
            
            # Chuẩn bị dữ liệu sinh viên
            student_data = {
                'gpa': student.totalgpa,
                'progressrate': progress.progressrate,
                'bloomscore': bloom.score,
                'num_submissions': num_submissions
            }
            
            # Gọi LLM Service để tạo đề xuất
            recommendation = self.llm_service.generate_intervention_recommendation(
                student_data, error_messages, common_error_types
            )
            
            # Phân tích đề xuất
            parsed_suggestions = self.llm_service.parse_intervention_suggestions(
                recommendation, studentid, error_messages
            )
            
            # Lưu vào database
            new_intervention = Intervention(
                studentid=studentid,
                recommendation=recommendation,
                createddate=datetime.utcnow().date(),
                isapplied=False
            )
            db.session.add(new_intervention)
            db.session.commit()
            
            # Trả về kết quả
            response = {
                'studentid': studentid,
                'suggestions': parsed_suggestions,
                'interventionid': new_intervention.interventionid
            }
            
            logger.info(f"Hoàn thành xử lý dự đoán can thiệp trong {datetime.now() - start_time}")
            return response
            
        except Exception as e:
            logger.error(f"Không thể dự đoán can thiệp: {str(e)}")
            raise e