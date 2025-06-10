"""
Bloom Assessment model
"""
from app import db

class BloomAssessment(db.Model):
    """Model cho bảng đánh giá Bloom"""
    __tablename__ = 'bloomassessment'
    
    assessmentid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    bloomlevel = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=False)
    lastupdated = db.Column(db.Date, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'assessmentid': self.assessmentid,
            'studentid': self.studentid,
            'courseid': self.courseid,
            'bloomlevel': self.bloomlevel,
            'status': self.status,
            'score': self.score,
            'lastupdated': self.lastupdated.isoformat() if self.lastupdated else None
        }