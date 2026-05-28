import React, { useState } from 'react';
import './predict.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088/api/v1';

const BatchPredictForm = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [csvPreview, setCsvPreview] = useState([]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setCsvPreview([]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Vui lòng chọn file Excel hoặc CSV.");
      return;
    }

    setLoading(true);
    setError(null);
    setCsvPreview([]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/predict/batch`, {
        method: 'POST',
        body: formData // Không set Content-Type vì fetch tự động xử lý boundary cho file
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Lỗi khi chạy xử lý hàng loạt.");
      }

      // Đọc file trả về dưới dạng Blob (CSV)
      const blob = await response.blob();
      
      // 1. Tự động tải file kết quả về máy người dùng
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KetQua_AI_${file.name}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // 2. Đọc lướt file để trích xuất 5 dòng đầu tiên làm Preview trên web
      const text = await blob.text();
      const lines = text.split('\n').filter(line => line.trim() !== '');
      const parsedLines = lines.slice(0, 6).map(line => line.split(',')); 
      setCsvPreview(parsedLines);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="predict-container">
      <div className="predict-card">
        <div className="predict-header">
          <h2>Dự đoán Hàng Loạt (Batch Processing)</h2>
          <p>Tải lên danh sách hàng nghìn khách hàng bằng file Excel/CSV. Hệ thống AI sẽ tự động chấm điểm tất cả và trả về file kết quả có đính kèm phán quyết.</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleUpload}>
          <div style={{ border: '2px dashed #cbd5e1', padding: '3rem 2rem', borderRadius: '0.75rem', textAlign: 'center', marginBottom: '1.5rem', background: '#f8fafc', transition: 'all 0.2s' }}>
            <input 
              type="file" 
              accept=".csv, .xlsx, .xls" 
              onChange={handleFileChange}
              style={{ display: 'block', margin: '0 auto', fontSize: '1rem' }}
            />
            <p style={{ marginTop: '1rem', color: '#64748b', fontSize: '0.95rem' }}>
              Chỉ hỗ trợ tải lên file <strong>.csv</strong> hoặc <strong>.xlsx</strong>
            </p>
          </div>

          <button type="submit" className="submit-btn" disabled={loading || !file}>
            {loading ? 'Đang nạp file vào máy học...' : 'Tải lên & Chạy AI Dự Đoán'}
          </button>
        </form>
      </div>

      {csvPreview.length > 0 && (
        <div className="predict-card" style={{ marginTop: '2rem', padding: '1.5rem', overflowX: 'auto', border: '2px solid #2563eb' }}>
          <h3 style={{ color: '#0f172a', marginBottom: '0.5rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🎉 Hoàn tất! File kết quả đã tự động lưu về máy.
          </h3>
          <p style={{ color: '#475569', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
            Bản xem trước 5 khách hàng đầu tiên (Cuộn sang phải cùng để xem cột <strong>RISK_SCORE</strong> và <strong>DECISION</strong> mà AI vừa gán vào):
          </p>
          
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '2px solid #cbd5e1' }}>
                {csvPreview[0].map((header, i) => (
                  <th key={i} style={{ padding: '0.85rem', whiteSpace: 'nowrap', color: '#334155' }}>{header.replace(/"/g, '')}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {csvPreview.slice(1).map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  {row.map((cell, j) => {
                    const cleanCell = cell.replace(/"/g, '');
                    // Highlight màu sắc cho 2 cột kết quả cuối cùng (Risk Score & Decision)
                    const isDecision = cleanCell === 'APPROVE' || cleanCell === 'REJECT';
                    let color = '#334155';
                    let bg = 'transparent';
                    let displayCell = cleanCell;
                    
                    if (cleanCell === 'REJECT') {
                      color = '#991b1b'; bg = '#fef2f2';
                    } else if (cleanCell === 'APPROVE') {
                      color = '#166534'; bg = '#f0fdf4';
                    } else if (j === row.length - 2) {
                      // Cột RISK_SCORE
                      const numVal = parseFloat(cleanCell);
                      if (!isNaN(numVal)) {
                         displayCell = (numVal * 100).toFixed(2) + '%';
                         color = numVal > 0.3 ? '#991b1b' : '#166534';
                         bg = numVal > 0.3 ? '#fef2f2' : '#f0fdf4';
                      }
                    }

                    return (
                      <td key={j} style={{ padding: '0.75rem', whiteSpace: 'nowrap', color, background: bg, fontWeight: (isDecision || j >= row.length - 2) ? '700' : 'normal' }}>
                        {displayCell}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BatchPredictForm;
