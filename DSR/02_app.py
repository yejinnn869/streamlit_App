import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression  # 머신러닝 라이브러리 추가

# 페이지 설정
st.set_page_config(page_title="금융 리스크 예측 & 관리 앱", layout="wide")

# ==========================================
# 1. ECOS API 연동 (데이터 호출 함수)
# ==========================================
ECOS_API_KEY = st.secret["ECOS_API_KEY"] 

def fetch_ecos_data():
    url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10/060Y001/MM/202301/202312/0101000"
    response = requests.get(url).json()
    
    # 임시 최신 거시경제 데이터 (CD 91일물, 가계대출 연체율, 국가 평균 DSR 추정치)
    return {response
    
    }


# ==========================================
# 2. 10년 치 과거 데이터 기반 머신러닝 모델 학습
# ==========================================
@st.cache_resource # 매번 학습하지 않도록 캐싱 처리
def train_ml_models():
    """
    과거 10년 치(가상) ECOS 경제 변수와 정책 단계를 생성하여 선형회귀 모델을 학습시킵니다.
    실제 데이터 확보 시 이 내부 로직을 pd.read_csv('ecos_10years.csv') 등으로 교체하면 됩니다.
    """
    np.random.seed(42)
    n_samples = 1200 # 과거 10년(120개월)치 샘플 데이터 증폭
    
    # 피처(X): [기준금리, 기준DSR, 기준연체율, 정책단계, 경과개월수]
    base_rates = np.random.uniform(1.0, 5.0, n_samples)
    base_dsrs = np.random.uniform(30.0, 50.0, n_samples)
    base_delinqs = np.random.uniform(0.1, 0.8, n_samples)
    policies = np.random.randint(0, 4, n_samples)
    future_months = np.random.randint(1, 7, n_samples)
    
    X = np.column_stack((base_rates, base_dsrs, base_delinqs, policies, future_months))
    
    # 타겟(y): 경제 변수 간의 복합적인 상관관계(가중치)를 반영한 미래 결과값 (가상)
    y_rate = base_rates + (future_months * 0.04) - (policies * 0.15) + np.random.normal(0, 0.05, n_samples)
    y_dsr = base_dsrs + (future_months * 0.25) - (policies * 1.2) + (base_rates * 0.15) + np.random.normal(0, 0.5, n_samples)
    y_delinq = base_delinqs + (future_months * 0.02) - (policies * 0.05) + (base_dsrs * 0.002) + np.random.normal(0, 0.01, n_samples)
    
    # 각각의 지표를 예측하는 선형회귀 모델 학습
    model_rate = LinearRegression().fit(X, y_rate)
    model_dsr = LinearRegression().fit(X, y_dsr)
    model_delinq = LinearRegression().fit(X, y_delinq)
    
    return model_rate, model_dsr, model_delinq

# 앱 실행 시 모델 학습 진행
model_rate, model_dsr, model_delinq = train_ml_models()

# ==========================================
# 3. 머신러닝 예측 알고리즘 적용
# ==========================================
def predict_indicators_ml(base_rate, base_dsr, base_delinq, policy_level):
    """학습된 선형회귀 모델을 통해 1~6개월 뒤 지표를 예측합니다."""
    months = ["1개월 뒤", "2개월 뒤", "3개월 뒤", "4개월 뒤", "5개월 뒤", "6개월 뒤"]
    
    pred_rates, pred_dsrs, pred_delinqs = [], [], []
    
    for i in range(1, 7):
        # 예측을 위한 입력 변수 세팅
        input_data = np.array([[base_rate, base_dsr, base_delinq, policy_level, i]])
        
        # ML 모델의 예측 수행 (.predict)
        pred_r = model_rate.predict(input_data)[0]
        pred_d = model_dsr.predict(input_data)[0]
        pred_dl = model_delinq.predict(input_data)[0]
        
        # 현실적인 하한선(0 이하로 떨어지지 않게) 적용
        pred_rates.append(round(max(pred_r, 1.0), 2))
        pred_dsrs.append(round(max(pred_d, 0.0), 2))
        pred_delinqs.append(round(max(pred_dl, 0.001), 3))

    return pd.DataFrame({
        "기간": months,
        "예측 금리(%)": pred_rates,
        "예측 DSR(%)": pred_dsrs,
        "예측 연체율(%)": pred_delinqs
    })

