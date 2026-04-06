import requests
import os
from dotenv import load_dotenv
import mysql.connector as mc
from datetime import datetime

load_dotenv()

API_KEY = os.getenv('SEOUL_DATA_KEY')

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}
DB_NAME = "bike_db"   # 따로 빼놓은 이유: 데이터 베이스 생성 시 충돌 일어나서

# DB 연결
conn = mc.connect(**DB_CONFIG)
cursor = conn.cursor()

print("DB 서버 연결:", conn.is_connected())

# 데이터베이스 생성
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")

# 추출 칼럼
# stationName  대여소 이름
# rackTotCnt  거치대 수
# parkingBikeTotCnt  현재 자전거 수
# shared  이용률
# checkTime  수집 시간
# stationLatitude 위도
# stationLongitude 경도

# 테이블 생성 
cursor.execute('''
CREATE TABLE IF NOT EXISTS bike_data(
    id INT AUTO_INCREMENT PRIMARY KEY,
    stationId VARCHAR(20),
    stationName VARCHAR(100) comment '대여소 이름',
    rackTotCnt INT comment '거치대 수',
    parkingBikeTotCnt INT comment '현재 자전거 수',
    shared FLOAT comment '이용율',
    stationLatitude FLOAT comment '위도',
    stationLongitude FLOAT comment '경도',
    checkTime DATETIME comment '수집시간',
    UNIQUE KEY unique_data (stationId, checkTime)             
) charset=utf8mb4
''')    # 기본값이라 안해도 되지만 혹시 몰라서 명시

# api 호출
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/bikeList/1/1000"

response = requests.get(url)
data = response.json()

rows = data.get('rentBikeStatus', {}).get('row', [])   # rentBikeStatus : 데이터 이름

print(f"데이터 개수: {len(rows)}")

# 데이터 가공
data_list = []

for row in rows:
    try:
        data_list.append((
            row.get('stationId'),
            row.get('stationName'),
            int(row.get('rackTotCnt')),
            int(row.get('parkingBikeTotCnt')),
            float(row.get('shared')),
            float(row.get('stationLatitude')),
            float(row.get('stationLongitude')),
            datetime.now()
        ))
    except:
        continue

# DB저장 (중복 수집 방지)
insert_query = """
INSERT IGNORE INTO bike_data (
    stationId, stationName, rackTotCnt,
    parkingBikeTotCnt, shared,
    stationLatitude, stationLongitude, checkTime
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
"""

# executemany : 여러 개의 INSERT(또는 쿼리)를 한 번에 실행하는 함수 / 속도 빠름
cursor.executemany(insert_query, data_list)
conn.commit()

print(f"{len(data_list)}건 저장 완료!")

# 종료
cursor.close()
conn.close()
