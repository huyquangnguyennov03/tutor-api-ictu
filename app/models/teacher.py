"""
Teacher model
"""
from app import db

class Teacher(db.Model):
    """Model cho bảng giáo viên"""
    __tablename__ = 'teacher'
    
    teacherid = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'teacherid': self.teacherid,
            'department': self.department,
            'subject': self.subject
        }