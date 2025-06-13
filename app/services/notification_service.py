"""
Notification Service - Xử lý logic nghiệp vụ cho thông báo
"""
import logging
import numpy as np
import pickle
import os
from datetime import datetime
from typing import List, Dict, Optional
from app import db
from app.models import (Notification, Student, Warning, Progress, 
                       BloomAssessment, Assignment, CommonError)

logger = logging.getLogger(__name__)

# Đường dẫn lưu mô hình
MODEL_PATH = 'rf_model.pkl'

class NotificationService:
    """Service xử lý các thao tác liên quan đến thông báo"""
    
    @staticmethod
    def create_notification(studentid: str, message: str) -> Notification:
        """
        Tạo thông báo mới cho sinh viên
        
        Args:
            studentid: ID sinh viên
            message: Nội dung thông báo
            
        Returns:
            Notification: Thông báo vừa tạo
            
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ
            Exception: Lỗi database
        """
        try:
            # Validate input
            if not studentid or not isinstance(studentid, str):
                raise ValueError("Student ID không hợp lệ")
            
            if not message or not isinstance(message, str):
                raise ValueError("Message không hợp lệ")
            
            # Kiểm tra sinh viên có tồn tại
            student = Student.query.filter_by(studentid=studentid).first()
            if not student:
                raise ValueError(f"Không tìm thấy sinh viên với ID: {studentid}")
            
            # Tạo notification
            notification = Notification(
                studentid=studentid,
                message=message,
                createddate=datetime.utcnow().date(),
                isread=False
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Tạo thành công thông báo cho sinh viên {studentid}")
            return notification
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi tạo thông báo: {str(e)}")
            raise Exception(f"Lỗi khi tạo thông báo: {str(e)}")
    
    @staticmethod
    def create_warning_with_notification(studentid: str, warning_data: Dict, 
                                       notification_message: Optional[str] = None) -> tuple:
        """
        Tạo cảnh báo và thông báo đồng thời
        
        Args:
            studentid: ID sinh viên
            warning_data: Dữ liệu cảnh báo
            notification_message: Nội dung thông báo (tùy chọn)
            
        Returns:
            tuple: (Warning, Notification)
        """
        try:
            # Validate input
            if not studentid or not isinstance(studentid, str):
                raise ValueError("Student ID không hợp lệ")
            
            # Kiểm tra sinh viên có tồn tại
            student = Student.query.filter_by(studentid=studentid).first()
            if not student:
                raise ValueError(f"Không tìm thấy sinh viên với ID: {studentid}")
            
            # Validate warning data
            required_fields = ['warningtype', 'message', 'severity', 'priority']
            for field in required_fields:
                if field not in warning_data or not warning_data[field]:
                    raise ValueError(f"Thiếu trường bắt buộc: {field}")
            
            # Tạo warning
            warning = Warning(
                studentid=studentid,
                class_=student.class_,
                warningtype=warning_data['warningtype'],
                message=warning_data['message'],
                severity=warning_data['severity'],
                priority=warning_data['priority'],
                createddate=datetime.utcnow().date(),
                isresolved=False,
                isnotified=False
            )
            
            # Tạo notification message
            if not notification_message:
                notification_message = f"Cảnh báo {warning_data['severity']}: {warning_data['message']}"
            
            notification = Notification(
                studentid=studentid,
                message=notification_message,
                createddate=datetime.utcnow().date(),
                isread=False
            )
            
            # Lưu vào database
            db.session.add(warning)
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Tạo thành công cảnh báo và thông báo cho sinh viên {studentid}")
            return warning, notification
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi tạo cảnh báo và thông báo: {str(e)}")
            raise Exception(f"Lỗi khi tạo cảnh báo và thông báo: {str(e)}")
    
    @staticmethod
    def get_student_notifications(studentid: str, limit: Optional[int] = None, 
                                only_unread: bool = False) -> List[Notification]:
        """
        Lấy danh sách thông báo của sinh viên
        
        Args:
            studentid: ID sinh viên
            limit: Giới hạn số lượng thông báo (tùy chọn)
            only_unread: Chỉ lấy thông báo chưa đọc
            
        Returns:
            List[Notification]: Danh sách thông báo
        """
        try:
            query = Notification.query.filter_by(studentid=studentid)
            
            if only_unread:
                query = query.filter_by(isread=False)
            
            query = query.order_by(Notification.createddate.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông báo: {str(e)}")
            raise Exception(f"Lỗi khi lấy thông báo: {str(e)}")
    
    @staticmethod
    def mark_notification_read(notification_id: int) -> bool:
        """
        Đánh dấu thông báo đã đọc
        
        Args:
            notification_id: ID thông báo
            
        Returns:
            bool: True nếu thành công
        """
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                raise ValueError(f"Không tìm thấy thông báo với ID: {notification_id}")
            
            notification.isread = True
            db.session.commit()
            
            logger.info(f"Đánh dấu thông báo {notification_id} đã đọc")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi đánh dấu thông báo: {str(e)}")
            raise Exception(f"Lỗi khi đánh dấu thông báo: {str(e)}")
    
    @staticmethod
    def mark_all_notifications_read(studentid: str) -> int:
        """
        Đánh dấu tất cả thông báo của sinh viên đã đọc
        
        Args:
            studentid: ID sinh viên
            
        Returns:
            int: Số lượng thông báo đã đánh dấu
        """
        try:
            count = Notification.query.filter_by(
                studentid=studentid, 
                isread=False
            ).update({'isread': True})
            
            db.session.commit()
            
            logger.info(f"Đánh dấu {count} thông báo đã đọc cho sinh viên {studentid}")
            return count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi đánh dấu tất cả thông báo: {str(e)}")
            raise Exception(f"Lỗi khi đánh dấu tất cả thông báo: {str(e)}")
    
    @staticmethod
    def get_unread_count(studentid: str) -> int:
        """
        Lấy số lượng thông báo chưa đọc của sinh viên
        
        Args:
            studentid: ID sinh viên
            
        Returns:
            int: Số lượng thông báo chưa đọc
        """
        try:
            return Notification.query.filter_by(
                studentid=studentid, 
                isread=False
            ).count()
            
        except Exception as e:
            logger.error(f"Lỗi khi đếm thông báo chưa đọc: {str(e)}")
            raise Exception(f"Lỗi khi đếm thông báo chưa đọc: {str(e)}")
    
    @staticmethod
    def delete_notification(notification_id: int) -> bool:
        """
        Xóa thông báo
        
        Args:
            notification_id: ID thông báo
            
        Returns:
            bool: True nếu thành công
        """
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                raise ValueError(f"Không tìm thấy thông báo với ID: {notification_id}")
            
            db.session.delete(notification)
            db.session.commit()
            
            logger.info(f"Xóa thông báo {notification_id} thành công")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi xóa thông báo: {str(e)}")
            raise Exception(f"Lỗi khi xóa thông báo: {str(e)}")
    
    @staticmethod
    def get_notification_stats(studentid: str) -> Dict:
        """
        Lấy thống kê thông báo của sinh viên
        
        Args:
            studentid: ID sinh viên
            
        Returns:
            Dict: Thống kê thông báo
        """
        try:
            total = Notification.query.filter_by(studentid=studentid).count()
            unread = Notification.query.filter_by(studentid=studentid, isread=False).count()
            read = total - unread
            
            return {
                'total': total,
                'read': read,
                'unread': unread,
                'unread_percentage': (unread / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy thống kê thông báo: {str(e)}")
            raise Exception(f"Lỗi khi lấy thống kê thông báo: {str(e)}")
    
    @staticmethod
    def create_ml_prediction_notification(studentid: str) -> Dict:
        """
        Tạo thông báo dựa trên dự đoán ML model
        
        Args:
            studentid: ID sinh viên
            
        Returns:
            Dict: Kết quả tạo thông báo
        """
        try:
            # Kiểm tra sinh viên tồn tại
            student = Student.query.get(studentid)
            if not student:
                logger.warning(f"Không tìm thấy sinh viên {studentid}")
                return {
                    'error': 'Không tìm thấy sinh viên',
                    'status_code': 404
                }
            
            # Kiểm tra tiến độ
            progress = Progress.query.filter_by(studentid=studentid).first()
            if not progress:
                logger.warning(f"Không tìm thấy dữ liệu tiến độ cho sinh viên {studentid}")
                return {
                    'error': 'Không tìm thấy dữ liệu tiến độ',
                    'status_code': 404
                }
            
            # Kiểm tra đánh giá Bloom
            bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
            if not bloom:
                logger.warning(f"Không tìm thấy đánh giá Bloom cho sinh viên {studentid}")
                return {
                    'error': 'Không tìm thấy đánh giá Bloom',
                    'status_code': 404
                }
            
            # Đếm số lần nộp bài
            def count_submissions():
                assignments = Assignment.query.all()
                total_submissions = sum(1 for a in assignments if studentid in a.studentssubmitted.split(','))
                return total_submissions
            
            num_submissions = count_submissions()
            
            # Tính số lỗi
            common_errors = CommonError.query.filter_by(courseid=progress.courseid).all()
            num_errors = sum(ce.occurrences for ce in common_errors)
            
            # Tải mô hình Random Forest
            if not os.path.exists(MODEL_PATH):
                logger.error(f"Không tìm thấy file mô hình: {MODEL_PATH}")
                return {
                    'error': 'Không tìm thấy mô hình ML',
                    'status_code': 500
                }
            
            with open(MODEL_PATH, 'rb') as f:
                rf_model = pickle.load(f)
            
            # Dự đoán rủi ro
            input_data = np.array([[student.totalgpa, progress.progressrate, bloom.score, num_submissions, num_errors]])
            risk_prediction = rf_model.predict(input_data)[0]
            
            # Kiểm tra điều kiện tạo thông báo
            if risk_prediction == 1 or student.totalgpa < 2.0:
                message = f"Sinh viên {student.name} có nguy cơ học vụ cao (GPA: {student.totalgpa}, Progress: {progress.progressrate}%, Số lần nộp bài: {num_submissions}, Số lỗi: {num_errors})"
                
                # Tạo thông báo mới
                new_notification = Notification(
                    studentid=studentid,
                    message=message,
                    createddate=datetime.utcnow().date(),
                    isread=False
                )
                db.session.add(new_notification)
                db.session.commit()
                
                logger.info(f"Thông báo đã được tạo cho sinh viên {studentid}")
                return {
                    'message': 'Thông báo đã được tạo cho sinh viên',
                    'notificationid': new_notification.notificationid,
                    'risk_prediction': int(risk_prediction),
                    'gpa': student.totalgpa,
                    'progress_rate': progress.progressrate,
                    'status_code': 201
                }
            else:
                logger.info(f"Không tạo thông báo, sinh viên {studentid} an toàn")
                return {
                    'message': 'Không tạo thông báo, sinh viên an toàn',
                    'risk_prediction': int(risk_prediction),
                    'gpa': student.totalgpa,
                    'progress_rate': progress.progressrate,
                    'status_code': 200
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi tạo thông báo ML: {str(e)}")
            return {
                'error': f'Lỗi khi tạo thông báo: {str(e)}',
                'status_code': 500
            }