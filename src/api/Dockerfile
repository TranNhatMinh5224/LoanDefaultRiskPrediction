FROM python:3.10-slim

# Cài đặt thư viện C++ và thư viện lõi của PostgreSQL
RUN apt-get update && apt-get install -y libgomp1 libpq-dev gcc

WORKDIR /app

# Copy thư viện vào cài trước
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code (main.py, database.py) và cả thư mục models vào container
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
