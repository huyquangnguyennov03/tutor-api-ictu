"""
Notification Model - Mô hình thông báo
"""
from datetime import datetime
from app import db

class Notification(db.Model):
    __tablename__ = 'notification'
    
    notificationid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    isread = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    student = db.relationship('Student', backref='notifications')
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'notificationid': self.notificationid,
            'studentid': self.studentid,
            'message': self.message,
            'createddate': self.createddate.isoformat() if self.createddate else None,
            'isread': self.isread
        }