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
        # Resolve backend directory (src/backend) and repo root directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        repo_root = os.path.dirname(os.path.dirname(backend_dir))
        
        # Candidate model directories in order of preference
        candidate_model_dirs = [
            os.path.join(repo_root, 'Model'),          # Local development / unit tests (root Model/)
            os.path.join(backend_dir, 'model'),       # Docker mapped directory '/app/model' or local backend/model
            '/app/model'                              # Direct absolute Docker container path
        ]
        
        # Find directory that actually contains the model registry metadata
        self.model_dir = None
        for d in candidate_model_dirs:
            meta_path = os.path.join(d, 'model_metadata.json')
            if os.path.exists(meta_path):
                self.model_dir = d
                break
        
        if not self.model_dir:
            # Fallback to local backend folder
            self.model_dir = os.path.join(backend_dir, 'model')
            
        self.metadata_path = os.path.join(self.model_dir, 'model_metadata.json')

        # Load Metadata (Model Registry) first to resolve paths
        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            self.active_version = self.metadata.get("active_version", "v1")
            self.threshold = self._get_active_threshold()
        except Exception:
            self.metadata = {}
            self.active_version = "v1"
            self.threshold = 0.3

        # Resolve paths dynamically based on active metadata
        active_model_info = {}
        for m in self.metadata.get("models", []):
            if m.get("version") == self.active_version:
                active_model_info = m
                break
                
        model_file = active_model_info.get("model_file", "lgbm_model_v1.joblib")
        preprocessor_file = active_model_info.get("preprocessor_file") or active_model_info.get("imputer_file") or "preprocessor_v1.joblib"

        self.model_path = os.path.join(self.model_dir, model_file)
        self.preprocessor_path = os.path.join(self.model_dir, preprocessor_file)

        # Load Model & Preprocessor Pipeline
        try:
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
            logger.info(f"✅ Loaded MLService successfully from {self.model_dir}!")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            self.model = None
            self.preprocessor = None

    def _get_active_threshold(self) -> float:
        """Đọc threshold từ model_metadata.json"""
        for m in self.metadata.get("models", []):
            if m.get("version") == self.active_version:
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
        
        df_copy = df_copy.replace([np.inf, -np.inf, np.float32(np.inf), np.float32(-np.inf)], np.nan)
        return df_copy

    def _run_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline chuẩn hóa: Feature Engineering → pd.get_dummies → Align columns → SimpleImputer"""
        import re
        df = self._create_domain_features(df)
        
        # Find active model info in metadata
        active_model_info = {}
        for m in self.metadata.get("models", []):
            if m.get("version") == self.active_version:
                active_model_info = m
                break
                
        feature_names = active_model_info.get("feature_names", [])
        num_cols = active_model_info.get("num_cols", [])
        
        # Fallback if metadata has no feature names (e.g. legacy model)
        if not feature_names:
            expected_cols = getattr(self.preprocessor, 'feature_names_in_', None)
            if expected_cols is not None:
                feature_names = list(expected_cols)
            else:
                feature_names = df.columns.tolist()
                
        # Perform get_dummies on input
        df_encoded = pd.get_dummies(df)
        df_encoded = df_encoded.rename(columns=lambda x: re.sub('[^A-Za-z0-9_]+', '_', x))
        
        # Reindex with expected columns, filling with NaN
        df_aligned = df_encoded.reindex(columns=feature_names, fill_value=np.nan)
        
        # Fill missing dummy columns with 0 (dummy columns are those not in num_cols)
        if num_cols:
            dummy_cols = [col for col in feature_names if col not in num_cols]
            df_aligned[dummy_cols] = df_aligned[dummy_cols].fillna(0)
            
        processed_data = self.preprocessor.transform(df_aligned)
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
