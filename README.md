# 🚀 Dự đoán Rủi ro Vỡ nợ Tín dụng (Home Credit Default Risk)
*Đọc bản tiếng Anh tại [English EN](README.md)*

### Hệ thống Machine Learning cho bài toán Phân loại Rủi ro Tín dụng & Đánh giá Năng lực Tài chính

**Tác giả:** [Tên của bạn]  
**Vị trí:** Data Scientist / Data Analyst  
**Địa điểm:** Việt Nam – 2026  

---

# 🌍 Bối cảnh bài toán

## 🏦 Mở rộng khả năng tiếp cận tài chính an toàn

Nhiều người dân gặp khó khăn trong việc vay vốn do không có đủ lịch sử tín dụng hoặc hồ sơ tài chính truyền thống. Các công ty tài chính như Home Credit muốn mở rộng dịch vụ đến nhóm khách hàng "unbanked" (chưa tiếp cận ngân hàng) này, nhưng đồng thời phải kiểm soát chặt chẽ rủi ro nợ xấu.

Để giải quyết vấn đề, Home Credit đã cung cấp một bộ dữ liệu khổng lồ bao gồm thông tin cá nhân, lịch sử ứng tuyển, và hành vi trả nợ từ các tổ chức tín dụng khác (Bureau) để dự đoán khả năng hoàn trả khoản vay của khách hàng.

**Thách thức chính:** *Làm thế nào để xây dựng một mô hình AI có thể tổng hợp dữ liệu từ 7 bảng độc lập, xử lý tình trạng mất cân bằng dữ liệu cực độ (92% trả đúng hạn - 8% vỡ nợ) và đưa ra dự đoán chính xác nhất để tối ưu hóa quyết định cho vay?*

---

## 📊 Mô tả dữ liệu & cấu trúc hệ thống

Dataset bao gồm 7 bảng dữ liệu quan hệ chứa hàng chục triệu bản ghi, được liên kết với nhau qua mã khách hàng (`SK_ID_CURR`).

### 1. Cấu trúc hệ thống
Hệ thống AI xử lý tập trung vào 1 nhánh duy nhất:
- Nhánh **Phân loại nhị phân (Binary Classification)**: Dự đoán xác suất khách hàng vỡ nợ (1: Vỡ nợ, 0: Trả đúng hạn).

### 2. Các nguồn dữ liệu chính (6 Bảng Vệ Tinh)
- `application_train/test.csv`: Thông tin nhân khẩu học và khoản vay hiện tại.
- `bureau.csv`: Lịch sử khoản vay tại các ngân hàng/tổ chức tài chính khác.
- `previous_application.csv`: Lịch sử nộp đơn vay trong quá khứ tại Home Credit.
- `installments_payments.csv`: Lịch sử đóng tiền trả góp (có trễ hạn hay không).
- `POS_CASH_balance.csv`: Số dư và trạng thái các khoản vay tiền mặt/mua hàng.
- `credit_card_balance.csv`: Biến động số dư thẻ tín dụng hàng tháng.

---

### 3. Output
- **Target (Classification):** Xác suất vỡ nợ (từ 0.0 đến 1.0).
- Được sử dụng để sắp xếp thứ tự rủi ro và ra quyết định duyệt/từ chối tự động.

---

### 4. Ứng dụng thực tế
Khi hệ thống dự đoán chính xác rủi ro vỡ nợ, nó mang lại giá trị to lớn cho tổ chức tài chính:
- **Tối ưu hóa lợi nhuận & Giảm nợ xấu:** Lọc bỏ những hồ sơ có rủi ro cao, tiết kiệm hàng chục tỷ đồng từ các khoản vay mất trắng.
- **Duyệt hồ sơ tự động (Auto-Approval):** Khách hàng điểm tín dụng tốt có thể được giải ngân ngay lập tức trong vài giây mà không cần con người thẩm định.
- **Cá nhân hóa lãi suất:** Đưa ra mức lãi suất và hạn mức tín dụng phù hợp dựa trên điểm rủi ro của từng cá nhân.

---

# 📌 Tóm tắt hệ thống

Hệ thống gồm các bước:
- Phân tích dữ liệu (EDA) và nhận diện Data Imbalance.
- Tiền xử lý (Xử lý Outlier, Missing Values).
- Feature Engineering (Tạo biến tài chính, Gộp 6 bảng vệ tinh).
- Huấn luyện đa mô hình & Đánh giá (Logistic, Random Forest, LightGBM).

---

# 1️⃣ Phân tích dữ liệu (EDA)

