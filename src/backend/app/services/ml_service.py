import pandas as pd
import joblib
import os
import time
import json
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        # Docker workspace is /app, model folder maps to /app/model
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = os.path.join(base_dir, 'model', 'lgbm_model_v1.joblib')
        self.preprocessor_path = os.path.join(base_dir, 'model', 'preprocessor_v1.joblib')
        self.metadata_path = os.path.join(base_dir, 'model', 'model_metadata.json')

        # Load Model & Preprocessor Pipeline
        try:
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
            logger.info("✅ Đã load MLService và Preprocessor Pipeline thành công!")
        except Exception as e:
            logger.error(f"❌ Không thể tải mô hình: {e}")
            self.model = None
            self.preprocessor = None

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
        """Đọc threshold từ model_metadata.json"""
        for m in self.metadata.get("models", []):
            if m["version"] == self.active_version:
                return m.get("threshold", 0.3)
        return 0.3

    def _create_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tạo các đặc trưng phái sinh số học."""
        df_copy = df.copy()

        # Biến tài chính phái sinh
        if 'DAYS_BIRTH' in df_copy:
            df_copy['AGE'] = df_copy['DAYS_BIRTH'] / -365.0
        if 'AMT_CREDIT' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
            df_copy['CREDIT_INCOME_PERCENT'] = df_copy['AMT_CREDIT'] / df_copy['AMT_INCOME_TOTAL']
        if 'AMT_ANNUITY' in df_copy and 'AMT_INCOME_TOTAL' in df_copy:
            df_copy['ANNUITY_INCOME_PERCENT'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_INCOME_TOTAL']
        if 'AMT_ANNUITY' in df_copy and 'AMT_CREDIT' in df_copy:
            df_copy['CREDIT_TERM'] = df_copy['AMT_ANNUITY'] / df_copy['AMT_CREDIT']
        if 'DAYS_EMPLOYED' in df_copy and 'DAYS_BIRTH' in df_copy:
            df_copy['DAYS_EMPLOYED_PERCENT'] = df_copy['DAYS_EMPLOYED'] / df_copy['DAYS_BIRTH']
        
        # Thay thế các giá trị vô cùng (inf) bằng NaN
        df_copy = df_copy.replace([np.inf, -np.inf], np.nan)
        return df_copy

    def _run_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline chuẩn hóa: Feature Engineering → Align original features → Transform via ColumnTransformer"""
        import re
        df = self._create_domain_features(df)
        
        # Căn chỉnh cột đầu vào trùng khớp với pipeline huấn luyện
        expected_cols = getattr(self.preprocessor, 'feature_names_in_', None)
        if expected_cols is not None:
            df = df.reindex(columns=expected_cols, fill_value=np.nan)
            
        processed_data = self.preprocessor.transform(df)
        
        # Gán lại tên cột sau mã hóa và làm sạch (sanitize) tên cột
        raw_feature_names = self.preprocessor.get_feature_names_out()
        sanitize_col = lambda x: re.sub(r'[^A-Za-z0-9_]+', '_', x)
        feature_names = [sanitize_col(col) for col in raw_feature_names]
        
        return pd.DataFrame(processed_data, columns=feature_names)

    def predict_default_risk(self, features: dict) -> tuple[float, str, float]:
        """
        Dự đoán rủi ro cho 1 khách hàng.
        Returns: (risk_score, decision, duration_ms)
        """
        if self.model is None or self.preprocessor is None:
            raise ValueError("Mô hình AI chưa được nạp.")

        # Performance Monitoring
        start = time.perf_counter()

        df = pd.DataFrame([features])
        df_imputed = self._run_pipeline(df)

        risk_prob = float(self.model.predict_proba(df_imputed)[0][1])
        decision = "REJECT" if risk_prob > self.threshold else "APPROVE"

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(f"Predict: score={risk_prob:.4f} decision={decision} duration={duration_ms}ms")
        return risk_prob, decision, duration_ms

    def predict_batch_risk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Dự đoán rủi ro cho nhiều khách hàng từ file CSV/Excel"""
        if self.model is None or self.preprocessor is None:
            raise ValueError("Mô hình AI chưa được nạp.")

        df_imputed = self._run_pipeline(df.copy())
        risk_probs = self.model.predict_proba(df_imputed)[:, 1]

        df_result = df.copy()
        df_result['RISK_SCORE'] = risk_probs
        df_result['DECISION'] = ['REJECT' if p > self.threshold else 'APPROVE' for p in risk_probs]
        return df_result


# Singleton Pattern
ml_service_instance = MLService()
