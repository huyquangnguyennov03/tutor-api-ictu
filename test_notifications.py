"""
Test script cho notification endpoints
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Test data
TEST_STUDENT_ID = "SV001"
TEST_WARNING_DATA = {
    "warningtype": "ACADEMIC",
    "message": "GPA thấp, cần cải thiện kết quả học tập",
    "severity": "HIGH",
    "priority": "URGENT"
}

# Headers (sẽ cần thêm token authentication trong thực tế)
HEADERS = {
    "Content-Type": "application/json"
}

def test_create_warning():
    """Test tạo thông báo dựa trên ML prediction"""
    print("=== Test Create Warning (ML Prediction) ===")
    url = f"{BASE_URL}/api/dashboard/create-warning/{TEST_STUDENT_ID}"
    
    response = requests.post(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_create_manual_warning():
    """Test tạo cảnh báo và thông báo thủ công"""
    print("=== Test Create Manual Warning ===")
    url = f"{BASE_URL}/api/dashboard/create-manual-warning/{TEST_STUDENT_ID}"
    
    response = requests.post(url, 
                           headers=HEADERS, 
                           data=json.dumps(TEST_WARNING_DATA))
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_notifications():
    """Test lấy danh sách thông báo"""
    print("=== Test Get Notifications ===")
    url = f"{BASE_URL}/api/dashboard/student-notifications/{TEST_STUDENT_ID}"
    
    response = requests.get(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_unread_count():
    """Test đếm thông báo chưa đọc"""
    print("=== Test Get Unread Count ===")
    url = f"{BASE_URL}/api/dashboard/notifications/unread-count/{TEST_STUDENT_ID}"
    
    response = requests.get(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_notification_stats():
    """Test lấy thống kê thông báo"""
    print("=== Test Get Notification Stats ===")
    url = f"{BASE_URL}/api/dashboard/notifications/stats/{TEST_STUDENT_ID}"
    
    response = requests.get(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_mark_notification_read():
    """Test đánh dấu thông báo đã đọc"""
    print("=== Test Mark Notification Read ===")
    # Giả sử notification ID = 1
    notification_id = 1
    url = f"{BASE_URL}/api/dashboard/notifications/{notification_id}/mark-read"
    
    response = requests.put(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_mark_all_read():
    """Test đánh dấu tất cả thông báo đã đọc"""
    print("=== Test Mark All Notifications Read ===")
    url = f"{BASE_URL}/api/dashboard/notifications/mark-all-read/{TEST_STUDENT_ID}"
    
    response = requests.put(url, headers=HEADERS)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def run_all_tests():
    """Chạy tất cả test"""
    print("Starting Notification API Tests...")
    print("=" * 50)
    
    test_create_warning()
    test_create_manual_warning()
    test_get_notifications()
    test_get_unread_count()
    test_get_notification_stats()
    test_mark_notification_read()
    test_mark_all_read()
    
    print("=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("Error: Không thể kết nối đến server. Hãy đảm bảo server đang chạy trên port 8000.")
    except Exception as e:
        print(f"Error: {str(e)}")