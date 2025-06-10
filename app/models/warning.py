"""
Warning model
"""
from app import db

class Warning(db.Model):
    """Model cho bảng cảnh báo"""
    __tablename__ = 'warning'
    
    warningid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    class_ = db.Column(db.Text, nullable=False, name='class')
    warningtype = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False)
    isresolved = db.Column(db.Boolean, nullable=False, default=False)
    resolveddate = db.Column(db.Date)
    isnotified = db.Column(db.Boolean, nullable=False, default=False)
    notificationsentdate = db.Column(db.Date)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'warningid': self.warningid,
            'studentid': self.studentid,
            'class': self.class_,
            'warningtype': self.warningtype,
            'message': self.message,
            'severity': self.severity,
            'priority': self.priority,
            'createddate': self.createddate.isoformat() if self.createddate else None,
            'isresolved': self.isresolved,
            'resolveddate': self.resolveddate.isoformat() if self.resolveddate else None,
            'isnotified': self.isnotified,
            'notificationsentdate': self.notificationsentdate.isoformat() if self.notificationsentdate else None
        }