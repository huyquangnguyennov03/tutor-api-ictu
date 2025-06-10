"""
Student model
"""
from flask_sqlalchemy import SQLAlchemy

# Import db từ app package
from app import db

class Student(db.Model):
    """Model cho bảng sinh viên"""
    __tablename__ = 'student'
    
    studentid = db.Column(db.Text, primary_key=True, index=True)
    name = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Text, nullable=False)
    major = db.Column(db.Text, nullable=False)
    academicyear = db.Column(db.Text, nullable=False)
    totalcredits = db.Column(db.Integer, nullable=False)
    totalgpa = db.Column(db.Float, nullable=False)
    currentsemester = db.Column(db.Text, nullable=False)
    class_ = db.Column(db.Text, nullable=False, name='class')
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'studentid': self.studentid,
            'name': self.name,
            'grade': self.grade,
            'major': self.major,
            'academicyear': self.academicyear,
            'totalcredits': self.totalcredits,
            'totalgpa': self.totalgpa,
            'currentsemester': self.currentsemester,
            'class': self.class_
        }