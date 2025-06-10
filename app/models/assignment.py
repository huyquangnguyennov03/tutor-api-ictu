"""
Assignment model
"""
from app import db

class Assignment(db.Model):
    """Model cho bảng bài tập"""
    __tablename__ = 'assignment'
    
    assignmentid = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    name = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    submitted = db.Column(db.Text, nullable=False)
    completionrate = db.Column(db.Float, nullable=False)
    status = db.Column(db.Text, nullable=False)
    studentssubmitted = db.Column(db.Text, nullable=False)
    studentsnotsubmitted = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        """Chuyển đổi object thành dictionary"""
        return {
            'assignmentid': self.assignmentid,
            'courseid': self.courseid,
            'name': self.name,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'submitted': self.submitted,
            'completionrate': self.completionrate,
            'status': self.status,
            'studentssubmitted': self.studentssubmitted,
            'studentsnotsubmitted': self.studentsnotsubmitted
        }