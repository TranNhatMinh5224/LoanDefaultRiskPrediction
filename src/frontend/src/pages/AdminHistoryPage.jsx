import React, { useState, useEffect } from 'react';
import MainLayout from '../components/layout/MainLayout';
import { apiClient } from '../services/apiClient';

const AdminHistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await apiClient('/history?page=1&size=20', { method: 'GET' });
      if (data && data.data && data.data.data) {
        setHistory(data.data.data);
      }
    } catch (err) {
      console.error(err);
      setError('Không thể tải lịch sử dự đoán từ máy chủ.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
  };

  return (
    <MainLayout>
      <div className="predict-card" style={{ maxWidth: '1000px', margin: '2rem auto' }}>
        <div className="predict-header">
          <h2>Quản Trị Viên: Lịch Sử Dự Đoán</h2>
          <p>Xem toàn bộ nhật ký các phiên chạy Mô hình AI của toàn hệ thống.</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div style={{ overflowX: 'auto' }}>
          {loading ? (
            <p style={{ textAlign: 'center', padding: '2rem' }}>Đang tải dữ liệu...</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.5)', borderBottom: '2px solid #cbd5e1' }}>
                  <th style={{ padding: '1rem' }}>Mã Khách Hàng</th>
                  <th style={{ padding: '1rem' }}>Thời Gian</th>
                  <th style={{ padding: '1rem' }}>Điểm Rủi Ro</th>
                  <th style={{ padding: '1rem' }}>Quyết Định</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>Chưa có dữ liệu lịch sử nào.</td>
                  </tr>
                ) : (
                  history.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
                      <td style={{ padding: '1rem' }}>{item.sk_id_curr}</td>
                      <td style={{ padding: '1rem' }}>{formatDate(item.created_at)}</td>
                      <td style={{ padding: '1rem', color: item.risk_score > 0.3 ? '#dc2626' : '#16a34a', fontWeight: 'bold' }}>
                        {item.risk_score.toFixed(4)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ 
                          padding: '4px 8px', 
                          background: item.decision === 'APPROVE' ? '#dcfce7' : '#fee2e2', 
                          color: item.decision === 'APPROVE' ? '#166534' : '#991b1b', 
                          borderRadius: '4px' 
                        }}>
                          {item.decision}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default AdminHistoryPage;