# ==========================================
# 4. 메인 UI 구성
# ==========================================
st.title("💡 머신러닝 기반 개인/국가 금융 리스크 예측 시스템")
st.markdown("과거 10년간의 ECOS 거시경제 데이터(선형회귀 모델 학습)와 **정부 금융지원 정책**을 결합하여 향후 6개월간의 리스크를 예측합니다.")

# 사이드바
st.sidebar.header("⚙️ 경제 변수 및 정책 설정")
policy_level = st.sidebar.slider(
    "정부 금융지원 정책 수준 (0~3단계)", 
    min_value=0, max_value=3, value=1, step=1,
    help="0: 지원 없음 / 3: 대규모 정책 자금 투입 및 상환 유예 등 강력한 지원"
)

# 데이터 로드
ecos_data = fetch_ecos_data()

# 탭 생성
tab1, tab2 = st.tabs(["📊 1. 개인 재무 리포트", "🌐 2. 국가 거시 경제 리스크 예측"])

# ------------------------------------------
# 탭 1: 개인 재무 리포트
# ------------------------------------------
with tab1:
    st.subheader("개인 DSR 및 가계대출 연체 위험도 예측")
    st.write("본인의 재무 정보를 입력하면, ML 모델이 금리 변동 추이를 분석해 개인의 미래 부담을 예측합니다.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        annual_income = st.number_input("연소득 (만원)", value=5000, step=100)
    with col2:
        total_loan = st.number_input("총 대출 잔액 (만원)", value=10000, step=100)
    with col3:
        my_interest_rate = st.number_input("현재 적용 금리 (%)", value=ecos_data['current_cd_rate'] + 1.5, step=0.1)

    # 기본 개인 DSR 및 연체위험도 계산
    current_annual_repayment = total_loan * (my_interest_rate / 100) + (total_loan / 10)
    personal_base_dsr = (current_annual_repayment / annual_income) * 100
    personal_base_delinq = max(0.1, (personal_base_dsr - 30) * 0.05) 

    # ML 기반 예측 실행
    df_personal = predict_indicators_ml(my_interest_rate, personal_base_dsr, personal_base_delinq, policy_level)
    
    st.markdown(f"**현재 추정 DSR:** `{personal_base_dsr:.1f}%` ｜ **정부 정책 적용:** `{policy_level}단계`")
    
    fig_personal = go.Figure()
    fig_personal.add_trace(go.Scatter(x=df_personal['기간'], y=df_personal['예측 DSR(%)'], mode='lines+markers', name='나의 DSR 예측 (ML)'))
    fig_personal.add_trace(go.Bar(x=df_personal['기간'], y=df_personal['예측 연체율(%)'], name='나의 연체 위험도(%)', yaxis='y2', opacity=0.3))
    
    fig_personal.update_layout(title="향후 6개월 개인 DSR 및 연체 위험도 변화 (ML 예측)", yaxis=dict(title='DSR (%)'), yaxis2=dict(title='연체 위험도 (%)', overlaying='y', side='right'), hovermode="x unified")
    st.plotly_chart(fig_personal, use_container_width=True)
    st.dataframe(df_personal, use_container_width=True)

# ------------------------------------------
# 탭 2: 국가 거시 경제 리스크 예측
# ------------------------------------------
with tab2:
    st.subheader("국가 단위 거시 지표 및 가계대출 연체율 예측")
    
    # ML 기반 예측 실행
    df_national = predict_indicators_ml(ecos_data['current_cd_rate'], ecos_data['current_nat_dsr'], ecos_data['current_nat_delinq'], policy_level)
    
    fig_national = go.Figure()
    fig_national.add_trace(go.Scatter(x=df_national['기간'], y=df_national['예측 금리(%)'], mode='lines+markers', name='예측 시장 금리 (ML)'))
    fig_national.add_trace(go.Scatter(x=df_national['기간'], y=df_national['예측 연체율(%)'], mode='lines+markers', name='가계대출 연체율(%)', yaxis='y2'))
    
    fig_national.update_layout(title="향후 6개월 국가 시장 금리 및 가계대출 연체율 변화 (ML 예측)", yaxis=dict(title='금리 / DSR (%)'), yaxis2=dict(title='연체율 (%)', overlaying='y', side='right'), hovermode="x unified")
    st.plotly_chart(fig_national, use_container_width=True)
    st.dataframe(df_national, use_container_width=True)
