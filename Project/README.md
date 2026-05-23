# Norwegian Learning App — Group 24

## Team
- Student 1: Trumshi, Ines, 12220438
- Student 2: Korobeinikova, Anastasiia, 12248216
- Student 3: Brayko, Anna, 12343205

## Requirements
- Docker Desktop
- Unzip

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/memoriessofyou/IMSE-Project
cd Project

### 2. Create your .env file
cp backend/.env.example backend/.env

### 3. Start the MariaDB container
docker run --name mariadb-dev \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=language_app \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=apppassword \
  -p 3306:3306 \
  -v "$(pwd)/db/init.sql:/docker-entrypoint-initdb.d/init.sql" \
  -d mariadb:10.11

### 4. Run the backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

### 5. Open Swagger
http://localhost:8000/docs
