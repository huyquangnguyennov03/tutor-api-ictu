# Notification API Documentation

## Tổng quan
Module Notification cung cấp các API để quản lý thông báo trong hệ thống tutor AI. Module này được tách biệt từ app.py và tích hợp vào app_new.py.

## Cấu trúc Files

```
app/
├── models/
│   └── notification.py          # Model Notification
├── routes/
│   └── notification.py          # Routes cho notification endpoints
└── services/
    └── notification_service.py  # Service xử lý logic nghiệp vụ
```

## Model: Notification

```python
class Notification(db.Model):
    __tablename__ = 'notification'
    
    notificationid = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Text, db.ForeignKey('student.studentid'), index=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    createddate = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    isread = db.Column(db.Boolean, nullable=False, default=False)
```

## API Endpoints

### 1. Tạo thông báo dựa trên ML prediction
- **URL**: `POST /api/dashboard/create-warning/<studentid>`
- **Quyền**: User (cho chính mình), Admin (cho tất cả)
- **Body**: Không cần body
- **Response** (khi có rủi ro):
```json
{
    "message": "Thông báo đã được tạo cho sinh viên",
    "notificationid": 456,
    "risk_prediction": 1,
    "gpa": 1.8,
    "progress_rate": 45.5
}
```
- **Response** (khi an toàn):
```json
{
    "message": "Không tạo thông báo, sinh viên an toàn",
    "risk_prediction": 0,
    "gpa": 3.2,
    "progress_rate": 85.0
}
```

### 1.1. Tạo cảnh báo và thông báo thủ công
- **URL**: `POST /api/dashboard/create-manual-warning/<studentid>`
- **Quyền**: Admin only
- **Body**:
```json
{
    "warningtype": "ACADEMIC",
    "message": "GPA thấp, cần cải thiện kết quả học tập",
    "severity": "HIGH",
    "priority": "URGENT"
}
```
- **Response**:
```json
{
    "warningid": 123,
    "notificationid": 456,
    "message": "Tạo cảnh báo và thông báo thủ công thành công"
}
```

### 2. Lấy danh sách thông báo của sinh viên
- **URL**: `GET /api/dashboard/student-notifications/<studentid>`
- **Quyền**: User (chỉ thông báo của mình), Admin (tất cả)
- **Response**:
```json
[
    {
        "notificationid": 1,
        "studentid": "SV001",
        "message": "Cảnh báo HIGH: GPA thấp, cần cải thiện kết quả học tập",
        "createddate": "2024-01-15",
        "isread": false
    }
]
```

### 3. Đánh dấu thông báo đã đọc
- **URL**: `PUT /api/dashboard/notifications/<notification_id>/mark-read`
- **Quyền**: User (thông báo của mình), Admin (tất cả)
- **Response**:
```json
{
    "notificationid": 1,
    "message": "Đánh dấu thông báo đã đọc thành công"
}
```

### 4. Đếm số thông báo chưa đọc
- **URL**: `GET /api/dashboard/notifications/unread-count/<studentid>`
- **Quyền**: User (của mình), Admin (tất cả)
- **Response**:
```json
{
    "studentid": "SV001",
    "unread_count": 5
}
```

### 5. Đánh dấu tất cả thông báo đã đọc
- **URL**: `PUT /api/dashboard/notifications/mark-all-read/<studentid>`
- **Quyền**: User (của mình), Admin (tất cả)
- **Response**:
```json
{
    "studentid": "SV001",
    "marked_count": 5,
    "message": "Đánh dấu 5 thông báo đã đọc thành công"
}
```

### 6. Lấy thống kê thông báo
- **URL**: `GET /api/dashboard/notifications/stats/<studentid>`
- **Quyền**: User (của mình), Admin (tất cả)
- **Response**:
```json
{
    "studentid": "SV001",
    "total": 10,
    "read": 3,
    "unread": 7,
    "unread_percentage": 70.0
}
```

