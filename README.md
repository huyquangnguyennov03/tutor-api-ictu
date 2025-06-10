# Tutor API ICTU - Refactored

## 📋 Tổng quan

Dự án API hỗ trợ giáo dục thông minh đã được chia tách từ file `app.py` monolithic (1436 dòng) thành cấu trúc modular để dễ bảo trì và mở rộng.

## 🏗️ Cấu trúc dự án

```
tutor-api-ictu/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── progress.py
│   │   ├── warning.py
│   │   ├── intervention.py
│   │   ├── course_history.py
│   │   ├── bloom_assessment.py
│   │   ├── assignment.py
│   │   ├── chapter.py
│   │   ├── common_error.py
│   │   └── teacher.py
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── dashboard.py         # Dashboard endpoints
│   │   ├── student.py           # Student endpoints
│   │   ├── course.py            # Course endpoints
│   │   └── analytics.py         # Analytics endpoints
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── ml_service.py        # Machine Learning
│   │   ├── llm_service.py       # OpenAI integration
│   │   └── student_service.py   # Student business logic
│   └── utils/                   # Helper functions
│       ├── __init__.py
│       └── helpers.py
├── config.py                    # Configuration
├── app_new.py                   # Main application (rút gọn)
├── app.py                       # File gốc (backup)
├── requirements.txt             # Dependencies
└── README.md                    # Documentation
```

## 🚀 Cài đặt và chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
```

### 3. Chạy ứng dụng

```bash
# Sử dụng file mới (khuyến nghị)
python app_new.py

# Hoặc sử dụng file cũ (backup)
python app.py
```

## 📊 API Endpoints

### Dashboard Routes (`/api/dashboard/`)

- `GET /students` - Danh sách sinh viên
- `GET /courses` - Danh sách khóa học
- `GET /progress` - Toàn bộ tiến độ
- `GET /students/excellent` - Sinh viên xuất sắc
- `GET /students/needs-support` - Sinh viên cần hỗ trợ
- `GET /warnings` - Danh sách cảnh báo
- `GET /assignments` - Danh sách bài tập
- `GET /chapters` - Danh sách chương
- `GET /common-errors` - Lỗi thường gặp
- `POST /update-status` - Cập nhật trạng thái cảnh báo

### Student Routes (`/api/student/`)

- `GET /progress/<studentid>` - Tiến độ sinh viên
- `GET /report/<studentid>` - Báo cáo chi tiết
- `GET /predict-intervention/<studentid>` - Dự đoán can thiệp
- `GET /errors/<studentid>` - Danh sách lỗi
- `POST /create-warning/<studentid>` - Tạo cảnh báo
- `GET /learning-path/<studentid>` - Lộ trình học tập

### Course Routes (`/api/course/`)

- `GET /assignment-status/<assignmentid>` - Trạng thái bài tập
- `GET /class-progress/<courseid>` - Tiến độ lớp học
- `GET /chapter-details/<studentid>/<courseid>` - Chi tiết chương
- `GET /common-errors/<courseid>` - Lỗi chung khóa học
- `GET /activity-rate/<courseid>` - Tỷ lệ hoạt động

### Analytics Routes (`/api/analytics/`)

- `GET /evaluate-model` - Đánh giá mô hình ML
- `GET /evaluate-llm/<studentid>` - Đánh giá LLM

## 🔧 Các thay đổi chính

### 1. **Chia tách Models**

- Mỗi model được tách thành file riêng
- Thêm phương thức `to_dict()` cho serialization
- Import tập trung trong `models/__init__.py`

### 2. **Chia tách Routes**

- Routes được nhóm theo chức năng
- Sử dụng Blueprint pattern
- Tách biệt logic nghiệp vụ

### 3. **Tạo Services Layer**

- `MLService`: Xử lý Machine Learning
- `LLMService`: Tích hợp OpenAI
- `StudentService`: Logic nghiệp vụ sinh viên

### 4. **Configuration Management**

- Cấu hình tập trung trong `config.py`
- Hỗ trợ nhiều môi trường (dev, prod)
- Sử dụng environment variables

### 5. **Application Factory**

- Pattern factory cho Flask app
- Dễ dàng testing và deployment
- Quản lý extensions tốt hơn

## 🎯 Lợi ích của việc refactor

1. **Maintainability**: Dễ bảo trì và debug
2. **Scalability**: Dễ mở rộng tính năng mới
3. **Testability**: Dễ viết unit tests
4. **Readability**: Code rõ ràng, dễ hiểu
5. **Reusability**: Tái sử dụng components
6. **Team Collaboration**: Nhiều người có thể làm việc song song

## 📝 Migration Guide

Để chuyển từ file cũ sang cấu trúc mới:

1. **Backup file cũ**: `app.py` đã được giữ lại
2. **Sử dụng file mới**: Chạy `app_new.py`
3. **Kiểm tra endpoints**: Tất cả endpoints giữ nguyên URL
4. **Cập nhật imports**: Nếu có code khác import từ `app.py`

## 🔍 Testing

```bash
# Test endpoints cơ bản
curl http://localhost:8000/api/dashboard/students
curl http://localhost:8000/api/student/progress/SV001
curl http://localhost:8000/api/course/class-progress/1
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License
