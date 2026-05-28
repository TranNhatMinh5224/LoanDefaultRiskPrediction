import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Khôi phục phiên đăng nhập từ token
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role'); // Giả lập lưu role
    
    if (token) {
      setUser({ 
        username: 'Admin', 
        role: role || 'admin' // Mặc định giả lập là admin để demo
      });
    }
    setLoading(false);
  }, []);

  const login = (token, refreshToken, role = 'admin') => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user_role', role);
    setUser({ username: 'Admin', role });
    navigate('/admin/history'); // Mặc định admin login xong vào dashboard
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
    setUser(null);
    navigate('/');
  };

  if (loading) return <div>Đang tải hệ thống...</div>;

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
