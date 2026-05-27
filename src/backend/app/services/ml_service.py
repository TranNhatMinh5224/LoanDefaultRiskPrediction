import pandas as pd
import joblib
import os

class MLService:
    def __init__(self):
        # Môi trường Docker sẽ chạy tại /app, thư mục model nằm tại /app/model
        # Chỉnh sửa lại đường dẫn cẩn thận để tương thích cả chạy bằng Docker và chạy Local
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = os.path.join(base_dir, 'model', 'lgbm_model_v1.joblib')
        self.imputer_path = os.path.join(base_dir, 'model', 'imputer_v1.joblib')
        
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
        
        # Tự động đồng bộ số lượng cột (Nếu Frontend gửi thiếu)
        # 1. Lấy danh sách 245 tên cột chuẩn mà Imputer/Model mong đợi
        expected_cols = getattr(self.imputer, 'feature_names_in_', getattr(self.model, 'feature_name_', None))
        
        if expected_cols is not None:
            # 2. Cột nào client gửi thiếu -> tự động thêm vào và gán giá trị NaN (Not a Number)
            df = df.reindex(columns=expected_cols, fill_value=None)
        
        # 3. Imputer sẽ tự động lấp đầy các ô NaN này bằng giá trị Trung Vị (Median) đã học lúc train
        df_imputed = pd.DataFrame(self.imputer.transform(df), columns=df.columns)
        
        risk_prob = float(self.model.predict_proba(df_imputed)[0][1])
        decision = "REJECT" if risk_prob > 0.3 else "APPROVE"
        
        return risk_prob, decision

    def predict_batch_risk(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")
            
        expected_cols = getattr(self.imputer, 'feature_names_in_', getattr(self.model, 'feature_name_', None))
        if expected_cols is not None:
            df_aligned = df.reindex(columns=expected_cols, fill_value=None)
        else:
            df_aligned = df
            
        df_imputed = pd.DataFrame(self.imputer.transform(df_aligned), columns=df_aligned.columns)
        
        # Trích xuất xác suất vỡ nợ (Class 1)
        risk_probs = self.model.predict_proba(df_imputed)[:, 1]
        
        # Clone DF gốc để đính kèm kết quả trả về
        df_result = df.copy()
        df_result['RISK_SCORE'] = risk_probs
        df_result['DECISION'] = ['REJECT' if p > 0.3 else 'APPROVE' for p in risk_probs]
        
        return df_result

# Áp dụng Singleton Pattern (Chỉ khởi tạo class 1 lần duy nhất để tiết kiệm RAM)
ml_service_instance = MLService()
