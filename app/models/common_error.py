"""
Common Error model
"""
from app import db

class CommonError(db.Model):
    """Model cho bảng lỗi thường gặp"""
    __tablename__ = 'commonerror'
    
    errorid = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    type = db.Column(db.Text, nullable=False)
    occurrences = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    studentsaffected = db.Column(db.Integer, nullable=False)
    relatedchapters = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'errorid': self.errorid,
            'courseid': self.courseid,
            'type': self.type,
            'occurrences': self.occurrences,
            'description': self.description,
            'studentsaffected': self.studentsaffected,
            'relatedchapters': self.relatedchapters
        }