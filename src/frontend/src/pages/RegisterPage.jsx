import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../services/apiClient';

const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if(password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp!');
      return;
    }

    setLoading(true);
    try {
      const data = await apiClient('/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password })
      });
      
      alert('Đăng ký thành công! Đang chuyển hướng về trang Đăng nhập...');
      navigate('/login');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Có lỗi xảy ra khi đăng ký.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-glass-card">
        <h1 className="auth-title">Đăng Ký Tài Khoản</h1>
        <p className="auth-subtitle">Tạo tài khoản mới để sử dụng hệ thống</p>
        
        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="auth-form-group">
            <label className="auth-label" htmlFor="reg-username">Tên đăng nhập</label>
            <input 
              id="reg-username"
              type="text" 
              className="auth-input" 
              placeholder="Ví dụ: nguyenvana" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="auth-form-group">
            <label className="auth-label" htmlFor="reg-email">Email công việc</label>
            <input 
              id="reg-email"
              type="email" 
              className="auth-input" 
              placeholder="nguyenvana@bank.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="auth-form-group">
            <label className="auth-label" htmlFor="reg-password">Mật khẩu</label>
            <input 
              id="reg-password"
              type="password" 
              className="auth-input" 
              placeholder="Ít nhất 6 ký tự" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="auth-form-group">
            <label className="auth-label" htmlFor="reg-confirm">Xác nhận mật khẩu</label>
            <input 
              id="reg-confirm"
              type="password" 
              className="auth-input" 
              placeholder="Nhập lại mật khẩu" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Đăng Ký'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <span style={{ color: '#64748b' }}>Đã có tài khoản? </span>
            <Link to="/login" style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: 'bold' }}>
              Đăng nhập ngay
            </Link>
          </div>

          <div style={{ position: 'relative', margin: '0.5rem 0' }}>
            <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
            <span style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(30, 27, 75, 1)', padding: '0 10px', color: '#94a3b8', fontSize: '0.85rem' }}>HOẶC</span>
          </div>

          <Link 
            to="/dashboard" 
            style={{ 
              display: 'inline-block',
              padding: '0.75rem', 
              background: 'rgba(255,255,255,0.05)', 
              color: '#e2e8f0', 
              border: '1px solid rgba(255,255,255,0.1)', 
              borderRadius: '0.5rem', 
              textDecoration: 'none', 
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => { e.target.style.background = 'rgba(255,255,255,0.1)' }}
            onMouseOut={(e) => { e.target.style.background = 'rgba(255,255,255,0.05)' }}
          >
            Tiếp tục với tư cách Khách
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
