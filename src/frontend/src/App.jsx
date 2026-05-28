import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AdminHistoryPage from './pages/AdminHistoryPage';

function AppRoutes() {
  return (
    <Routes>
      {/* Tính năng Public (Khách vãng lai cũng dùng được) */}
      <Route path="/" element={<DashboardPage />} />
      <Route path="/predict" element={<DashboardPage />} />
      
      {/* Xác thực */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Tính năng Private (Dành cho Admin) */}
      <Route path="/admin/history" element={<AdminHistoryPage />} />
      
      {/* Mặc định nhảy về trang chủ */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
