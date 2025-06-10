"""
Course History model
"""
from app import db

class CourseHistory(db.Model):
    """Model cho bảng lịch sử khóa học"""
    __tablename__ = 'coursehistory'
    
    historyid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    completedsemester = db.Column(db.Text, nullable=False)
    completeddate = db.Column(db.Date, nullable=False)
    finalscore = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'historyid': self.historyid,
            'studentid': self.studentid,
            'courseid': self.courseid,
            'completedsemester': self.completedsemester,
            'completeddate': self.completeddate.isoformat() if self.completeddate else None,
            'finalscore': self.finalscore
        }