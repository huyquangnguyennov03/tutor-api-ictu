"""
Progress model
"""
from app import db

class Progress(db.Model):
    """Model cho bảng tiến độ học tập"""
    __tablename__ = 'progress'
    
    progressid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    progressrate = db.Column(db.Float, nullable=False)
    completedcredits = db.Column(db.Integer, nullable=False)
    completionrate = db.Column(db.Float, nullable=False)
    lastupdated = db.Column(db.Date, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'progressid': self.progressid,
            'studentid': self.studentid,
            'courseid': self.courseid,
            'progressrate': self.progressrate,
            'completedcredits': self.completedcredits,
            'completionrate': self.completionrate,
            'lastupdated': self.lastupdated.isoformat() if self.lastupdated else None
        }