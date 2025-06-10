"""
Course model
"""
from app import db

class Course(db.Model):
    """Model cho bảng khóa học"""
    __tablename__ = 'course'
    
    courseid = db.Column(db.Integer, primary_key=True, index=True)
    coursename = db.Column(db.Text, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    prerequisite = db.Column(db.Text)
    semester = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Text, nullable=True)
    category = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'courseid': self.courseid,
            'coursename': self.coursename,
            'credits': self.credits,
            'prerequisite': self.prerequisite,
            'semester': self.semester,
            'status': self.status,
            'difficulty': self.difficulty,
            'category': self.category
        }