import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import pickle
import os
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import re
from flask_auth import get_current_user, require_auth, get_current_user_or_error

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load biến môi trường
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# Cấu hình CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Cấu hình kết nối PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Đường dẫn lưu mô hình
MODEL_PATH = 'rf_model.pkl'

# Hàm phân loại sinh viên dựa trên GPA
def classify_student(gpa):
    if gpa >= 3.5:
        return 'ĐẠT CHỈ TIÊU'
    elif gpa >= 3.0:
        return 'KHÁ'
    elif gpa >= 2.0:
        return 'CẦN CẢI THIỆN'
    else:
        return 'NGUY HIỂM'

# Định nghĩa các mô hình với chỉ mục để tối ưu truy vấn
class Student(db.Model):
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

class Course(db.Model):
    __tablename__ = 'course'
    courseid = db.Column(db.Integer, primary_key=True, index=True)
    coursename = db.Column(db.Text, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    prerequisite = db.Column(db.Text)
    semester = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Text, nullable=True)
    category = db.Column(db.Text, nullable=True)

class Progress(db.Model):
    __tablename__ = 'progress'
    progressid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    progressrate = db.Column(db.Float, nullable=False)
    completedcredits = db.Column(db.Integer, nullable=False)
    completionrate = db.Column(db.Float, nullable=False)
    lastupdated = db.Column(db.Date, nullable=False)

class Warning(db.Model):
    __tablename__ = 'warning'
    warningid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    class_ = db.Column(db.Text, nullable=False, name='class')
    warningtype = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False)
    isresolved = db.Column(db.Boolean, nullable=False, default=False)
    resolveddate = db.Column(db.Date)
    isnotified = db.Column(db.Boolean, nullable=False, default=False)
    notificationsentdate = db.Column(db.Date)

class Intervention(db.Model):
    __tablename__ = 'intervention'
    interventionid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    recommendation = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False)
    isapplied = db.Column(db.Boolean, nullable=False, default=False)

class CourseHistory(db.Model):
    __tablename__ = 'coursehistory'
    historyid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    completedsemester = db.Column(db.Text, nullable=False)
    completeddate = db.Column(db.Date, nullable=False)
    finalscore = db.Column(db.Float, nullable=False)

class BloomAssessment(db.Model):
    __tablename__ = 'bloomassessment'
    assessmentid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    bloomlevel = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=False)
    lastupdated = db.Column(db.Date, nullable=False)

class Assignment(db.Model):
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

class Chapter(db.Model):
    __tablename__ = 'chapter'
    chapterid = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    name = db.Column(db.Text, nullable=False)
    totalstudents = db.Column(db.Integer, nullable=False)
    completionrate = db.Column(db.Float, nullable=False)
    averagescore = db.Column(db.Float, nullable=False)
    studentscompleted = db.Column(db.Text, nullable=False)
    estimatedtime = db.Column(db.Integer, nullable=False)

class CommonError(db.Model):
    __tablename__ = 'commonerror'
    errorid = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), index=True)
    type = db.Column(db.Text, nullable=False)
    occurrences = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    studentsaffected = db.Column(db.Integer, nullable=False)
    relatedchapters = db.Column(db.Text, nullable=False)

class Teacher(db.Model):
    __tablename__ = 'teacher'
    teacherid = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text, nullable=False)

class Notification(db.Model):
    __tablename__ = 'notification'
    notificationid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    isread = db.Column(db.Boolean, nullable=False, default=False)

# Hàm mã hóa
def encode_priority(priority):
    mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    return mapping.get(priority, 1)

def encode_severity(severity):
    mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    return mapping.get(severity, 1)

def encode_bloomlevel(bloomlevel):
    mapping = {'Nhớ': 0, 'Hiểu': 1, 'Áp dụng': 2, 'Phân tích': 3, 'Đánh giá': 4, 'Sáng tạo': 5}
    return mapping.get(bloomlevel, 0)

# Hàm tạo thông báo tùy chỉnh
def generate_warning_message(student, progressrate, bloomscore, count_errors, priority, severity, bloomlevel, risk):
    name = student.name
    gpa = student.totalgpa
    bloom_levels = ['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo']
    
    # Ưu tiên đánh giá tích cực nếu GPA và tiến độ cao
    if gpa >= 3.5 and progressrate >= 80 and count_errors <= 5 and severity <= 1:
        return f"Sinh viên {name} đang học tập tốt (GPA: {gpa}, Tiến độ: {progressrate}%, Lỗi: {count_errors}, Mức Bloom: {bloom_levels[bloomlevel]}). Hãy tiếp tục duy trì!"
    
    # Đánh giá nguy cơ cao nếu risk == 1 hoặc GPA thấp
    if risk == 1 or gpa < 2.0:
        reasons = []
        if gpa < 2.0:
            reasons.append(f"GPA thấp ({gpa})")
        if progressrate < 30:
            reasons.append(f"tiến độ học tập chậm ({progressrate}%)")
        if count_errors > 5:
            reasons.append(f"nhiều lỗi học thuật ({count_errors})")
        if severity >= 1.5:  # Ngưỡng severity cao hơn
            reasons.append("các cảnh báo có mức độ nghiêm trọng cao")
        if bloomscore < 5:
            reasons.append(f"điểm Bloom thấp ({bloomscore})")
        if bloomlevel <= 1:
            reasons.append(f"mức độ tư duy thấp ({bloom_levels[bloomlevel]})")
        if priority >= 1.5:
            reasons.append("các cảnh báo có ưu tiên cao")
        reasons_str = ", ".join(reasons) if reasons else "một số yếu tố cần cải thiện"
        return f"Sinh viên {name} có nguy cơ học vụ cao do {reasons_str}. Vui lòng tập trung cải thiện."
    
    # Trường hợp trung gian
    suggestions = []
    if gpa < 3.0:
        suggestions.append("nâng cao GPA")
    if progressrate < 60:
        suggestions.append("tăng tốc độ học tập")
    if count_errors >= 3:
        suggestions.append("giảm số lỗi học thuật")
    if bloomlevel <= 2:
        suggestions.append(f"phát triển tư duy ở mức cao hơn ({bloom_levels[bloomlevel]})")
    if bloomscore < 6:
        suggestions.append("cải thiện điểm Bloom")
    suggestions_str = ", ".join(suggestions) or "tiếp tục cải thiện tổng thể"
    return f"Sinh viên {name} cần {suggestions_str} để đạt kết quả tốt hơn (GPA: {gpa}, Tiến độ: {progressrate}%, Lỗi: {count_errors}, Mức Bloom: {bloom_levels[bloomlevel]})."

