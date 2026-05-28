import React, { useState } from 'react';
import { apiClient } from '../../../services/apiClient';
import './predict.css';

const PREDICT_FIELDS = [
  // 1. Phân loại Khách hàng (Categorical)
  { key: 'CODE_GENDER', label: 'Giới tính', type: 'select', options: [{value: 'F', label: 'Nữ'}, {value: 'M', label: 'Nam'}], desc: 'Giới tính của khách hàng' },
  { key: 'NAME_EDUCATION_TYPE', label: 'Trình độ học vấn', type: 'select', options: [{value: 'Higher education', label: 'Đại học/Sau Đại học'}, {value: 'Secondary / secondary special', label: 'Trung học/Nghề'}, {value: 'Lower secondary', label: 'Cấp 2'}], desc: 'Trình độ học vấn cao nhất' },
  { key: 'FLAG_OWN_CAR', label: 'Sở hữu Ô tô (Tài sản)', type: 'select', options: [{value: 'Y', label: 'Có'}, {value: 'N', label: 'Không'}], desc: 'Khách hàng có sở hữu ô tô không?' },
  
  // 2. Điểm tín dụng (Numerical)
  { key: 'EXT_SOURCE_1', label: 'Điểm uy tín Dân cư (Hồ sơ gốc)', placeholder: 'VD: 0.501', desc: 'Thang điểm 0.0 -> 1.0 (Dựa trên thông tin nhân khẩu, dân cư, bảo hiểm...)' },
  { key: 'EXT_SOURCE_2', label: 'Điểm tín dụng Ngân hàng (CIC)', placeholder: 'VD: 0.222', desc: 'Thang điểm 0.0 -> 1.0 (Đánh giá uy tín trả nợ ở các ngân hàng khác)' },
  { key: 'EXT_SOURCE_3', label: 'Điểm uy tín Viễn thông (Thay thế)', placeholder: 'VD: 0.155', desc: 'Thang điểm 0.0 -> 1.0 (Dựa trên lịch sử thanh toán cước điện thoại, sinh hoạt)' },
  
  // 3. Thông tin cá nhân & Khoản vay
  { key: 'DAYS_BIRTH', label: 'Tuổi của Khách hàng', placeholder: 'VD: 41', desc: 'Hệ thống sẽ tự động quy đổi tuổi ra số ngày âm để báo cáo Backend (Từ 18 đến 100 tuổi).' },
  { key: 'DAYS_EMPLOYED', label: 'Số năm làm việc', placeholder: 'VD: 5', desc: 'Hệ thống sẽ tự động quy đổi ra số ngày âm.' },
  { key: 'AMT_INCOME_TOTAL', label: 'Tổng thu nhập hằng năm', placeholder: 'VD: 200000', desc: 'Mức thu nhập hàng năm của khách hàng (Phải > 0)' },
  { key: 'AMT_CREDIT', label: 'Tổng số tiền muốn vay', placeholder: 'VD: 500000', desc: 'Hạn mức tín dụng hoặc khoản vay (Phải > 0)' },
  { key: 'AMT_ANNUITY', label: 'Tiền trả góp hàng tháng', placeholder: 'VD: 25000', desc: 'Khoản tiền khách hàng cam kết trả mỗi kỳ' },
  { key: 'BUREAU_AMT_CREDIT_SUM_mean', label: 'Dư nợ trung bình hiện tại', placeholder: 'VD: 150000', desc: 'Trung bình khoản nợ đang có tại các TCTD khác' },
  { key: 'INSTAL_DPD_max', label: 'Số ngày trễ hạn cao nhất', placeholder: 'VD: 5', desc: 'Số ngày khách hàng từng đóng tiền trễ trong quá khứ' }
];

