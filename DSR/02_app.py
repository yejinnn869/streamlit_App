import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="금융 리스크 예측 & 관리 앱", layout="wide")

# ==========================================
# 1. ECOS API 연동 (데이터 호출 함수)
# ==========================================
# 주의: 실제 사용 시 본인의 ECOS API 키를 Streamlit Secrets에 저장해야 합니다.
ECOS_API_KEY = st.secrets["ECOS_API_KEY"]

def fetch_ecos_data():
    """
    한국은행 ECOS API에서 실시간 거시경제 지표(CD금리, 기준금리 등)를 가져오는 함수입니다.
    (현재는 앱이 바로 작동하도록 최신 평균값을 Mock Data로 구성했습니다. 
    실제 배포 시 requests.get() 주석을 해제하고 연동하세요.)
    """
    #실제 API 호출 코드 예시:
    url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10/060Y001/MM/202301/202312/0101000"
    response = requests.get(url).json()
    
    # 임시 최신 거시경제 데이터 (CD 91일물, 가계대출 연체율, 국가 평균 DSR 추정치)
    return {
        "current_cd_rate": 3.65,      # 현재 CD금리 (%)
        "current_nat_dsr": 40.5,      # 국가 평균 DSR (%)
        "current_nat_delinq": 0.38    # 가계대출 연체율 (%)
    }

# ==========================================
# 2. 예측 알고리즘 (1~6개월 뒤)
# ==========================================
def predict_indicators(base_rate, base_dsr, base_delinq, policy_level):
    """
    정부 정책 단계(0~3)와 현재 지표를 바탕으로 1~6개월 뒤의 값을 예측합니다.
    - policy_level (0: 지원 없음 ~ 3: 강력한 금융 지원 및 금리 인하 압박)
    """
    months = ["1개월 뒤", "2개월 뒤", "3개월 뒤", "4개월 뒤", "5개월 뒤", "6개월 뒤"]
    
    # 정책 단계에 따른 가중치 (단계가 높을수록 금리, DSR, 연체율 상승 억제)
    policy_effect_rate = policy_level * 0.05
    policy_effect_dsr = policy_level * 0.8
    policy_effect_delinq = policy_level * 0.02

    pred_rates = []
    pred_dsrs = []
    pred_delinqs = []

    for i in range(1, 7):
        # 시간 경과(i)에 따른 단순 추세 반영 + 정책 효과 차감 (간단한 시뮬레이션 모델)
        rate = base_rate + (i * 0.03) - policy_effect_rate
        dsr = base_dsr + (i * 0.2) - policy_effect_dsr
        delinq = base_delinq + (i * 0.015) - policy_effect_delinq
        
        pred_rates.append(round(max(rate, 1.0), 2)) # 금리 하한선 1.0%
        pred_dsrs.append(round(max(dsr, 0.0), 2))
        pred_delinqs.append(round(max(delinq, 0.0), 3))

    df_predict = pd.DataFrame({
        "기간": months,
        "예측 금리(%)": pred_rates,
        "예측 DSR(%)": pred_dsrs,
        "예측 연체율(%)": pred_delinqs
    })
    return df_predict

# ==========================================
# 3. 메인 UI 구성
# ==========================================
st.title("💡 개인 및 국가 금융 리스크 예측 시스템")
st.markdown("한국은행 ECOS 데이터를 기반으로 다양한 변수와 **정부 금융지원 정책**을 고려하여 6개월간의 재무 리스크를 예측합니다.")

# 사이드바: 정부 정책 변수 조절
st.sidebar.header("⚙️ 거시경제 변수 설정")
policy_level = st.sidebar.slider(
    "정부 금융지원 정책 수준 (0~3단계)", 
    min_value=0, max_value=3, value=1, step=1,
    help="0: 지원 없음 / 3: 대규모 정책 자금 투입 및 상환 유예 등 강력한 지원"
)

# 데이터 로드
ecos_data = fetch_ecos_data()

# 탭 생성: 1번(개인) / 2번(국가)
tab1, tab2 = st.tabs(["📊 1. 개인 재무 리포트", "🌐 2. 국가 거시 경제 리스크 예측"])

