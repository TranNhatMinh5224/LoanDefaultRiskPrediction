import pandas as pd
import joblib
import os

class MLService:
    def __init__(self):
        # Môi trường Docker sẽ chạy tại /app, thư mục models nằm tại /app/models
        # Chỉnh sửa lại đường dẫn cẩn thận để tương thích cả chạy bằng Docker và chạy Local
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = os.path.join(base_dir, 'models', 'lgbm_model_v3.joblib')
        self.imputer_path = os.path.join(base_dir, 'models', 'imputer_v3.joblib')
        
        try:
            self.model = joblib.load(self.model_path)
            self.imputer = joblib.load(self.imputer_path)
            print("✅ Đã load Tầng Dịch Vụ AI (ML Service) thành công!")
        except Exception as e:
            print(f"❌ Lỗi: Không thể tải mô hình từ {self.model_path}")
            self.model = None
            self.imputer = None

    def predict_default_risk(self, features: dict) -> tuple[float, str]:
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")
            
        df = pd.DataFrame([features])
        df_imputed = pd.DataFrame(self.imputer.transform(df), columns=df.columns)
        
        risk_prob = float(self.model.predict_proba(df_imputed)[0][1])
        decision = "REJECT" if risk_prob > 0.3 else "APPROVE"
        
        return risk_prob, decision

# Áp dụng Singleton Pattern (Chỉ khởi tạo class 1 lần duy nhất để tiết kiệm RAM)
ml_service_instance = MLService()
