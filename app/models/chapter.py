"""
Chapter model
"""
from app import db

class Chapter(db.Model):
    """Model cho bảng chương học"""
    __tablename__ = 'chapter'
    
    chapterid = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    name = db.Column(db.Text, nullable=False)
    totalstudents = db.Column(db.Integer, nullable=False)
    completionrate = db.Column(db.Float, nullable=False)
    averagescore = db.Column(db.Float, nullable=False)
    studentscompleted = db.Column(db.Text, nullable=False)
    estimatedtime = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'chapterid': self.chapterid,
            'courseid': self.courseid,
            'name': self.name,
            'totalstudents': self.totalstudents,
            'completionrate': self.completionrate,
            'averagescore': self.averagescore,
            'studentscompleted': self.studentscompleted,
            'estimatedtime': self.estimatedtime
        }