# Hàm đề xuất lộ trình học tập
def generate_learning_path(student, progressrate, bloomscore, count_errors, priority, severity, bloomlevel, risk):
    name = student.name
    gpa = student.totalgpa
    bloom_levels = ['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo']
    recommendations = []

    if risk == 1 or gpa < 2.0:
        recommendations.append("Tham gia các lớp bổ trợ để cải thiện kiến thức cơ bản.")
        if gpa < 2.0:
            recommendations.append("Tập trung nâng cao điểm GPA qua các bài tập và kỳ thi.")
        if progressrate < 30:
            recommendations.append("Tăng cường thời gian học tập để cải thiện tiến độ.")
        if count_errors > 5:
            recommendations.append("Xem lại các lỗi học thuật và tham gia hướng dẫn khắc phục.")
        if severity >= 1.5:
            recommendations.append("Ưu tiên giải quyết các cảnh báo nghiêm trọng.")
        if bloomscore < 5:
            recommendations.append("Luyện tập các bài tập Bloom để nâng cao điểm số.")
        if bloomlevel <= 1:
            recommendations.append(f"Tập trung phát triển kỹ năng tư duy {bloom_levels[bloomlevel + 1]}.")
    else:
        if gpa < 3.0:
            recommendations.append("Cải thiện GPA bằng cách hoàn thành tốt các bài tập và kỳ thi.")
        if progressrate < 60:
            recommendations.append("Tăng tốc độ học tập để đạt tiến độ tốt hơn.")
        if count_errors >= 3:
            recommendations.append("Giảm số lỗi học thuật bằng cách kiểm tra kỹ trước khi nộp.")
        if bloomlevel <= 2:
            recommendations.append(f"Phát triển kỹ năng tư duy ở mức {bloom_levels[bloomlevel + 1]} hoặc cao hơn.")
        if not recommendations:
            recommendations.append(f"Duy trì hiệu suất học tập tốt và thử thách với các bài tập {bloom_levels[min(bloomlevel + 1, 5)]}.")

    return {
        "studentid": student.studentid,
        "name": name,
        "gpa": gpa,
        "progressrate": progressrate,
        "bloomscore": bloomscore,
        "count_errors": count_errors,
        "priority": priority,
        "severity": severity,
        "bloomlevel": bloom_levels[bloomlevel],
        "risk": int(risk),
        "recommendations": recommendations
    }

