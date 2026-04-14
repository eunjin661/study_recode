import pandas as pd
import numpy as np

def run_preprocessing_pipeline(filepath):
    '''filepath : cvs 파일명'''
    # 데이터 로드
    try:
        df = pd.read_csv(filepath,encoding='utf-8')
    except UnicodeDecodeError as e:
        df = pd.read_csv(filepath,encoding='cp949')
    # 결측치 처리 (대치)
    # age salary 중앙값
    df['age'] = df['age'].fillna(df['age'].median())
    df['salary'] = df['salary'].fillna(df['salary'].median())
    # score 선형보간 하고 양끝에 남은 nan은 앞뒤 값으로 채움
    df['score'] = df['score'].interpolate(method='linear')
    df['score'] = df['score'].bfill().ffill()
    # 이상치 처리 capping (경계값으로 이상치 대치)
    numeric_cols = ['age','salary','score']
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - IQR * 1.5
        upper = Q3 + IQR * 1.5
        df[col] = df[col].clip(lower=lower,upper=upper)
    # 중복 데이터
    df = df.drop_duplicates(keep='first')
    # 종료
    print(f'파이프라인 종료')
    print(f'shape = {df.shape}')
    return df

if __name__ == "__main__":
    filepath = 'pandsa/dffect/data/messy_data.csv'
    clean_df = run_preprocessing_pipeline(filepath)
    clean_df.to_csv('pandsa/data/clean_data.csv',encoding='utf-8')
    print('데이터 저장완료')
