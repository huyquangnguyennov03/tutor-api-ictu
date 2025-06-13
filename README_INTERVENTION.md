# Tài liệu hướng dẫn: Endpoint Predict Intervention

## Tổng quan

Tài liệu này mô tả cách tách endpoint `/api/dashboard/predict-intervention` từ file `app.py` gốc thành các module riêng biệt để sử dụng trong `app_new.py`.

## Các file đã tạo/chỉnh sửa

### 1. app/services/intervention_service.py (Mới)

- Tạo service mới để xử lý logic can thiệp và đề xuất
- Sử dụng LLMService để tạo đề xuất từ OpenAI
- Tách logic xử lý dữ liệu và phân tích kết quả

### 2. app/routes/intervention.py (Mới)

- Tạo blueprint mới cho endpoint can thiệp
- Định nghĩa route `/api/dashboard/predict-intervention/<string:studentid>`
- Xử lý xác thực và kiểm tra quyền truy cập
- Sử dụng InterventionService để xử lý logic

### 3. app/routes/**init**.py (Cập nhật)

- Thêm import cho intervention_bp
- Đăng ký blueprint mới với Flask app

### 4. app/routes/dashboard_complete.py (Cập nhật)

- Thêm import cho InterventionService
- Cập nhật endpoint predict_intervention để sử dụng service

## Cách hoạt động

1. Khi có request đến `/api/dashboard/predict-intervention/<string:studentid>`:

   - Route trong intervention_bp xử lý request
   - Kiểm tra xác thực và quyền truy cập
   - Truy vấn dữ liệu sinh viên, tiến độ, bloom, assignments, errors, warnings

2. InterventionService xử lý logic:

   - Chuẩn bị dữ liệu cho LLM
   - Gọi LLMService để tạo đề xuất
   - Phân tích kết quả và lưu vào database
   - Trả về kết quả đã định dạng

3. LLMService xử lý tương tác với OpenAI:
   - Tạo prompt từ dữ liệu sinh viên
   - Gọi OpenAI API để tạo đề xuất
   - Phân tích kết quả thành các suggestion

## Lưu ý

- Endpoint mới giữ nguyên URL `/api/dashboard/predict-intervention/<string:studentid>` để tương thích với frontend
- Logic xử lý giống hệt file app.py gốc, chỉ tách thành các module riêng biệt
- Sử dụng các service để tái sử dụng code và dễ bảo trì

## Cách sử dụng trong app_new.py

File app_new.py đã được cấu hình để sử dụng các blueprint từ app/routes/**init**.py, nên không cần thay đổi gì thêm. Endpoint mới sẽ tự động được đăng ký khi app khởi động.# Tài liệu hướng dẫn: Endpoint Predict Intervention

## Tổng quan

Tài liệu này mô tả cách tách endpoint `/api/dashboard/predict-intervention` từ file `app.py` gốc thành các module riêng biệt để sử dụng trong `app_new.py`.

## Các file đã tạo/chỉnh sửa

### 1. app/services/intervention_service.py (Mới)

- Tạo service mới để xử lý logic can thiệp và đề xuất
- Sử dụng LLMService để tạo đề xuất từ OpenAI
- Tách logic xử lý dữ liệu và phân tích kết quả

### 2. app/routes/intervention.py (Mới)

- Tạo blueprint mới cho endpoint can thiệp
- Định nghĩa route `/api/dashboard/predict-intervention/<string:studentid>`
- Xử lý xác thực và kiểm tra quyền truy cập
- Sử dụng InterventionService để xử lý logic

### 3. app/routes/**init**.py (Cập nhật)

- Thêm import cho intervention_bp
- Đăng ký blueprint mới với Flask app

### 4. app/routes/dashboard_complete.py (Cập nhật)

- Thêm import cho InterventionService
- Cập nhật endpoint predict_intervention để sử dụng service

## Cách hoạt động

1. Khi có request đến `/api/dashboard/predict-intervention/<string:studentid>`:

   - Route trong intervention_bp xử lý request
   - Kiểm tra xác thực và quyền truy cập
   - Truy vấn dữ liệu sinh viên, tiến độ, bloom, assignments, errors, warnings

2. InterventionService xử lý logic:

   - Chuẩn bị dữ liệu cho LLM
   - Gọi LLMService để tạo đề xuất
   - Phân tích kết quả và lưu vào database
   - Trả về kết quả đã định dạng

3. LLMService xử lý tương tác với OpenAI:
   - Tạo prompt từ dữ liệu sinh viên
   - Gọi OpenAI API để tạo đề xuất
   - Phân tích kết quả thành các suggestion

## Lưu ý

- Endpoint mới giữ nguyên URL `/api/dashboard/predict-intervention/<string:studentid>` để tương thích với frontend
- Logic xử lý giống hệt file app.py gốc, chỉ tách thành các module riêng biệt
- Sử dụng các service để tái sử dụng code và dễ bảo trì

## Cách sử dụng trong app_new.py

File app_new.py đã được cấu hình để sử dụng các blueprint từ app/routes/**init**.py, nên không cần thay đổi gì thêm. Endpoint mới sẽ tự động được đăng ký khi app khởi động.