### 7. Xóa thông báo
- **URL**: `DELETE /api/dashboard/notifications/<notification_id>`
- **Quyền**: Admin only
- **Response**:
```json
{
    "notificationid": 1,
    "message": "Xóa thông báo thành công"
}
```

## Service Layer

### NotificationService
Service này cung cấp các phương thức:

- `create_notification(studentid, message)`: Tạo thông báo đơn
- `create_warning_with_notification(studentid, warning_data)`: Tạo cảnh báo + thông báo
- `create_ml_prediction_notification(studentid)`: Tạo thông báo dựa trên ML prediction
- `get_student_notifications(studentid, limit, only_unread)`: Lấy danh sách thông báo
- `mark_notification_read(notification_id)`: Đánh dấu thông báo đã đọc
- `mark_all_notifications_read(studentid)`: Đánh dấu tất cả đã đọc
- `get_unread_count(studentid)`: Đếm thông báo chưa đọc
- `delete_notification(notification_id)`: Xóa thông báo
- `get_notification_stats(studentid)`: Lấy thống kê thông báo

## Authentication & Authorization

### Roles:
- **User**: Chỉ truy cập thông báo của chính mình
- **Admin**: Truy cập tất cả thông báo của sinh viên

### Headers yêu cầu:
```
Authorization: Bearer <token>
Content-Type: application/json
```

## Error Handling

### Common Error Codes:
- `400`: Bad Request - Dữ liệu không hợp lệ
- `401`: Unauthorized - Chưa đăng nhập
- `403`: Forbidden - Không có quyền truy cập
- `404`: Not Found - Không tìm thấy tài nguyên
- `500`: Internal Server Error - Lỗi server

### Error Response Format:
```json
{
    "error": "Mô tả lỗi chi tiết"
}
```

## Testing

Sử dụng file `test_notifications.py` để test các endpoint:

```bash
python test_notifications.py
```

## Database Migration

Khi chạy app_new.py lần đầu, bảng notification sẽ được tạo tự động:

```python
with app.app_context():
    db.create_all()
```

## Integration với Frontend

### React Component Example:
```jsx
// Lấy thông báo
const fetchNotifications = async (studentId) => {
    const response = await fetch(`/api/dashboard/student-notifications/${studentId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
};

// Tạo thông báo dựa trên ML
const createMLNotification = async (studentId) => {
    const response = await fetch(`/api/dashboard/create-warning/${studentId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
};

// Tạo cảnh báo thủ công
const createManualWarning = async (studentId, warningData) => {
    const response = await fetch(`/api/dashboard/create-manual-warning/${studentId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(warningData)
    });
    return response.json();
};

// Đánh dấu đã đọc
const markAsRead = async (notificationId) => {
    await fetch(`/api/dashboard/notifications/${notificationId}/mark-read`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
};
```

## Performance Considerations

1. **Indexing**: Đã tạo index trên `studentid` để tối ưu truy vấn
2. **Pagination**: Có thể thêm limit trong service để phân trang
3. **Caching**: Có thể cache số lượng thông báo chưa đọc
4. **Real-time**: Có thể tích hợp WebSocket cho thông báo real-time

## Security

1. **Input Validation**: Tất cả input đều được validate
2. **SQL Injection**: Sử dụng SQLAlchemy ORM để tránh SQL injection  
3. **Authorization**: Kiểm tra quyền truy cập ở mọi endpoint
4. **Logging**: Log tất cả hoạt động quan trọng

## Future Enhancements

1. **Push Notifications**: Tích hợp với Firebase/OneSignal
2. **Email Notifications**: Gửi email cho thông báo quan trọng
3. **Notification Templates**: Tạo template cho các loại thông báo
4. **Bulk Operations**: Tạo thông báo cho nhiều sinh viên cùng lúc
5. **Notification Categories**: Phân loại thông báo theo chủ đề