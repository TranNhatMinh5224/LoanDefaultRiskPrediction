// src/services/apiClient.js
// Cấu hình gọi API chung tới Backend

// Đọc URL từ file .env (Mặc định sẽ fallback về localhost nếu chưa cấu hình)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088/api/v1';

export const apiClient = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    let errorMsg = 'Có lỗi xảy ra khi gọi API';
    if (error.detail) {
      if (Array.isArray(error.detail)) {
        // FastAPI 422 Validation Error
        errorMsg = error.detail.map(err => `${err.loc.join('.')} : ${err.msg}`).join('\n');
      } else if (typeof error.detail === 'string') {
        errorMsg = error.detail;
      } else {
        errorMsg = JSON.stringify(error.detail);
      }
    }
    throw new Error(errorMsg);
  }

  return response.json();
};