const PredictForm = () => {
  const [formData, setFormData] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);



  const validateForm = () => {
    // Chỉ validate nếu người dùng CÓ nhập dữ liệu
    if (formData.DAYS_BIRTH && (formData.DAYS_BIRTH < 18 || formData.DAYS_BIRTH > 100)) return 'Tuổi khách hàng phải từ 18 đến 100.';
    if (formData.AMT_INCOME_TOTAL && formData.AMT_INCOME_TOTAL <= 0) return 'Tổng thu nhập phải lớn hơn 0.';
    if (formData.AMT_CREDIT && formData.AMT_CREDIT <= 0) return 'Tổng số tiền vay phải lớn hơn 0.';
    if (formData.EXT_SOURCE_1 && (formData.EXT_SOURCE_1 < 0 || formData.EXT_SOURCE_1 > 1)) return 'EXT_SOURCE_1 phải nằm trong khoảng từ 0 đến 1.';
    if (formData.EXT_SOURCE_2 && (formData.EXT_SOURCE_2 < 0 || formData.EXT_SOURCE_2 > 1)) return 'EXT_SOURCE_2 phải nằm trong khoảng từ 0 đến 1.';
    if (formData.EXT_SOURCE_3 && (formData.EXT_SOURCE_3 < 0 || formData.EXT_SOURCE_3 > 1)) return 'EXT_SOURCE_3 phải nằm trong khoảng từ 0 đến 1.';
    return null;
  };

  const handleChange = (e, key, type) => {
    let val = e.target.value;
    if (type !== 'select') {
      val = parseFloat(val);
      val = isNaN(val) ? '' : val;
    }
    setFormData({ ...formData, [key]: val });
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 1. Validate tại Frontend
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    // 2. Tiền xử lý dữ liệu trước khi gửi xuống Backend
    const processedFeatures = {};
    Object.keys(formData).forEach(key => {
      // Giữ lại chuỗi (cho select) hoặc số (cho input)
      if (formData[key] !== '' && formData[key] !== null) {
        if (typeof formData[key] === 'string' || !isNaN(formData[key])) {
          processedFeatures[key] = formData[key];
        }
      }
    });
    
    if (processedFeatures.DAYS_BIRTH) {
      processedFeatures.DAYS_BIRTH = processedFeatures.DAYS_BIRTH * -365; // Đổi Tuổi -> Ngày âm
    }
    if (processedFeatures.DAYS_EMPLOYED) {
      processedFeatures.DAYS_EMPLOYED = processedFeatures.DAYS_EMPLOYED * -365; // Đổi Số năm -> Ngày âm
    }

    try {
      // 3. Gọi API thật
      const payload = {
        sk_id_curr: "KH_WEB_" + Math.floor(Math.random() * 10000), // Random ID
        features: processedFeatures
      };

      const data = await apiClient('/predict', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setResult({
        decision: data.data.decision,
        risk_score: data.data.risk_score.toFixed(4)
      });
    } catch (err) {
      console.error(err);
      setError(err.message || 'Có lỗi xảy ra khi kết nối với máy chủ AI.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="predict-container">
      <div className="predict-card">
        <div className="predict-header">
          <h2>Đánh giá Khách hàng Cá nhân</h2>
          <p>Điền các thông số tài chính để nhận định mức độ rủi ro tín dụng.</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="predict-form">
          <div className="form-grid">
            {PREDICT_FIELDS.map((field) => (
              <div className="input-group" key={field.key}>
                <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '4px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: '600', color: '#1e293b' }}>
                    {field.label}
                    {field.key.includes('EXT_SOURCE') && <span style={{ color: '#2563eb', fontSize: '0.8rem', marginLeft: '6px', fontWeight: 'bold' }}>({field.key})</span>}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '400', lineHeight: '1.4' }}>
                    {field.desc}
                  </span>
                </label>
                {field.type === 'select' ? (
                  <select 
                    onChange={(e) => handleChange(e, field.key, field.type)}
                    defaultValue=""
                  >
                    <option value="" disabled>--- Bỏ qua hoặc Chọn ---</option>
                    {field.options.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    step="any"
                    placeholder={field.placeholder || "Bỏ trống nếu không có..."}
                    onChange={(e) => handleChange(e, field.key, field.type)}
                  />
                )}
              </div>
            ))}
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Đang phân tích mô hình...' : 'Chạy Mô Hình Dự Đoán'}
          </button>
        </form>
      </div>

      {result && (
        <div className={`result-card ${result.decision.toLowerCase()}`}>
          <h3>Kết quả phán quyết</h3>
          <div className="result-score">
            Xác suất vỡ nợ: <span>{(parseFloat(result.risk_score) * 100).toFixed(2)}%</span>
            <span style={{ fontSize: '0.9rem', fontWeight: '400', color: '#64748b', display: 'block', marginTop: '6px' }}>
              (Ngưỡng từ chối: &gt; 30%)
            </span>
          </div>
          <div className="result-decision">
            Trạng thái: <strong>{result.decision}</strong>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictForm;
