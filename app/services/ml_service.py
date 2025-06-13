"""
Machine Learning Service - Giống hệt logic trong file app.py gốc
"""
import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class MLService:
    """Service xử lý Machine Learning"""
    
    def __init__(self):
        self.model = None
        self.model_path = 'rf_model.pkl'  # Giống file gốc
        self.load_or_train_model()
    
    def encode_priority(self, priority):
        """Mã hóa priority"""
        mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        return mapping.get(priority, 1)

    def encode_severity(self, severity):
        """Mã hóa severity"""
        mapping = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        return mapping.get(severity, 1)

    def encode_bloomlevel(self, bloomlevel):
        """Mã hóa bloom level"""
        mapping = {'Nhớ': 0, 'Hiểu': 1, 'Áp dụng': 2, 'Phân tích': 3, 'Đánh giá': 4, 'Sáng tạo': 5}
        return mapping.get(bloomlevel, 0)
    
    def load_training_data(self):
        """
        Tạo dữ liệu huấn luyện với 250 bản ghi - CẬP NHẬT 7 ĐẶC TRƯNG
        
        Returns:
            tuple: (X, y) - Features và labels
        """
        np.random.seed(42)  # Đảm bảo tính tái lập
        n_samples = 250
        
        # Tạo dữ liệu giả lập
        gpa = np.random.uniform(1.5, 4.0, n_samples)
        progressrate = np.random.uniform(10, 100, n_samples)
        bloomscore = np.random.uniform(2, 10, n_samples)
        count_errors = np.random.randint(0, 10, n_samples)
        priority = np.random.choice(['LOW', 'MEDIUM', 'HIGH'], n_samples)
        severity = np.random.choice(['LOW', 'MEDIUM', 'HIGH'], n_samples)
        bloomlevel = np.random.choice(['Nhớ', 'Hiểu', 'Áp dụng', 'Phân tích', 'Đánh giá', 'Sáng tạo'], n_samples)
        
        # Mã hóa categorical features
        priority_encoded = [self.encode_priority(p) for p in priority]
        severity_encoded = [self.encode_severity(s) for s in severity]
        bloomlevel_encoded = [self.encode_bloomlevel(b) for b in bloomlevel]
        
        # Tạo nhãn risk với logic mới
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
    
    def train_and_evaluate_model(self):
        """
        Huấn luyện và đánh giá mô hình - GIỐNG HỆT FILE GỐC
        
        Returns:
            tuple: (model, metrics) - Mô hình đã huấn luyện và metrics
        """
        X, y = self.load_training_data()
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
    
    def load_or_train_model(self):
        """Tải mô hình từ file hoặc huấn luyện mới - GIỐNG HỆT FILE GỐC"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model, _ = self.train_and_evaluate_model()
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
    
    def predict_risk(self, gpa, progressrate, bloomscore, count_errors, priority, severity, bloomlevel):
        """
        Dự đoán nguy cơ học vụ với 7 đặc trưng
        
        Args:
            gpa (float): Điểm GPA
            progressrate (float): Tỷ lệ tiến độ
            bloomscore (float): Điểm Bloom
            count_errors (int): Số lỗi
            priority (float): Mức độ ưu tiên (đã mã hóa)
            severity (float): Mức độ nghiêm trọng (đã mã hóa)
            bloomlevel (int): Mức độ Bloom (đã mã hóa)
            
        Returns:
            int: 0 (an toàn) hoặc 1 (nguy hiểm)
        """
        if not self.model:
            self.load_or_train_model()
        
        input_data = np.array([[gpa, progressrate, bloomscore, count_errors, priority, severity, bloomlevel]])
        return self.model.predict(input_data)[0]
    
    def get_model_metrics(self):
        """
        Lấy metrics của mô hình
        
        Returns:
            dict: Metrics của mô hình
        """
        _, metrics = self.train_and_evaluate_model()
        return {
            'accuracy': round(metrics['accuracy'], 2),
            'precision': round(metrics['precision'], 2),
            'recall': round(metrics['recall'], 2),
            'f1_score': round(metrics['f1'], 2),
            'f1_cv': round(metrics['f1_cv'], 2)
        }