"""
Smoke test tối thiểu để kiểm tra MLService hoạt động đúng.
Chạy: pytest tests/ -v
"""
import pytest
import sys
import os

# Thêm đường dẫn backend vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMLService:
    """Test lớp MLService - hạt nhân của hệ thống AI"""

    def test_model_loaded_successfully(self):
        """Model và Preprocessor phải load được khi khởi động"""
        from app.services.ml_service import ml_service_instance
        assert ml_service_instance.model is not None, "LightGBM model chưa được nạp!"
        assert ml_service_instance.preprocessor is not None, "Preprocessor pipeline chưa được nạp!"

    def test_predict_returns_valid_score(self):
        """Điểm rủi ro phải nằm trong khoảng [0.0, 1.0]"""
        from app.services.ml_service import ml_service_instance
        features = {
            "EXT_SOURCE_1": 0.5,
            "EXT_SOURCE_2": 0.4,
            "EXT_SOURCE_3": 0.3,
            "DAYS_BIRTH": -12000,
            "DAYS_EMPLOYED": -2000,
            "AMT_INCOME_TOTAL": 180000,
            "AMT_CREDIT": 450000,
            "AMT_ANNUITY": 22500,
        }
        score, decision, duration_ms = ml_service_instance.predict_default_risk(features)
        assert 0.0 <= score <= 1.0, f"Risk score không hợp lệ: {score}"
        assert decision in ["APPROVE", "REJECT"], f"Decision không hợp lệ: {decision}"
        assert duration_ms >= 0, "Thời gian xử lý không hợp lệ"

    def test_high_risk_profile_returns_reject(self):
        """Hồ sơ rủi ro cực cao phải bị REJECT"""
        from app.services.ml_service import ml_service_instance
        features = {
            "EXT_SOURCE_1": 0.01,   # Điểm tín dụng cực thấp
            "EXT_SOURCE_2": 0.01,
            "EXT_SOURCE_3": 0.01,
            "DAYS_BIRTH": -8000,    # Rất trẻ (~22 tuổi)
            "INSTAL_DPD_max": 90,   # Từng trễ hạn 90 ngày
        }
        score, decision, duration_ms = ml_service_instance.predict_default_risk(features)
        assert decision == "REJECT", f"Hồ sơ xấu phải bị REJECT, nhưng trả về: {decision}"

    def test_feature_engineering_creates_derived_columns(self):
        """Hàm _create_domain_features phải tạo ra cột AGE và các tỷ lệ tài chính"""
        import pandas as pd
        from app.services.ml_service import ml_service_instance
        df = pd.DataFrame([{
            "DAYS_BIRTH": -14600,       # 40 tuổi
            "AMT_CREDIT": 500000,
            "AMT_INCOME_TOTAL": 200000,
            "AMT_ANNUITY": 25000,
            "DAYS_EMPLOYED": -3650,
        }])
        result = ml_service_instance._create_domain_features(df)
        assert "AGE" in result.columns, "Thiếu cột AGE"
        assert "CREDIT_INCOME_PERCENT" in result.columns, "Thiếu cột CREDIT_INCOME_PERCENT"
        assert "ANNUITY_INCOME_PERCENT" in result.columns, "Thiếu cột ANNUITY_INCOME_PERCENT"
        assert abs(result["AGE"].iloc[0] - 40.0) < 1, "AGE tính sai"
