# 🚀 Home Credit Default Risk - Production API

Đây là hệ thống Backend API chuẩn MLOps để phục vụ dự đoán khả năng vỡ nợ của khách hàng (Home Credit Default Risk). Hệ thống được xây dựng bằng **FastAPI**, lưu vết chấm điểm (Audit Log) bằng **PostgreSQL** và được tổ chức theo chuẩn **Clean Architecture**.

---

## 📂 Cấu trúc dự án (Clean Architecture)

Dự án áp dụng chặt chẽ 3 Design Patterns chuyên nghiệp: **Dependency Injection**, **Service Layer**, và **Repository Pattern**.

- `app/api/`: Chứa Controllers/Routes (Nơi định tuyến các API Endpoint).
- `app/services/`: Chứa khối não bộ nghiệp vụ ML (Load file Joblib, xử lý Pandas, tính toán rủi ro).
- `app/repositories/`: Chứa thao tác giao tiếp với Database (Thêm, Sửa, Xóa).
- `app/schemas/`: Chứa Pydantic Models để kiểm soát và Validation dữ liệu đầu vào.
- `app/core/`: Cấu hình hệ thống cốt lõi và đọc các biến môi trường.

---

## ⚙️ Hướng dẫn Khởi chạy (Sử dụng Docker)

Toàn bộ Backend và Database đã được đóng gói 100% bằng Docker. 

### Bước 1: Bơm AI vào hệ thống
Bạn cần copy 2 file AI đã huấn luyện xong (Từ giai đoạn Research Notebook):
- `lgbm_model_v3.joblib`
- `imputer_v3.joblib`

Và đặt chúng vào thư mục: `models/` (Nằm ngay trong thư mục `src/backend/model/`).

### Bước 2: Cấu hình môi trường
Hệ thống sử dụng các file `.env` để bảo mật. Trong thư mục này đã có sẵn file `.env.example`. Khi chạy thực tế, Docker Compose sẽ tự động nhận diện các thông số để khởi tạo Database.

### Bước 3: Đóng gói và Chạy
Mở Terminal tại thư mục `src/backend/` và gõ câu lệnh sau:

```bash
docker-compose up --build -d
```
*(Hệ thống sẽ kéo PostgreSQL về, cài đặt các thư viện AI và bật API Server trong nền).*

---

## 🌍 Tài liệu giao tiếp API (Swagger UI)

Sự ưu việt của FastAPI là nó tự động sinh ra trang tài liệu tương tác.
Khi server báo khởi động thành công, hãy truy cập vào trình duyệt:
👉 **[http://localhost:8088/docs](http://localhost:8088/docs)**

Tại đây bạn có thể dùng tính năng `Try it out` để gửi một tệp JSON thông tin khách hàng vào Endpoint `POST /api/v1/predict` và nhận về quyết định duyệt vay.

---

## 🛠 Công nghệ nền tảng (Tech Stack)
- **Web Framework:** FastAPI, Uvicorn, Pydantic
- **Machine Learning:** LightGBM, Scikit-learn, Pandas
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **DevOps / MLOps:** Docker, Docker Compose
