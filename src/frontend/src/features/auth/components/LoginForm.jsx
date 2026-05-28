import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../../../services/apiClient';
import { useAuth } from '../../../context/AuthContext';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const data = await apiClient('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
      });

      // Delegate auth state to context
      login(data.data.access_token, data.data.refresh_token, 'admin');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Sai tên đăng nhập hoặc mật khẩu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {error && <div className="error-message" style={{marginBottom: '1.5rem'}}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="auth-form-group">
          <label className="auth-label" htmlFor="username">Tên đăng nhập</label>
          <input 
            id="username"
            type="text" 
            className="auth-input" 
            placeholder="Nhập tên đăng nhập" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        
        <div className="auth-form-group">
          <label className="auth-label" htmlFor="password">Mật khẩu</label>
          <input 
            id="password"
            type="password" 
            className="auth-input" 
            placeholder="••••••••" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? 'Đang xử lý...' : 'Đăng nhập hệ thống'}
        </button>
      </form>
      
      <div style={{ textAlign: 'center', marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <span style={{ color: '#64748b' }}>Chưa có tài khoản? </span>
          <Link to="/register" style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: 'bold' }}>
            Đăng ký ngay
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
  );
};

export default LoginForm;
