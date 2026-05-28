import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const MainLayout = ({ children }) => {
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItemStyle = (path) => ({
    color: location.pathname === path ? '#2563eb' : '#475569',
    fontWeight: location.pathname === path ? '600' : '500',
    textDecoration: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '0.375rem',
    background: location.pathname === path ? '#eff6ff' : 'transparent',
    transition: 'all 0.2s',
    fontSize: '0.95rem'
  });

  return (
    <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh', fontFamily: "'Inter', sans-serif" }}>
      {/* Header Chuyên Nghiệp */}
      <header style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        padding: '0 2rem', 
        height: '64px',
        backgroundColor: '#ffffff', 
        borderBottom: '1px solid #e2e8f0', 
        position: 'sticky', 
        top: 0, 
        zIndex: 100,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <h1 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a', fontWeight: '700', letterSpacing: '-0.5px' }}>
            <span style={{ color: '#2563eb' }}>HomeCredit</span> AI
          </h1>
          
          <nav style={{ display: 'flex', gap: '0.5rem' }}>
            <Link to="/" style={navItemStyle('/')}>Khách Hàng (Public)</Link>
            {user?.role === 'admin' && (
              <Link to="/admin/history" style={navItemStyle('/admin/history')}>Quản Trị (Admin)</Link>
            )}
          </nav>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {user ? (
            <>
              <span style={{ fontSize: '0.9rem', color: '#64748b' }}>Xin chào, <strong>{user.username}</strong></span>
              <button 
                onClick={logout} 
                style={{ padding: '0.4rem 1rem', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500', fontSize: '0.9rem', transition: 'all 0.2s' }}
                onMouseOver={(e) => { e.target.style.background = '#e2e8f0'; e.target.style.color = '#0f172a'; }}
                onMouseOut={(e) => { e.target.style.background = '#f1f5f9'; e.target.style.color = '#475569'; }}
              >
                Đăng Xuất
              </button>
            </>
          ) : (
            <>
              <Link to="/login" style={{ color: '#475569', textDecoration: 'none', fontWeight: '500', fontSize: '0.9rem' }}>Đăng nhập</Link>
              <Link to="/register" style={{ padding: '0.4rem 1rem', background: '#2563eb', color: 'white', border: 'none', borderRadius: '0.375rem', textDecoration: 'none', fontWeight: '500', fontSize: '0.9rem', boxShadow: '0 1px 2px rgba(37, 99, 235, 0.3)' }}>Đăng ký</Link>
            </>
          )}
        </div>
      </header>
      
      <main style={{ minHeight: 'calc(100vh - 128px)', padding: '2rem' }}>
        {children}
      </main>
      
      <footer style={{ textAlign: 'center', padding: '1rem', color: '#94a3b8', fontSize: '0.85rem', borderTop: '1px solid #e2e8f0' }}>
        &copy; {new Date().getFullYear()} Loan Default Prediction System - Enterprise Edition
      </footer>
    </div>
  );
};

export default MainLayout;
