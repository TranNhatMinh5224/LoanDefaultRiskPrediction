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

    def _create_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tái tạo chính xác các đặc trưng (features) đã Feature Engineering trong Notebook"""
        df_copy = df.copy()
        
        # 1. Tạo biến One-Hot Encoding cho Categorical từ Frontend
        if 'CODE_GENDER' in df_copy:
            df_copy['CODE_GENDER_F'] = df_copy['CODE_GENDER'].apply(lambda x: 1.0 if x == 'F' else 0.0)
            df_copy['CODE_GENDER_M'] = df_copy['CODE_GENDER'].apply(lambda x: 1.0 if x == 'M' else 0.0)
            df_copy.drop(columns=['CODE_GENDER'], inplace=True)
            
        if 'FLAG_OWN_CAR' in df_copy:
            df_copy['FLAG_OWN_CAR_Y'] = df_copy['FLAG_OWN_CAR'].apply(lambda x: 1.0 if x == 'Y' else 0.0)
            df_copy['FLAG_OWN_CAR_N'] = df_copy['FLAG_OWN_CAR'].apply(lambda x: 1.0 if x == 'N' else 0.0)
            df_copy.drop(columns=['FLAG_OWN_CAR'], inplace=True)
            
        if 'NAME_EDUCATION_TYPE' in df_copy:
            val = df_copy['NAME_EDUCATION_TYPE'].iloc[0]
            if val == 'Higher education':
                df_copy['NAME_EDUCATION_TYPE_Higher education'] = 1.0
            elif val == 'Secondary / secondary special':
                df_copy['NAME_EDUCATION_TYPE_Secondary / secondary special'] = 1.0
            elif val == 'Lower secondary':
                df_copy['NAME_EDUCATION_TYPE_Lower secondary'] = 1.0
            df_copy.drop(columns=['NAME_EDUCATION_TYPE'], inplace=True)

        # 2. Xử lý các biến tài chính phái sinh
        if 'DAYS_BIRTH' in df_copy:
            df_copy['AGE'] = df_copy['DAYS_BIRTH'] / -365
        if 'AMT_CREDIT' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
            df_copy['CREDIT_INCOME_PERCENT'] = df_copy['AMT_CREDIT'] / df_copy['AMT_INCOME_TOTAL']
        if 'AMT_ANNUITY' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
            df_copy['ANNUITY_INCOME_PERCENT'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_INCOME_TOTAL']
        if 'AMT_ANNUITY' in df_copy and 'AMT_CREDIT' in df_copy:
            df_copy['CREDIT_TERM'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_CREDIT']
        if 'DAYS_EMPLOYED' in df_copy and 'DAYS_BIRTH' in df_copy:
            df_copy['DAYS_EMPLOYED_PERCENT'] = df_copy['DAYS_EMPLOYED'] / df_copy['DAYS_BIRTH']
        return df_copy

    def predict_default_risk(self, features: dict) -> tuple[float, str]:
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")
            
        df = pd.DataFrame([features])
        
        # 1. Feature Engineering (Bắt buộc phải làm giống lúc Train Model)
        df = self._create_domain_features(df)
        
        # 2. Lấy danh sách 245 tên cột chuẩn mà Imputer/Model mong đợi
        expected_cols = getattr(self.imputer, 'feature_names_in_', getattr(self.model, 'feature_name_', None))
        
        if expected_cols is not None:
            # 3. Cột nào client gửi thiếu -> tự động thêm vào và gán giá trị NaN (Not a Number)
            df = df.reindex(columns=expected_cols, fill_value=None)
        
        # 4. Imputer sẽ tự động lấp đầy các ô NaN này bằng giá trị Trung Vị (Median) đã học lúc train
        df_imputed = pd.DataFrame(self.imputer.transform(df), columns=df.columns)
        
        risk_prob = float(self.model.predict_proba(df_imputed)[0][1])
        decision = "REJECT" if risk_prob > 0.3 else "APPROVE"
        
        return risk_prob, decision

    def predict_batch_risk(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")
            
        # 1. Feature Engineering (áp dụng cho tập dữ liệu lớn)
        df_engineered = self._create_domain_features(df)
            
        expected_cols = getattr(self.imputer, 'feature_names_in_', getattr(self.model, 'feature_name_', None))
        if expected_cols is not None:
            df_aligned = df_engineered.reindex(columns=expected_cols, fill_value=None)
        else:
            df_aligned = df_engineered
            
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