## Mất cân bằng lớp (Class Imbalance)
Dữ liệu cực kỳ lệch: 92% mẫu là Class 0, chỉ 8% là Class 1. 
👉 Sử dụng metric **ROC-AUC** để đánh giá thay vì Accuracy.

## Ngoại lai (Outliers)
Phát hiện biến `DAYS_EMPLOYED` chứa giá trị dị thường `365243` ngày (~1000 năm). Đã thay thế toàn bộ bằng `NaN` để tránh nhiễu.

## Tương quan & Phân bố
Tuổi tác (`AGE`) có ảnh hưởng rõ rệt: Nhóm người trẻ (20-30 tuổi) có tỷ lệ bùng nợ cao hơn đáng kể so với nhóm trung niên.

---

# 2️⃣ Tiền xử lý & Feature Engineering

- **Domain Knowledge Features:** Tạo các chỉ số tài chính chuyên sâu như `CREDIT_INCOME_PERCENT` (Tỷ lệ nợ/thu nhập), `ANNUITY_INCOME_PERCENT`.
- **Advanced Relational Aggregation:** Dùng `groupby` và `agg` để đúc kết hàng triệu dòng từ 5 bảng vệ tinh (tính Tổng nợ, Số ngày trễ hạn tối đa, Số lần bị từ chối...) và nối vào bảng chính.
- **Mã hóa (Encoding):** One-hot Encoding đồng bộ giữa Train/Test.
- **Xử lý Missing/Infinity:** Thay thế giá trị vô cực bằng `NaN` và lấp đầy toàn bộ khoảng trống bằng thuật toán `SimpleImputer(strategy='median')`.
- **Tối ưu RAM:** Áp dụng `gc.collect()` để giải phóng bộ nhớ sau mỗi lần nối bảng, giúp hệ thống không bị tràn RAM (Crash).

---

# 3️⃣ Mô hình & đánh giá

## Metric
- **ROC-AUC:** Tiêu chuẩn vàng cho bài toán phân loại mất cân bằng lớp. Độ đo khả năng phân tách giữa người trả đúng hạn và người vỡ nợ.

---

## Quá trình Thử nghiệm Đa mô hình
1. **Logistic Regression (Baseline):** 
   - Yêu cầu Scale dữ liệu (MinMaxScaler).
   - Đạt ROC-AUC ~ 0.6925.
2. **Random Forest (Tầm trung):**
   - Thuật toán Ensemble Tree cơ bản.
   - Đạt ROC-AUC ~ 0.7244.
3. **LightGBM (State-of-the-Art):**
   - Thuật toán Gradient Boosting siêu tốc độ và tối ưu cho dữ liệu dạng bảng khổng lồ.
   - Tích hợp *Early Stopping* chống Overfitting.
   - Đạt ROC-AUC ~ **0.7768**.

---

# 4️⃣ Kết quả cuối

- **Best Model:** LightGBM  
- **Validation ROC-AUC:** 0.7768
- **Tốc độ:** Xử lý tập train gồm ~250.000 dòng và 245 features chỉ trong chưa đầy 1 phút.

## Data Insights (Top Features)
Mô hình đã chứng minh việc gộp bảng vệ tinh là cực kỳ giá trị khi các biến quan trọng nhất quyết định rủi ro bao gồm:
1. `EXT_SOURCE_1/2/3`: Điểm tín dụng từ tổ chức bên ngoài.
2. `BUREAU_TOTAL_DEBT`: Tổng số tiền đang nợ ở các ngân hàng khác.
3. `INSTAL_DPD_max`: Số ngày trả chậm tối đa trong quá khứ.
4. `AGE`: Tuổi của khách hàng.

## Model artifacts
- `lgbm_model_v3.joblib`: Mô hình LightGBM đã huấn luyện.
- `imputer_v3.joblib`: Bộ điền khuyết thiếu Median chuẩn hóa.
- `submission_v3_full_database.csv`: File dự đoán sẵn sàng đẩy lên Kaggle.

---

# 🏁 Kết luận

Dự án đã xây dựng thành công một quy trình (Pipeline) Machine Learning khép kín từ khâu thu thập dữ liệu quan hệ phức tạp đến tối ưu mô hình. Việc áp dụng LightGBM kết hợp cùng Feature Engineering tinh xảo không chỉ xử lý được bài toán mất cân bằng mà còn tăng cường độ chính xác lên mức cạnh tranh (ROC-AUC 0.7768), giúp ngân hàng tự động hóa và nâng cao năng lực xét duyệt hồ sơ vay.
