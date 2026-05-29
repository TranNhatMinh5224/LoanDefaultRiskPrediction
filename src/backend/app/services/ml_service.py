import pandas as pd
import joblib
import os
import time
import json
import logging

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        # Môi trường Docker sẽ chạy tại /app, thư mục model nằm tại /app/model
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = os.path.join(base_dir, 'model', 'lgbm_model_v1.joblib')
        self.imputer_path = os.path.join(base_dir, 'model', 'imputer_v1.joblib')
        self.metadata_path = os.path.join(base_dir, 'model', 'model_metadata.json')

        # Load Model & Imputer
        try:
            self.model = joblib.load(self.model_path)
            self.imputer = joblib.load(self.imputer_path)
            logger.info("✅ Đã load MLService thành công!")
        except Exception as e:
            logger.error(f"❌ Không thể tải mô hình: {e}")
            self.model = None
            self.imputer = None

        # Load Metadata (Model Registry)
        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            self.active_version = self.metadata.get("active_version", "v1")
            self.threshold = self._get_active_threshold()
        except Exception:
            self.metadata = {}
            self.active_version = "v1"
            self.threshold = 0.3

    def _get_active_threshold(self) -> float:
        """Đọc threshold từ model_metadata.json — dễ thay đổi mà không cần sửa code"""
        for m in self.metadata.get("models", []):
            if m["version"] == self.active_version:
                return m.get("threshold", 0.3)
        return 0.3

    def _create_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tái tạo chính xác các đặc trưng đã Feature Engineering trong Notebook"""
        df_copy = df.copy()

        # 1. One-Hot Encoding cho Categorical từ Frontend
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

        # 2. Biến tài chính phái sinh
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

    def _run_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline chung: Feature Engineering → Align → Impute"""
        df = self._create_domain_features(df)
        expected_cols = getattr(
            self.imputer, 'feature_names_in_',
            getattr(self.model, 'feature_name_', None)
        )
        if expected_cols is not None:
            df = df.reindex(columns=expected_cols, fill_value=None)
        return pd.DataFrame(self.imputer.transform(df), columns=df.columns)

    def predict_default_risk(self, features: dict) -> tuple[float, str, float]:
        """
        Dự đoán rủi ro cho 1 khách hàng.
        Returns: (risk_score, decision, duration_ms)
        """
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")

        # ⏱️ Performance Monitoring — bắt đầu đo thời gian
        start = time.perf_counter()

        df = pd.DataFrame([features])
        df_imputed = self._run_pipeline(df)

        risk_prob = float(self.model.predict_proba(df_imputed)[0][1])
        decision = "REJECT" if risk_prob > self.threshold else "APPROVE"

        # ⏱️ Kết thúc đo — tính ra milliseconds
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(f"Predict: score={risk_prob:.4f} decision={decision} duration={duration_ms}ms")
        return risk_prob, decision, duration_ms

    def predict_batch_risk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Dự đoán rủi ro cho nhiều khách hàng từ file CSV/Excel"""
        if self.model is None or self.imputer is None:
            raise ValueError("Mô hình AI chưa được nạp.")

        df_imputed = self._run_pipeline(df.copy())
        risk_probs = self.model.predict_proba(df_imputed)[:, 1]

        df_result = df.copy()
        df_result['RISK_SCORE'] = risk_probs
        df_result['DECISION'] = ['REJECT' if p > self.threshold else 'APPROVE' for p in risk_probs]
        return df_result


# Singleton Pattern — chỉ khởi tạo 1 lần khi server bật
ml_service_instance = MLService()