# ------------------------------------------
# 탭 1: 개인 재무 리포트
# ------------------------------------------
with tab1:
    st.subheader("개인 DSR 및 가계대출 연체 위험도 분석")
    st.write("본인의 소득과 대출 정보를 입력하면, 금리 변동에 따른 개인의 재무 부담을 예측해 드립니다.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        annual_income = st.number_input("연소득 (만원)", value=5000, step=100)
    with col2:
        total_loan = st.number_input("총 대출 잔액 (만원)", value=10000, step=100)
    with col3:
        my_interest_rate = st.number_input("현재 적용 금리 (%)", value=ecos_data['current_cd_rate'] + 1.5, step=0.1)

    # 간단한 개인 DSR 계산 (원리금 균등상환 가정 등락 반영)
    current_annual_repayment = total_loan * (my_interest_rate / 100) + (total_loan / 10) # 임시 상환액 산식
    personal_base_dsr = (current_annual_repayment / annual_income) * 100
    
    # 개인 연체 위험도 (DSR이 40%가 넘어가면 위험도 급증 가정)
    personal_base_delinq = max(0.1, (personal_base_dsr - 30) * 0.05) 

    # 예측 실행
    df_personal = predict_indicators(my_interest_rate, personal_base_dsr, personal_base_delinq, policy_level)
    
    st.markdown(f"**현재 추정 DSR:** `{personal_base_dsr:.1f}%` ｜ **정부 정책 적용:** `{policy_level}단계`")
    
    # 시각화 (Plotly)
    fig_personal = go.Figure()
    fig_personal.add_trace(go.Scatter(x=df_personal['기간'], y=df_personal['예측 DSR(%)'], mode='lines+markers', name='나의 DSR 예측'))
    fig_personal.add_trace(go.Bar(x=df_personal['기간'], y=df_personal['예측 연체율(%)'], name='나의 연체 위험도(%)', yaxis='y2', opacity=0.3))
    
    fig_personal.update_layout(
        title="향후 6개월 개인 DSR 및 연체 위험도 변화",
        yaxis=dict(title='DSR (%)'),
        yaxis2=dict(title='연체 위험도 (%)', overlaying='y', side='right'),
        hovermode="x unified"
    )
    st.plotly_chart(fig_personal, use_container_width=True)
    st.dataframe(df_personal, use_container_width=True)

# ------------------------------------------
# 탭 2: 국가 거시 경제 리스크 예측
# ------------------------------------------
with tab2:
    st.subheader("국가 단위 거시 지표 및 가계대출 연체율 예측")
    st.write(f"ECOS 기준 현재 CD금리 **{ecos_data['current_cd_rate']}%**, 국가 평균 DSR **{ecos_data['current_nat_dsr']}%** 기반 예측입니다.")
    
    # 예측 실행
    df_national = predict_indicators(ecos_data['current_cd_rate'], ecos_data['current_nat_dsr'], ecos_data['current_nat_delinq'], policy_level)
    
    # 시각화 (Plotly)
    fig_national = go.Figure()
    fig_national.add_trace(go.Scatter(x=df_national['기간'], y=df_national['예측 금리(%)'], mode='lines+markers', name='예측 시장 금리'))
    fig_national.add_trace(go.Scatter(x=df_national['기간'], y=df_national['예측 연체율(%)'], mode='lines+markers', name='가계대출 연체율(%)', yaxis='y2'))
    
    fig_national.update_layout(
        title="향후 6개월 국가 시장 금리 및 가계대출 연체율 변화",
        yaxis=dict(title='금리 / DSR (%)'),
        yaxis2=dict(title='연체율 (%)', overlaying='y', side='right'),
        hovermode="x unified"
    )
    st.plotly_chart(fig_national, use_container_width=True)
    
    # 요약 분석
    st.info(f"💡 **분석 결과**: 정부 정책이 {policy_level}단계로 시행될 경우, 6개월 뒤 국가 가계대출 연체율은 **{df_national['예측 연체율(%)'].iloc[-1]}%** 로 예상됩니다.")
    st.dataframe(df_national, use_container_width=True)
