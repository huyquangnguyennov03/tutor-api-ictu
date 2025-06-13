"""
Notification Routes - API endpoints cho thông báo
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from app import db
from app.models import Student, Warning, Notification
from app.services.notification_service import NotificationService
from flask_auth import get_current_user

# Thiết lập logging
logger = logging.getLogger(__name__)

# Tạo Blueprint
notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/api/dashboard/create-warning/<string:studentid>', methods=['POST'])
def create_warning(studentid):
    """Tạo thông báo cho sinh viên dựa trên dự đoán ML"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu tạo thông báo cho studentid: {studentid}")
    
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
        
        # Kiểm tra quyền truy cập
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only create notifications for themselves")
                return jsonify({'error': 'Unauthorized: Students can only create notifications for themselves'}), 403
        
        # Sử dụng service để tạo thông báo dựa trên ML prediction
        result = NotificationService.create_ml_prediction_notification(studentid)
        
        logger.info(f"Hoàn thành tạo thông báo trong {datetime.now() - start_time}")
        return jsonify(result), result.get('status_code', 200)
        
    except ValueError as e:
        logger.error(f"Dữ liệu không hợp lệ: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Lỗi khi tạo thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi tạo thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/student-notifications/<string:studentid>', methods=['GET'])
def get_student_notifications(studentid):
    """Lấy danh sách thông báo của sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu lấy thông báo cho studentid: {studentid}")
    
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
        
        # Kiểm tra quyền truy cập
        target_studentid = None
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own notifications")
                return jsonify({'error': 'Unauthorized: Students can only access their own notifications'}), 403
            target_studentid = user_studentid
        elif role == 'admin':
            target_studentid = studentid
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Sử dụng service để lấy thông báo
        notifications = NotificationService.get_student_notifications(target_studentid)
        
        # Chuyển đổi thành response format
        response = [notification.to_dict() for notification in notifications]
        
        logger.info(f"Hoàn thành lấy thông báo trong {datetime.now() - start_time}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/notifications/<int:notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Đánh dấu thông báo đã đọc"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu đánh dấu thông báo đã đọc: {notification_id}")
    
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        # Tìm thông báo
        notification = Notification.query.get(notification_id)
        if not notification:
            logger.error(f"Không tìm thấy thông báo với ID: {notification_id}")
            return jsonify({'error': 'Không tìm thấy thông báo'}), 404
        
        # Kiểm tra quyền truy cập
        if role == 'user':
            if not user_studentid or user_studentid != notification.studentid:
                logger.error("Unauthorized: Students can only modify their own notifications")
                return jsonify({'error': 'Unauthorized: Students can only modify their own notifications'}), 403
        elif role != 'admin':
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Sử dụng service để đánh dấu đã đọc
        NotificationService.mark_notification_read(notification_id)
        
        response = {
            'notificationid': notification.notificationid,
            'message': 'Đánh dấu thông báo đã đọc thành công'
        }
        
        logger.info(f"Hoàn thành đánh dấu thông báo trong {datetime.now() - start_time}")
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error(f"Dữ liệu không hợp lệ: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Lỗi khi đánh dấu thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi đánh dấu thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/notifications/unread-count/<string:studentid>', methods=['GET'])
def get_unread_notifications_count(studentid):
    """Lấy số lượng thông báo chưa đọc của sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu đếm thông báo chưa đọc cho studentid: {studentid}")
    
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
        
        # Kiểm tra quyền truy cập
        target_studentid = None
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
            target_studentid = user_studentid
        elif role == 'admin':
            target_studentid = studentid
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Sử dụng service để đếm thông báo chưa đọc
        unread_count = NotificationService.get_unread_count(target_studentid)
        
        response = {
            'studentid': studentid,
            'unread_count': unread_count
        }
        
        logger.info(f"Hoàn thành đếm thông báo trong {datetime.now() - start_time}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Lỗi khi đếm thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi đếm thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/notifications/mark-all-read/<string:studentid>', methods=['PUT'])
def mark_all_notifications_read(studentid):
    """Đánh dấu tất cả thông báo của sinh viên đã đọc"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu đánh dấu tất cả thông báo đã đọc cho studentid: {studentid}")
    
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
        
        # Kiểm tra quyền truy cập
        target_studentid = None
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only modify their own notifications")
                return jsonify({'error': 'Unauthorized: Students can only modify their own notifications'}), 403
            target_studentid = user_studentid
        elif role == 'admin':
            target_studentid = studentid
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Sử dụng service để đánh dấu tất cả thông báo đã đọc
        count = NotificationService.mark_all_notifications_read(target_studentid)
        
        response = {
            'studentid': target_studentid,
            'marked_count': count,
            'message': f'Đánh dấu {count} thông báo đã đọc thành công'
        }
        
        logger.info(f"Hoàn thành đánh dấu tất cả thông báo trong {datetime.now() - start_time}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Lỗi khi đánh dấu tất cả thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi đánh dấu tất cả thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/notifications/stats/<string:studentid>', methods=['GET'])
def get_notification_stats(studentid):
    """Lấy thống kê thông báo của sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu lấy thống kê thông báo cho studentid: {studentid}")
    
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
        
        # Kiểm tra quyền truy cập
        target_studentid = None
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
            target_studentid = user_studentid
        elif role == 'admin':
            target_studentid = studentid
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        # Sử dụng service để lấy thống kê
        stats = NotificationService.get_notification_stats(target_studentid)
        stats['studentid'] = target_studentid
        
        logger.info(f"Hoàn thành lấy thống kê thông báo trong {datetime.now() - start_time}")
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy thống kê thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi lấy thống kê thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Xóa thông báo (chỉ admin)"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu xóa thông báo: {notification_id}")
    
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    if role != 'admin':
        logger.error("Unauthorized: Only admin can delete notifications")
        return jsonify({'error': 'Unauthorized: Only admin can delete notifications'}), 403
    
    try:
        # Sử dụng service để xóa thông báo
        NotificationService.delete_notification(notification_id)
        
        response = {
            'notificationid': notification_id,
            'message': 'Xóa thông báo thành công'
        }
        
        logger.info(f"Hoàn thành xóa thông báo trong {datetime.now() - start_time}")
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error(f"Dữ liệu không hợp lệ: {str(e)}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Lỗi khi xóa thông báo: {str(e)}")
        return jsonify({'error': f'Lỗi khi xóa thông báo: {str(e)}'}), 500

@notification_bp.route('/api/dashboard/create-manual-warning/<string:studentid>', methods=['POST'])
def create_manual_warning(studentid):
    """Tạo cảnh báo và thông báo thủ công cho sinh viên"""
    start_time = datetime.now()
    logger.info(f"Bắt đầu tạo cảnh báo thủ công cho studentid: {studentid}")
    
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    if role != 'admin':
        logger.error("Unauthorized: Only admin can create manual warnings")
        return jsonify({'error': 'Unauthorized: Only admin can create manual warnings'}), 403
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Kiểm tra sinh viên có tồn tại không
        student = Student.query.filter_by(studentid=studentid).first()
        if not student:
            logger.error(f"Không tìm thấy sinh viên với ID: {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        # Lấy dữ liệu từ request
        data = request.get_json()
        if not data:
            logger.error("Dữ liệu request không hợp lệ")
            return jsonify({'error': 'Dữ liệu request không hợp lệ'}), 400
        
        # Validate required fields
        required_fields = ['warningtype', 'message', 'severity', 'priority']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.error(f"Thiếu trường bắt buộc: {field}")
                return jsonify({'error': f'Thiếu trường bắt buộc: {field}'}), 400
        
        # Sử dụng service để tạo warning và notification
        new_warning, new_notification = NotificationService.create_warning_with_notification(
            studentid=studentid,
            warning_data=data
        )
        
        response = {
            'warningid': new_warning.warningid,
            'notificationid': new_notification.notificationid,
            'message': 'Tạo cảnh báo và thông báo thủ công thành công'
        }
        
        logger.info(f"Hoàn thành tạo cảnh báo thủ công trong {datetime.now() - start_time}")
        return jsonify(response), 201
        
    except ValueError as e:
        logger.error(f"Dữ liệu không hợp lệ: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Lỗi khi tạo cảnh báo thủ công: {str(e)}")
        return jsonify({'error': f'Lỗi khi tạo cảnh báo thủ công: {str(e)}'}), 500