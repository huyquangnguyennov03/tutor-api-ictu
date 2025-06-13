"""
Migration script để tạo bảng Notification
"""
import os
import sys
from app import create_app, db

def migrate_notification():
    """Tạo bảng notification trong database"""
    print("Bắt đầu migration cho bảng Notification...")
    
    try:
        # Tạo Flask app
        app = create_app(os.getenv('FLASK_ENV', 'default'))
        
        with app.app_context():
            # Import tất cả models để SQLAlchemy nhận diện
            from app.models import (Student, Course, Progress, Warning, Assignment, 
                                  Chapter, CommonError, BloomAssessment, Intervention, 
                                  CourseHistory, Teacher, Notification)
            
            print("Đã import tất cả models...")
            
            # Tạo bảng notification nếu chưa tồn tại
            db.create_all()
            print("Đã tạo tất cả bảng (bao gồm notification)...")
            
            # Kiểm tra bảng notification đã được tạo
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'notification' in tables:
                print("✅ Bảng 'notification' đã được tạo thành công!")
                
                # Kiểm tra cấu trúc bảng
                columns = inspector.get_columns('notification')
                print("\nCấu trúc bảng notification:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                
                # Kiểm tra indexes
                indexes = inspector.get_indexes('notification')
                if indexes:
                    print("\nIndexes:")
                    for idx in indexes:
                        print(f"  - {idx['name']}: {idx['column_names']}")
                
            else:
                print("❌ Bảng 'notification' chưa được tạo!")
                return False
            
            print("\n✅ Migration hoàn thành thành công!")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi khi migration: {str(e)}")
        return False

def check_notification_relationship():
    """Kiểm tra relationship giữa Student và Notification"""
    print("\nKiểm tra relationship Student-Notification...")
    
    try:
        app = create_app(os.getenv('FLASK_ENV', 'default'))
        
        with app.app_context():
            from app.models import Student, Notification
            
            # Lấy sinh viên đầu tiên
            student = Student.query.first()
            if student:
                print(f"Sinh viên: {student.name} ({student.studentid})")
                
                # Kiểm tra relationship
                notifications = student.notifications
                print(f"Số thông báo: {len(notifications)}")
                
                # Tạo thông báo test
                test_notification = Notification(
                    studentid=student.studentid,
                    message="Test notification từ migration script",
                    isread=False
                )
                
                db.session.add(test_notification)
                db.session.commit()
                
                print("✅ Tạo thông báo test thành công!")
                print(f"Notification ID: {test_notification.notificationid}")
                
                # Xóa thông báo test
                db.session.delete(test_notification)
                db.session.commit()
                print("✅ Xóa thông báo test thành công!")
                
            else:
                print("❌ Không tìm thấy sinh viên nào trong database")
                
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra relationship: {str(e)}")

if __name__ == "__main__":
    print("=== NOTIFICATION MIGRATION SCRIPT ===")
    
    # Chạy migration
    success = migrate_notification()
    
    if success:
        # Kiểm tra relationship
        check_notification_relationship()
        
        print("\n=== HƯỚNG DẪN SỬ DỤNG ===")
        print("1. Chạy app_new.py để khởi động server")
        print("2. Sử dụng test_notifications.py để test các endpoint")
        print("3. Tham khảo NOTIFICATION_API.md để biết chi tiết API")
    else:
        print("\n❌ Migration thất bại. Vui lòng kiểm tra lại cấu hình database.")
        sys.exit(1)