import React from 'react';
import LoginForm from '../features/auth/components/LoginForm';

const LoginPage = () => {
  return (
    <div className="auth-page">
      <div className="auth-glass-card">
        <h1 className="auth-title">Home Credit AI</h1>
        <p className="auth-subtitle">Cổng truy cập Dự đoán Rủi ro Tín dụng</p>
        <LoginForm />
      </div>
    </div>
  );
};

export default LoginPage;
