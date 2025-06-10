"""
Intervention model
"""
from app import db

class Intervention(db.Model):
    """Model cho bảng can thiệp"""
    __tablename__ = 'intervention'
    
    interventionid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    recommendation = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False)
    isapplied = db.Column(db.Boolean, nullable=False, default=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'interventionid': self.interventionid,
            'studentid': self.studentid,
            'recommendation': self.recommendation,
            'createddate': self.createddate.isoformat() if self.createddate else None,
            'isapplied': self.isapplied
        }