# Endpoint create-warning
@app.route('/api/dashboard/create-warning/<string:studentid>', methods=['POST'])
def create_warning(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu tạo thông báo cho studentid: {studentid}")
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Kiểm tra sinh viên tồn tại
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        # Kiểm tra tiến độ
        progress = Progress.query.filter_by(studentid=studentid).first()
        if not progress:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ'}), 404
        
        # Kiểm tra đánh giá Bloom
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        if not bloom:
            logger.warning(f"Không tìm thấy đánh giá Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy đánh giá Bloom'}), 404
        
        # Đếm tổng số lỗi và lấy priority, severity
        warnings = Warning.query.filter_by(studentid=studentid).all()
        count_errors = len(warnings)
        priority = sum([encode_priority(w.priority) for w in warnings]) / len(warnings) if warnings else encode_priority('LOW')
        severity = sum([encode_severity(w.severity) for w in warnings]) / len(warnings) if warnings else encode_severity('LOW')
        bloomlevel = encode_bloomlevel(bloom.bloomlevel)
        
        # Tải mô hình Random Forest
        with open(MODEL_PATH, 'rb') as f:
            rf_model = pickle.load(f)
        
        # Dự đoán rủi ro
        input_data = np.array([[student.totalgpa, progress.progressrate, bloom.score, count_errors, priority, severity, bloomlevel]])
        risk_prediction = rf_model.predict(input_data)[0]
        
        # Tạo thông báo tùy chỉnh
        message = generate_warning_message(
            student, progress.progressrate, bloom.score, count_errors, 
            priority, severity, bloomlevel, risk_prediction
        )
        
        # Lưu thông báo vào bảng Notification
        new_notification = Notification(
            studentid=studentid,
            message=message,
            createddate=datetime.utcnow().date(),
            isread=False
        )
        db.session.add(new_notification)
        db.session.commit()
        
        logger.info(f"Thông báo đã được tạo cho sinh viên {studentid} trong {datetime.now() - start_time}")
        return jsonify({
            'message': 'Thông báo đã được tạo cho sinh viên',
            'notificationid': new_notification.notificationid,
            'content': message
        }), 201
    
    except Exception as e:
        logger.error(f"Không thể tạo thông báo: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Không thể tạo thông báo: {str(e)}'}), 500

# Endpoint learning-path
@app.route('/api/dashboard/learning-path/<string:studentid>', methods=['GET'])
def get_learning_path(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý lộ trình học tập cho studentid: {studentid}")
    
    # Kiểm tra quyền truy cập
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Kiểm tra quyền: Sinh viên chỉ xem được dữ liệu của mình
        if role == 'user' and user_studentid != studentid:
            logger.error("Unauthorized: Students can only access their own data")
            return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        
        # Kiểm tra sinh viên tồn tại
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        # Lấy khóa học hiện tại
        current_course = Course.query.join(
            Progress, Progress.courseid == Course.courseid
        ).filter(
            Progress.studentid == studentid,
            Course.status == 'ACTIVE'
        ).first()
        
        current_course_data = {
            'courseid': current_course.courseid,
            'coursename': current_course.coursename,
            'credits': current_course.credits,
            'semester': current_course.semester,
            'difficulty': current_course.difficulty,
            'category': current_course.category,
            'progressrate': Progress.query.filter_by(studentid=studentid, courseid=current_course.courseid).first().progressrate if current_course else 0.0
        } if current_course else {}
        
        # Lấy danh sách khóa học đã hoàn thành
        completed_courses = CourseHistory.query.filter_by(studentid=studentid).with_entities(CourseHistory.courseid).all()
        completed_course_ids = [c.courseid for c in completed_courses]
        
        # Lấy tất cả khóa học chưa hoàn thành (trừ khóa học hiện tại)
        all_courses = Course.query.filter(
            Course.courseid != (current_course.courseid if current_course else None),
            ~Course.courseid.in_(completed_course_ids)
        ).all()
        all_courses_data = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in all_courses]
        
        # Lấy dữ liệu tiến độ, Bloom, và cảnh báo
        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        
        if not progress:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ'}), 404
        
        if not bloom:
            logger.warning(f"Không tìm thấy đánh giá Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy đánh giá Bloom'}), 404
        
        # Đếm số lỗi và lấy priority, severity
        warnings = Warning.query.filter_by(studentid=studentid).all()
        count_errors = min(len(warnings), 10)  # Giới hạn tối đa 10 lỗi
        priority = sum([encode_priority(w.priority) for w in warnings]) / len(warnings) if warnings else encode_priority('LOW')
        severity = sum([encode_severity(w.severity) for w in warnings]) / len(warnings) if warnings else encode_severity('LOW')
        bloomlevel = encode_bloomlevel(bloom.bloomlevel)
        
        # Lấy assignments và errors
        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        
        # Đếm số lần nộp bài
        def count_submissions():
            count = 0
            for assignment in assignments:
                if assignment.studentssubmitted:
                    submitted_students = assignment.studentssubmitted.split(', ')
                    if student.name in submitted_students:
                        count += 1
            return count
        
        num_submissions = count_submissions()
        
        # Tải mô hình Random Forest
        with open(MODEL_PATH, 'rb') as f:
            rf_model = pickle.load(f)
        
        # Dự đoán rủi ro với 7 đặc trưng
        input_data = np.array([[student.totalgpa, progress.progressrate, bloom.score, count_errors, priority, severity, bloomlevel]])
        logger.info(f"Input data: {input_data}, shape: {input_data.shape}")
        risk_prediction = rf_model.predict(input_data)[0]
        
        # Đề xuất khóa học
        recommended_courses = []
        if progress and bloom:
            if risk_prediction == 1 or student.totalgpa < 2.0:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'BASIC',
                    Course.courseid != (current_course.courseid if current_course else None),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
            elif bloom.bloomlevel in ['Sáng tạo', 'Đánh giá']:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'ADVANCED',
                    Course.courseid != (current_course.courseid if current_course else None),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
            else:
                recommended_courses = Course.query.filter(
                    Course.difficulty == 'INTERMEDIATE',
                    Course.courseid != (current_course.courseid if current_course else None),
                    ~Course.courseid.in_(completed_course_ids)
                ).limit(2).all()
        else:
            recommended_courses = Course.query.filter(
                Course.difficulty == 'BASIC',
                ~Course.courseid.in_(completed_course_ids)
            ).limit(2).all()
        
        recommended_courses_data = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in recommended_courses]
        
        # Phản hồi
        response = {
            'studentid': studentid,
            'current_course': current_course_data,
            'recommended_courses': recommended_courses_data,
            'all_courses': all_courses_data
        }
        
        logger.info(f"Hoàn thành xử lý lộ trình học tập trong {datetime.now() - start_time}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Không thể lấy lộ trình học tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy lộ trình học tập: {str(e)}'}), 500

# Hàm huấn luyện
def load_training_data():
    np.random.seed(42)
    n_samples = 250
    gpa = np.random.uniform(1.5, 4.0, n_samples)
    progressrate = np.random.uniform(10, 100, n_samples)
    bloomscore = np.random.uniform(2, 10, n_samples)
    count_errors = np.random.randint(0, 10, n_samples)
    priority = np.random.choice(['LOW', 'MEDIUM', 'HIGH'], n_samples)
    severity = np.random.choice(['LOW', 'MEDIUM', 'HIGH'], n_samples)
    bloomlevel = np.random.choice(['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo'], n_samples)
    priority_encoded = [encode_priority(p) for p in priority]
    severity_encoded = [encode_severity(s) for s in severity]
    bloomlevel_encoded = [encode_bloomlevel(b) for b in bloomlevel]
    risk = []
    for i in range(n_samples):
        if gpa[i] < 2.0 or progressrate[i] < 30 or count_errors[i] > 5 or severity_encoded[i] == 2:
            risk.append(1)
        elif gpa[i] >= 3.0 and progressrate[i] >= 70 and count_errors[i] <= 5 and severity_encoded[i] <= 1:
            risk.append(0)
        else:
            risk.append(np.random.choice([0, 1], p=[0.8, 0.2]))
    data = {
        'gpa': gpa,
        'progressrate': progressrate,
        'bloomscore': bloomscore,
        'count_errors': count_errors,
        'priority': priority_encoded,
        'severity': severity_encoded,
        'bloomlevel': bloomlevel_encoded,
        'risk': risk
    }
    df = pd.DataFrame(data)
    X = df[['gpa', 'progressrate', 'bloomscore', 'count_errors', 'priority', 'severity', 'bloomlevel']]
    y = df['risk']
    return X, y

def train_and_evaluate_model():
    X, y = load_training_data()
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(model, X, y, cv=5, scoring='f1')
    model.fit(X, y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='binary'),
        'recall': recall_score(y_test, y_pred, average='binary'),
        'f1': f1_score(y_test, y_pred, average='binary'),
        'f1_cv': scores.mean()
    }
    return model, metrics

if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        rf_model = pickle.load(f)
else:
    rf_model, _ = train_and_evaluate_model()
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(rf_model, f)

# API Endpoints
@app.route('/api/dashboard/students', methods=['GET'])
def get_students():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        students = Student.query.all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên: {str(e)}'}), 500

@app.route('/api/dashboard/courses', methods=['GET'])
def get_courses():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách khóa học")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        courses = Course.query.all()
        response = [{
            'courseid': c.courseid,
            'coursename': c.coursename,
            'credits': c.credits,
            'semester': c.semester,
            'status': c.status,
            'difficulty': c.difficulty,
            'category': c.category
        } for c in courses]
        logger.info(f"Hoàn thành xử lý danh sách khóa học trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách khóa học: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách khóa học: {str(e)}'}), 500

@app.route('/api/dashboard/progress/<string:studentid>', methods=['GET'])
def get_progress(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tiến độ cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
            progress = Progress.query.filter_by(studentid=user_studentid).all()
        elif role == 'admin':
            progress = Progress.query.filter_by(studentid=studentid).all()
        else:
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403

        if not progress:
            logger.warning(f"Không tìm thấy tiến độ cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy tiến độ cho sinh viên này'}), 404
        
        response = [{
            'progressid': p.progressid,
            'progressrate': p.progressrate,
            'completionrate': p.completionrate,
            'lastupdated': p.lastupdated.isoformat(),
            'courseid': p.courseid
        } for p in progress]
        logger.info(f"Hoàn thành xử lý tiến độ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tiến độ: {str(e)}")
        return jsonify({'error': f'Không thể lấy tiến độ: {str(e)}'}), 500

@app.route('/api/dashboard/progress', methods=['GET'])
def get_all_progress():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý toàn bộ tiến độ")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        progress = Progress.query.all()
        response = [{
            'progressid': p.progressid,
            'studentid': p.studentid,
            'courseid': p.courseid,
            'progressrate': p.progressrate,
            'completionrate': p.completionrate,
            'lastupdated': p.lastupdated.isoformat()
        } for p in progress]
        logger.info(f"Hoàn thành xử lý toàn bộ tiến độ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy toàn bộ tiến độ: {str(e)}")
        return jsonify({'error': f'Không thể lấy toàn bộ tiến độ: {str(e)}'}), 500

@app.route('/api/dashboard/assignment-status/<int:assignmentid>', methods=['GET'])
def get_assignment_status(assignmentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý trạng thái bài tập cho assignmentid: {assignmentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        assignment = Assignment.query.get(assignmentid)
        if not assignment:
            logger.warning(f"Không tìm thấy bài tập {assignmentid}")
            return jsonify({'error': 'Không tìm thấy bài tập'}), 404

        course_students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == assignment.courseid).all()
        if not course_students:
            logger.warning(f"Không tìm thấy sinh viên cho khóa học {assignment.courseid}")
            return jsonify({'error': 'Không tìm thấy sinh viên cho khóa học này'}), 404

        submitted_names = assignment.studentssubmitted.split(', ') if assignment.studentssubmitted else []
        not_submitted_names = assignment.studentsnotsubmitted.split(', ') if assignment.studentsnotsubmitted else []

        result_submitted = []
        result_not_submitted = []

        for student in course_students:
            progress = Progress.query.filter_by(studentid=student.studentid, courseid=assignment.courseid).first()
            bloom = BloomAssessment.query.filter_by(studentid=student.studentid, courseid=assignment.courseid).first()
            current_score = bloom.score if bloom else None

            student_info = {
                'studentid': student.studentid,
                'name': student.name,
                'progress': progress.progressrate if progress else 0,
                'current_score': current_score,
                'status': 'Đã nộp' if student.name in submitted_names else 'Chưa nộp'
            }

            if student.name in submitted_names:
                result_submitted.append(student_info)
            elif student.name in not_submitted_names:
                result_not_submitted.append(student_info)

        response = {
            'assignment_name': assignment.name,
            'deadline': assignment.deadline.isoformat(),
            'total_students': len(course_students),
            'submitted_count': len(submitted_names),
            'not_submitted_count': len(not_submitted_names),
            'submitted_students': result_submitted,
            'not_submitted_students': result_not_submitted
        }
        logger.info(f"Hoàn thành xử lý trạng thái bài tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy trạng thái bài tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy trạng thái bài tập: {str(e)}'}), 500

@app.route('/api/dashboard/students/excellent', methods=['GET'])
def get_excellent_students():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên xuất sắc")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        excellent_students = Student.query.filter(Student.totalgpa >= 3.5).all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in excellent_students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên xuất sắc trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên xuất sắc: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên xuất sắc: {str(e)}'}), 500

@app.route('/api/dashboard/students/needs-support', methods=['GET'])
def get_needs_support_students():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách sinh viên cần hỗ trợ")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        needs_support_students = Student.query.filter(Student.totalgpa < 2.0).all()
        response = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'status': classify_student(s.totalgpa)
        } for s in needs_support_students]
        logger.info(f"Hoàn thành xử lý danh sách sinh viên cần hỗ trợ trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách sinh viên cần hỗ trợ: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách sinh viên cần hỗ trợ: {str(e)}'}), 500

@app.route('/api/dashboard/warnings', methods=['GET'])
def get_warnings():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách cảnh báo")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        warnings = Warning.query.filter_by(isresolved=False).all()
        response = [{
            'warningid': w.warningid,
            'studentid': w.studentid,
            'class': w.class_,
            'warningtype': w.warningtype,
            'message': w.message,
            'severity': w.severity,
            'priority': w.priority,
            'isnotified': w.isnotified
        } for w in warnings]
        logger.info(f"Hoàn thành xử lý danh sách cảnh báo trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách cảnh báo: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách cảnh báo: {str(e)}'}), 500

@app.route('/api/dashboard/assignments', methods=['GET'])
def get_assignments():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách bài tập")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        assignments = Assignment.query.all()
        response = [{
            'assignmentid': a.assignmentid,
            'courseid': a.courseid,
            'name': a.name,
            'deadline': a.deadline.isoformat(),
            'submitted': a.submitted,
            'completionrate': a.completionrate,
            'status': a.status
        } for a in assignments]
        logger.info(f"Hoàn thành xử lý danh sách bài tập trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách bài tập: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách bài tập: {str(e)}'}), 500

@app.route('/api/dashboard/chapters', methods=['GET'])
def get_chapters():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách chương")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        chapters = Chapter.query.all()
        response = [{
            'chapterid': c.chapterid,
            'courseid': c.courseid,
            'name': c.name,
            'totalstudents': c.totalstudents,
            'completionrate': c.completionrate,
            'averagescore': c.averagescore,
            'studentscompleted': c.studentscompleted,
            'estimatedtime': c.estimatedtime
        } for c in chapters]
        logger.info(f"Hoàn thành xử lý danh sách chương trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách chương: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách chương: {str(e)}'}), 500

@app.route('/api/dashboard/common-errors', methods=['GET'])
def get_common_errors():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý danh sách lỗi thường gặp")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        errors = CommonError.query.all()
        response = [{
            'errorid': e.errorid,
            'courseid': e.courseid,
            'type': e.type,
            'description': e.description,
            'occurrences': e.occurrences,
            'studentsaffected': e.studentsaffected,
            'relatedchapters': e.relatedchapters
        } for e in errors]
        logger.info(f"Hoàn thành xử lý danh sách lỗi thường gặp trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách lỗi thường gặp: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách lỗi thường gặp: {str(e)}'}), 500

@app.route('/api/dashboard/student-report/<string:studentid>', methods=['GET'])
def get_student_report(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý báo cáo sinh viên cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        progress = Progress.query.filter_by(studentid=studentid).all()
        warnings = Warning.query.filter_by(studentid=studentid, isresolved=False).all()
        bloom_assessments = BloomAssessment.query.filter_by(studentid=studentid).all()
        course_id = progress[0].courseid if progress else None
        assignments = Assignment.query.filter_by(courseid=course_id).all() if course_id else []
        chapters = Chapter.query.filter_by(courseid=course_id).all() if course_id else []
        interventions = Intervention.query.filter_by(studentid=studentid).all()

        suggestions_from_warnings = [{
            'id': w.warningid,
            'title': 'Đề xuất cải thiện',
            'content': w.message,
            'type': 'info'
        } for w in warnings if w.warningtype == 'THÔNG TIN']

        suggestions_from_interventions = [{
            'id': i.interventionid,
            'title': 'Đề xuất can thiệp',
            'content': i.recommendation,
            'type': 'info'
        } for i in interventions]

        all_suggestions = suggestions_from_warnings + suggestions_from_interventions

        response = {
            'student': {
                'studentid': student.studentid,
                'name': student.name,
                'totalgpa': student.totalgpa,
                'class': student.class_,
                'status': classify_student(student.totalgpa)
            },
            'progress': [{
                'progressid': p.progressid,
                'progressrate': p.progressrate,
                'completionrate': p.completionrate,
                'lastupdated': p.lastupdated.isoformat(),
                'courseid': p.courseid
            } for p in progress],
            'bloom_assessments': [{
                'assessmentid': b.assessmentid,
                'bloomlevel': b.bloomlevel,
                'status': b.status,
                'score': b.score,
                'lastupdated': b.lastupdated.isoformat()
            } for b in bloom_assessments],
            'warnings': [{
                'warningid': w.warningid,
                'class': w.class_,
                'warningtype': w.warningtype,
                'message': w.message,
                'severity': w.severity,
                'priority': w.priority
            } for w in warnings],
            'assignments': [{
                'assignmentid': a.assignmentid,
                'name': a.name,
                'deadline': a.deadline.isoformat(),
                'submitted': a.submitted,
                'completionrate': a.completionrate,
                'status': a.status
            } for a in assignments],
            'chapters': [{
                'chapterid': c.chapterid,
                'name': c.name,
                'completionrate': c.completionrate,
                'averagescore': c.averagescore,
                'estimatedtime': c.estimatedtime
            } for c in chapters],
            'suggestions': all_suggestions
        }
        logger.info(f"Hoàn thành xử lý báo cáo sinh viên trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy báo cáo sinh viên: {str(e)}")
        return jsonify({'error': f'Không thể lấy báo cáo sinh viên: {str(e)}'}), 500

@app.route('/api/dashboard/predict-intervention/<string:studentid>', methods=['GET'])
def predict_intervention(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý dự đoán can thiệp cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        elif role != 'admin':
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []

        if not progress or not bloom:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ hoặc Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ hoặc Bloom'}), 404

        warnings = Warning.query.filter_by(studentid=studentid).all()
        error_messages = [w.message for w in warnings]
        common_error_types = [e.type for e in errors]

        def count_submissions():
            count = 0
            for assignment in assignments:
                if assignment.studentssubmitted:
                    submitted_students = assignment.studentssubmitted.split(', ')
                    if student.name in submitted_students:
                        count += 1
            return count

        num_submissions = count_submissions()

        prompt = f"""
        Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp phân tích lỗi và đề xuất cải thiện chi tiết, ngắn gọn, dễ hiểu bằng tiếng Việt, dành cho sinh viên học lập trình.

        Dưới đây là thông tin sinh viên:
        - GPA: {student.totalgpa}
        - Tiến độ học tập: {progress.progressrate}%
        - Điểm Bloom: {bloom.score}
        - Số lần nộp bài: {num_submissions}

        ## Danh sách tất cả lỗi và cảnh báo của sinh viên (cần phân tích):
        {'\n'.join([f'- {error}' for error in error_messages]) if error_messages else 'Không có lỗi hoặc cảnh báo cụ thể'}

        ## Các lỗi phổ biến trong khóa học (chỉ tham khảo để liên hệ nếu có liên quan):
        {', '.join(common_error_types) if common_error_types else 'Không có lỗi chung'}

        ---

        ### 🎯 Yêu cầu phản hồi:
        1. **Phân tích chi tiết từng lỗi và cảnh báo của sinh viên** (dựa trên danh sách trên), **không được bỏ sót bất kỳ mục nào**.
        2. Mỗi lỗi hãy sử dụng định dạng markdown sau:

        ---

        ## Lỗi [số thứ tự]: [Tên lỗi]
        ### 1. Phân tích lỗi
        - Mô tả lỗi: [Mô tả ngắn gọn lỗi xảy ra trong hoàn cảnh nào, biểu hiện ra sao – tối đa 2-3 câu].
        - Nguyên nhân: [Lý do sinh viên mắc lỗi, ví dụ: thiếu hiểu biết về cú pháp, nhầm lẫn logic – tối đa 2 câu].

        ### 2. Đề xuất cải thiện
        - Cách khắc phục: [Hướng dẫn cụ thể, ngắn gọn, từng bước nếu cần – tối đa 3-4 câu].
        - Ví dụ minh họa (nếu áp dụng):
        ```c
        [Đoạn mã minh họa cách sửa lỗi. Ưu tiên dùng C/C++ trừ khi lỗi thuộc ngôn ngữ khác. Nếu không có ví dụ mã, giải thích lý do.]
        ```

        ---

        3. Nếu không có lỗi hoặc cảnh báo cụ thể, cung cấp đề xuất chung để cải thiện hiệu suất học tập, tập trung vào kỹ năng lập trình, với định dạng:
        ## Đề xuất cải thiện chung
        - Mô tả: [Mô tả ngắn gọn tình trạng học tập hiện tại dựa trên GPA, tiến độ, điểm Bloom].
        - Đề xuất: [Hướng dẫn cụ thể, ví dụ: cải thiện kỹ năng debug, đọc tài liệu – tối đa 3-4 câu].

        **Ví dụ phản hồi**:
        ## Lỗi 1: Lỗi hàm: Truyền tham số không đúng kiểu
        ### 1. Phân tích lỗi
        - Mô tả lỗi: Lỗi xảy ra khi truyền tham số kiểu chuỗi vào hàm yêu cầu kiểu số nguyên, gây lỗi biên dịch.
        - Nguyên nhân: Sinh viên chưa nắm rõ cách khai báo và sử dụng kiểu dữ liệu trong C/C++.

        ### 2. Đề xuất cải thiện
        - Cách khắc phục: Kiểm tra kiểu dữ liệu của tham số trước khi truyền vào hàm, đảm bảo khớp với định nghĩa hàm.
        - Ví dụ minh họa:
        ```c
        // Sai:
        void tinhTong(int a, int b) {{ printf("%d", a + b); }}
        tinhTong("10", 20); // Lỗi kiểu dữ liệu
        // Đúng:
        tinhTong(10, 20);
        ```

        ## Đề xuất cải thiện chung
        - Mô tả: Sinh viên có GPA cao và tiến độ tốt, nhưng cần cải thiện kỹ năng debug.
        - Đề xuất: Thực hành debug bằng cách sử dụng công cụ như gdb và đọc tài liệu về cú pháp C/C++.

        Đảm bảo trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, và sử dụng ngôn ngữ lập trình C/C++ cho ví dụ minh họa trừ khi lỗi yêu cầu ngôn ngữ khác. Phản hồi phải bao gồm tất cả lỗi được liệt kê và tuân thủ nghiêm ngặt định dạng markdown.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp phân tích lỗi và đề xuất cải thiện chi tiết và dễ hiểu bằng tiếng Việt."},
                {"role": "user", "content": prompt}
            ]
        )

        recommendation = response.choices[0].message.content

        error_sections = re.split(r'## Lỗi \d+:', recommendation)[1:]
        parsed_suggestions = []

        for i, section in enumerate(error_sections, 1):
            name_match = re.match(r'([^\n]+)\n', section)
            error_name = name_match.group(1).strip() if name_match else f"Lỗi {i}"

            parts = re.split(r'### \d+\.', section)
            error_analysis = parts[1].strip() if len(parts) > 1 else "Không có phân tích chi tiết"
            improvement_suggestion = parts[2].strip() if len(parts) > 2 else "Không có đề xuất chi tiết"

            parsed_suggestions.append({
                'id': f"error_{i}_{studentid}",
                'title': f"Đề xuất cải thiện cho {error_name}",
                'content': f"## {error_name}\n{error_analysis}\n### Đề xuất cải thiện\n{improvement_suggestion}",
                'type': 'info'
            })

        if not error_messages:
            general_section = re.search(r'## Đề xuất cải thiện chung.*?$(.*?)(?=(##|$))', recommendation, re.DOTALL)
            general_content = general_section.group(1).strip() if general_section else recommendation
            parsed_suggestions.append({
                'id': f"general_{studentid}",
                'title': "Đề xuất cải thiện chung",
                'content': f"## Đề xuất cải thiện chung\n{general_content}",
                'type': 'info'
            })

        new_intervention = Intervention(
            studentid=studentid,
            recommendation=recommendation,
            createddate=datetime.utcnow().date(),
            isapplied=False
        )
        db.session.add(new_intervention)
        db.session.commit()

        response = {
            'studentid': studentid,
            'suggestions': parsed_suggestions,
            'interventionid': new_intervention.interventionid
        }
        logger.info(f"Hoàn thành xử lý dự đoán can thiệp trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể dự đoán can thiệp: {str(e)}")
        return jsonify({'error': f'Không thể dự đoán can thiệp: {str(e)}'}), 500

@app.route('/api/dashboard/student-errors/<string:studentid>', methods=['GET'])
def get_student_errors(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý danh sách lỗi cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own data")
                return jsonify({'error': 'Unauthorized: Students can only access their own data'}), 403
        elif role != 'admin':
            logger.error("Unauthorized: Invalid role")
            return jsonify({'error': 'Unauthorized: Invalid role'}), 403
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        warnings = Warning.query.filter_by(studentid=studentid).all()
        progress = Progress.query.filter_by(studentid=studentid).first()
        common_errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []
        
        response = {
            'studentid': studentid,
            'student_name': student.name,
            'personal_errors': [{
                'warningid': w.warningid,
                'message': w.message,
                'createddate': w.createddate.isoformat() if w.createddate else None,
                'severity': getattr(w, 'severity', 'medium')
            } for w in warnings],
            'common_errors': [{
                'errorid': e.errorid,
                'type': e.type,
                'description': e.description,
                'courseid': e.courseid
            } for e in common_errors],
            'total_personal_errors': len(warnings),
            'total_common_errors': len(common_errors)
        }
        logger.info(f"Hoàn thành xử lý danh sách lỗi trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy danh sách lỗi: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách lỗi: {str(e)}'}), 500


@app.route('/api/dashboard/class-progress/<int:courseid>', methods=['GET'])
def get_class_progress(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tiến độ lớp học cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        course = Course.query.filter_by(courseid=courseid).first()
        if not course:
            logger.warning(f"Không tìm thấy khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy khóa học'}), 404

        students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == courseid).all()
        total_students = len(students)
        if total_students == 0:
            logger.warning(f"Không tìm thấy sinh viên cho khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy sinh viên cho khóa học này'}), 404

        progress_data = Progress.query.filter_by(courseid=courseid).all()
        total_completion = sum(p.completionrate for p in progress_data) / total_students if progress_data else 0
        avg_gpa = sum(s.totalgpa for s in students) / total_students if students else 0

        active_students = sum(1 for p in progress_data if p.completionrate == 100)
        activity_rate = (active_students / total_students) * 100 if total_students > 0 else 0

        students_list = [{
            'studentid': s.studentid,
            'name': s.name,
            'totalgpa': s.totalgpa,
            'class': s.class_,
            'progress': next((p.progressrate for p in progress_data if p.studentid == s.studentid), 0),
            'status': classify_student(s.totalgpa)
        } for s in students]

        response = {
            'courseid': courseid,
            'coursename': course.coursename,
            'semester': course.semester,
            'total_students': total_students,
            'activity_rate': round(activity_rate, 2),
            'average_gpa': round(avg_gpa, 2),
            'completion_rate': round(total_completion, 2),
            'students': students_list
        }
        logger.info(f"Hoàn thành xử lý tiến độ lớp học trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tiến độ lớp học: {str(e)}")
        return jsonify({'error': f'Không thể lấy tiến độ lớp học: {str(e)}'}), 500

@app.route('/api/dashboard/chapter-details/<string:studentid>/<int:courseid>', methods=['GET'])
def get_chapter_details(studentid, courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý chi tiết chương cho studentid: {studentid}, courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        chapters = Chapter.query.filter_by(courseid=courseid).all()
        progress = Progress.query.filter_by(studentid=studentid, courseid=courseid).first()
        if not progress or not chapters:
            logger.warning(f"Không tìm thấy dữ liệu chương hoặc tiến độ cho sinh viên {studentid}, khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu chương hoặc tiến độ sinh viên'}), 404

        chapter_details = [{
            'chapterid': chapter.chapterid,
            'name': chapter.name,
            'completion_rate': chapter.completionrate,
            'average_score': chapter.averagescore,
            'estimated_time': chapter.estimatedtime
        } for chapter in chapters]

        response = {
            'studentid': studentid,
            'courseid': courseid,
            'chapters': chapter_details
        }
        logger.info(f"Hoàn thành xử lý chi tiết chương trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy chi tiết chương: {str(e)}")
        return jsonify({'error': f'Không thể lấy chi tiết chương: {str(e)}'}), 500

@app.route('/api/dashboard/common/courses/<int:courseid>', methods=['GET'])
def get_course_common_errors(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý lỗi chung cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        errors = CommonError.query.filter_by(courseid=courseid).all()
        if not errors:
            logger.warning(f"Không tìm thấy lỗi chung cho khóa học {courseid}")
            return jsonify({'error': 'Không tìm thấy lỗi chung nào cho khóa học này'}), 404

        response = [{
            'errorid': e.errorid,
            'type': e.type,
            'description': e.description,
            'occurrences': e.occurrences,
            'studentsaffected': e.studentsaffected,
            'relatedchapters': e.relatedchapters
        } for e in errors]
        logger.info(f"Hoàn thành xử lý lỗi chung trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy các lỗi chung cho khóa học: {str(e)}")
        return jsonify({'error': f'Không thể lấy các lỗi chung cho khóa học: {str(e)}'}), 500

@app.route('/api/dashboard/update-status', methods=['POST'])
def update_status():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý cập nhật trạng thái cảnh báo")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        data = request.json
        warningid = data.get('warningid')
        status = data.get('status')

        warning = Warning.query.get(warningid)
        if not warning:
            logger.warning(f"Không tìm thấy cảnh báo {warningid}")
            return jsonify({'error': 'Không tìm thấy cảnh báo'}), 404

        if status == 'contacted':
            warning.isresolved = True
            warning.resolveddate = datetime.utcnow().date()
        else:
            logger.error(f"Trạng thái không hợp lệ: {status}")
            return jsonify({'error': 'Trạng thái không hợp lệ'}), 400

        db.session.commit()
        logger.info(f"Cập nhật trạng thái cảnh báo {warningid} thành công trong {datetime.now() - start_time}")
        return jsonify({'message': 'Cập nhật trạng thái thành công', 'warningid': warningid})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Không thể cập nhật trạng thái: {str(e)}")
        return jsonify({'error': f'Không thể cập nhật trạng thái: {str(e)}'}), 500

@app.route('/api/dashboard/activity-rate/<int:courseid>', methods=['GET'])
def get_activity_rate(courseid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý tỷ lệ hoạt động cho courseid: {courseid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        total_students = Student.query.select_from(Student).join(
            Progress, Progress.studentid == Student.studentid
        ).filter(Progress.courseid == courseid).distinct().count()
        if total_students == 0:
            logger.info(f"Tỷ lệ hoạt động cho khóa học {courseid}: 0.0 trong {datetime.now() - start_time}")
            return jsonify({'activity_rate': 0.0}), 200

        active_students = Progress.query.filter(
            Progress.courseid == courseid,
            Progress.completionrate >= 80
        ).count()

        activity_rate = (active_students / total_students) * 100 if total_students > 0 else 0
        response = {'activity_rate': round(activity_rate, 2)}
        logger.info(f"Hoàn thành xử lý tỷ lệ hoạt động trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể lấy tỷ lệ hoạt động: {str(e)}")
        return jsonify({'error': f'Không thể lấy tỷ lệ hoạt động cho khóa học {courseid}: {str(e)}'}), 500

@app.route('/api/dashboard/evaluate-model', methods=['GET'])
def evaluate_model():
    start_time = datetime.now()
    logger.info("Bắt đầu xử lý đánh giá mô hình")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        _, metrics = train_and_evaluate_model()
        response = {
            'metrics': {
                'accuracy': round(metrics['accuracy'], 2),
                'precision': round(metrics['precision'], 2),
                'recall': round(metrics['recall'], 2),
                'f1_score': round(metrics['f1'], 2),
                'f1_cv': round(metrics['f1_cv'], 2)
            }
        }
        logger.info(f"Hoàn thành xử lý đánh giá mô hình trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể đánh giá mô hình: {str(e)}")
        return jsonify({'error': f'Không thể đánh giá mô hình: {str(e)}'}), 500

@app.route('/api/dashboard/evaluate-llm/<string:studentid>', methods=['GET'])
def evaluate_llm(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý đánh giá LLM cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    try:
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404

        progress = Progress.query.filter_by(studentid=studentid).first()
        bloom = BloomAssessment.query.filter_by(studentid=studentid).first()
        assignments = Assignment.query.filter_by(courseid=progress.courseid).all() if progress else []
        errors = CommonError.query.filter_by(courseid=progress.courseid).all() if progress else []

        if not progress or not bloom:
            logger.warning(f"Không tìm thấy dữ liệu tiến độ hoặc Bloom cho sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy dữ liệu tiến độ hoặc Bloom'}), 404

        def count_submissions():
            count = 0
            for assignment in assignments:
                if assignment.studentssubmitted:
                    submitted_students = assignment.studentssubmitted.split(', ')
                    if student.name in submitted_students:
                        count += 1
            return count

        num_submissions = count_submissions()
        num_errors = len(errors)

        scenarios = [
            {
                'name': 'Sinh viên nguy hiểm',
                'gpa': 1.8,
                'progressrate': 20,
                'bloomscore': 3,
                'num_submissions': 2,
                'num_errors': 5,
                'errors': ['Lỗi hàm: Truyền tham số không đúng kiểu', 'Lỗi cú pháp: Sai định dạng printf']
            },
            {
                'name': 'Sinh viên trung bình',
                'gpa': 3.0,
                'progressrate': 60,
                'bloomscore': 6,
                'num_submissions': 6,
                'num_errors': 2,
                'errors': ['Lỗi logic: Sai điều kiện if']
            },
            {
                'name': 'Sinh viên xuất sắc',
                'gpa': 3.8,
                'progressrate': 90,
                'bloomscore': 9,
                'num_submissions': 10,
                'num_errors': 0,
                'errors': []
            }
        ]

        results = []
        for scenario in scenarios:
            prompt = f"""
            Sinh viên có GPA là {scenario['gpa']}, tiến độ học tập là {scenario['progressrate']}%, điểm Bloom là {scenario['bloomscore']}, số lần nộp bài là {scenario['num_submissions']}.
            Các lỗi của sinh viên: {', '.join(scenario['errors']) if scenario['errors'] else 'Không có lỗi'}.
            Dựa trên thông tin này, hãy đưa ra các đề xuất cải thiện chi tiết, bao gồm giải thích lỗi, cách khắc phục, và ví dụ minh họa nếu có.
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp các đề xuất cải thiện học tập chi tiết và dễ hiểu."},
                    {"role": "user", "content": prompt}
                ]
            )
            recommendation = response.choices[0].message.content
            results.append({
                'scenario': scenario['name'],
                'recommendation': recommendation
            })

        warnings = Warning.query.filter(
            Warning.studentid == studentid,
            Warning.message.ilike('%Lỗi%')
        ).all()
        error_messages = [w.message for w in warnings]
        common_error_types = [e.type for e in errors]
        prompt = f"""
        Sinh viên có GPA là {student.totalgpa}, tiến độ học tập là {progress.progressrate}%, điểm Bloom là {bloom.score}, số lần nộp bài là {num_submissions}.
        Các lỗi của sinh viên: {', '.join(error_messages) if error_messages else 'Không có lỗi cụ thể'}.
        Các lỗi chung trong khóa học: {', '.join(common_error_types) if common_error_types else 'Không có lỗi chung'}.
        Dựa trên thông tin này, hãy đưa ra các đề xuất cải thiện chi tiết, bao gồm giải thích lỗi, cách khắc phục, và ví dụ minh họa nếu có.
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp các đề xuất cải thiện học tập chi tiết và dễ hiểu."},
                {"role": "user", "content": prompt}
            ]
        )
        actual_recommendation = response.choices[0].message.content
        results.append({
            'scenario': 'Thực tế',
            'recommendation': actual_recommendation
        })

        response = {
            'studentid': studentid,
            'evaluation_results': results
        }
        logger.info(f"Hoàn thành xử lý đánh giá LLM trong {datetime.now() - start_time}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Không thể đánh giá LLM: {str(e)}")
        return jsonify({'error': f'Không thể đánh giá LLM: {str(e)}'}), 500
    
@app.route('/api/dashboard/extend-deadline/<int:assignmentid>', methods=['POST'])
@require_auth
def extend_deadline(assignmentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu xử lý gia hạn deadline cho assignmentid: {assignmentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    if user.get('role') != 'admin':
        logger.error("Unauthorized: Only admins can extend deadlines")
        return jsonify({'error': 'Unauthorized: Only admins can extend deadlines'}), 403
    
    try:
        data = request.json
        new_deadline = data.get('new_deadline')  # Định dạng: YYYY-MM-DD
        if not new_deadline:
            logger.error("Missing new_deadline in request body")
            return jsonify({'error': 'Missing new_deadline in request body'}), 400

        # Chuyển đổi new_deadline thành đối tượng datetime.date
        try:
            new_deadline_date = datetime.strptime(new_deadline, '%Y-%m-%d').date()
        except ValueError:
            logger.error("Invalid date format for new_deadline. Use YYYY-MM-DD")
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        assignment = Assignment.query.get(assignmentid)
        if not assignment:
            logger.warning(f"Không tìm thấy bài tập {assignmentid}")
            return jsonify({'error': 'Không tìm thấy bài tập'}), 404

        # Kiểm tra nếu deadline mới hợp lệ (ví dụ: không sớm hơn ngày hiện tại)
        if new_deadline_date < datetime.utcnow().date():
            logger.error("New deadline cannot be in the past")
            return jsonify({'error': 'New deadline cannot be in the past'}), 400

        # Cập nhật deadline
        assignment.deadline = new_deadline_date
        db.session.commit()
        
        logger.info(f"Gia hạn deadline cho bài tập {assignmentid} thành công trong {datetime.now() - start_time}")
        return jsonify({
            'message': 'Gia hạn deadline thành công',
            'assignmentid': assignmentid,
            'new_deadline': assignment.deadline.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Không thể gia hạn deadline: {str(e)}")
        return jsonify({'error': f'Không thể gia hạn deadline: {str(e)}'}), 500    
    
@app.route('/api/dashboard/student-notifications/<string:studentid>', methods=['GET'])
@require_auth
def get_student_notifications(studentid):
    start_time = datetime.now()
    logger.info(f"Bắt đầu lấy danh sách thông báo cho studentid: {studentid}")
    user = get_current_user()
    if not user:
        logger.error("Unauthorized: Missing user data")
        return jsonify({'error': 'Unauthorized: Missing user data'}), 401
    
    role = user.get('role')
    user_studentid = user.get('studentId')
    
    try:
        # Kiểm tra studentid hợp lệ
        if not studentid or not isinstance(studentid, str):
            logger.error("ID sinh viên không hợp lệ")
            return jsonify({'error': 'ID sinh viên không hợp lệ'}), 400
        
        # Kiểm tra quyền truy cập
        if role == 'user':
            if not user_studentid:
                logger.error("Unauthorized: Missing student ID")
                return jsonify({'error': 'Unauthorized: Missing student ID'}), 401
            if user_studentid != studentid:
                logger.error("Unauthorized: Students can only access their own notifications")
                return jsonify({'error': 'Unauthorized: Students can only access their own notifications'}), 403
        
        # Kiểm tra sinh viên tồn tại
        student = Student.query.get(studentid)
        if not student:
            logger.warning(f"Không tìm thấy sinh viên {studentid}")
            return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
        
        # Lấy danh sách thông báo của sinh viên
        notifications = Notification.query.filter_by(studentid=studentid).all()
        
        # Nếu không có thông báo
        if not notifications:
            logger.info(f"Không tìm thấy thông báo cho sinh viên {studentid}")
            return jsonify({'message': 'Không có thông báo nào cho sinh viên này', 'notifications': []}), 200
        
        # Tạo phản hồi
        response = [{
            'notificationid': n.notificationid,
            'studentid': n.studentid,
            'message': n.message,
            'createddate': n.createddate.isoformat() if n.createddate else None,
            'isread': n.isread
        } for n in notifications]
        
        logger.info(f"Hoàn thành lấy danh sách thông báo trong {datetime.now() - start_time}")
        return jsonify({'notifications': response}), 200
    
    except Exception as e:
        logger.error(f"Không thể lấy danh sách thông báo: {str(e)}")
        return jsonify({'error': f'Không thể lấy danh sách thông báo: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)
