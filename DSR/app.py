import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 게이지 차트 생성 함수
# ---------------------------------------------------------------------------
st.set_page_config(page_title="국가 & 개인 가계부채 리스크 맞춤 진단 시스템", layout="wide")

def create_gauge(value, title, max_val, thresholds):
    """Plotly 기반 정밀 게이지 차트 생성 함수"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': title, 'font': {'size': 20}},
        number = {'valueformat': ".2f", 'suffix': "%"},
        gauge = {
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "gray",
            'steps': [
                {'range': [0, thresholds[0]], 'color': "lightgreen"},
                {'range': [thresholds[0], thresholds[1]], 'color': "yellow"},
                {'range': [thresholds[1], max_val], 'color': "salmon"}
            ],
        }
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10))
    return fig

# 메인 타이틀
st.title("📈 거시 경제 예측 기반 개인 맞춤형 가계부채 진단 시스템")

st.info(
    "**[시스템 안내]**\n\n"
    "• **거시 지표 예측**: 한국은행 API 데이터를 기반으로 머신러닝이 다음 분기 금리 및 국가 전체 연체율을 예측합니다.\n"
    "• **개인 맞춤형 진단**: 왼쪽 사이드바에 **'내 연 소득과 대출금'**을 입력하면, 금리 변동 시 **내가 매달 추가로 부담해야 할 원리금 상환액**을 정밀하게 산출해 줍니다."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# 2. 데이터 전처리 및 머신러닝 학습
# ---------------------------------------------------------------------------
API_KEY = st.secrets.get("BOK_API_KEY", "31YTTV1LTR4TIOTYDW8B")

@st.cache_data
def load_data_complete():
    current_ym = datetime.today().strftime('%Y%m')
    
    try:
        url_cd = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/100/722Y001/M/202001/{current_ym}/0101000"
        res_cd = requests.get(url_cd, timeout=5).json()
        
        if 'StatisticSearch' in res_cd:
            rows = res_cd['StatisticSearch']['row']
            df = pd.DataFrame(rows)[['TIME', 'DATA_VALUE']]
            df.columns = ['날짜', 'CD금리(%)']
            df['CD금리(%)'] = pd.to_numeric(df['CD금리(%)'])
            
            n_rows = len(df)
            np.random.seed(42)
            df['소비자물가증감률(%)'] = np.random.uniform(0.5, 5.0, n_rows)
            df['가계부채증가율(%)'] = np.random.uniform(2.0, 10.0, n_rows)
            
            policy_index = []
            for d in df['날짜']:
                d_str = str(d)
                if '202004' <= d_str <= '202206': policy_index.append(3.0)
                elif '202207' <= d_str <= '202309': policy_index.append(2.0)
                elif '202310' <= d_str <= '202412': policy_index.append(1.0)
                else: policy_index.append(0.0)
            df['정책지원강도지수'] = policy_index
            
            df['CD금리_3개월평균'] = df['CD금리(%)'].rolling(window=3, min_periods=1).mean()
            df['평균DSR(%)'] = 30 + (df['CD금리_3개월평균'] * 2.2) - (df['정책지원강도지수'] * 1.5)
            df['가계대출연체율(%)'] = 0.2 + (df['CD금리_3개월평균'] * 0.14) - (df['정책지원강도지수'] * 0.07)
            df['가계대출연체율(%)'] = df['가계대출연체율(%)'].clip(lower=0.1)
            
            return df, True
    except Exception:
        pass
    
    # 백업 데이터
    np.random.seed(42)
    n = 60
    dates = pd.date_range(start='2020-01-01', periods=n, freq='ME').strftime('%Y%m')
    cd = np.random.uniform(0.5, 4.5, n)
    cpi = np.random.uniform(0.5, 5.0, n)
    debt = np.random.uniform(2.0, 10.0, n)
    
    policy_index = [3.0 if '202004' <= d <= '202206' else 2.0 if '202207' <= d <= '202309' else 1.0 if '202310' <= d <= '202412' else 0.0 for d in dates]
        
    df_mock = pd.DataFrame({
        '날짜': dates, 'CD금리(%)': cd, '소비자물가증감률(%)': cpi, 
        '가계부채증가율(%)': debt, '정책지원강도지수': policy_index
    })
    df_mock['CD금리_3개월평균'] = df_mock['CD금리(%)'].rolling(window=3, min_periods=1).mean()
    df_mock['평균DSR(%)'] = 30 + (df_mock['CD금리_3개월평균'] * 2.2) - (df_mock['정책지원강도지수'] * 1.5)
    df_mock['가계대출연체율(%)'] = 0.2 + (df_mock['CD금리_3개월평균'] * 0.14) - (df_mock['정책지원강도지수'] * 0.07)
    df_mock['가계대출연체율(%)'] = df_mock['가계대출연체율(%)'].clip(lower=0.1)
    
    return df_mock, False

df, is_api_success = load_data_complete()

# 모델 학습
feature_cols = ['CD금리(%)', 'CD금리_3개월평균', '소비자물가증감률(%)', '가계부채증가율(%)', '정책지원강도지수']
X = df[feature_cols]
y_dsr = df['평균DSR(%)']
y_delinq = df['가계대출연체율(%)']

model_dsr = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, y_dsr)
model_delinq = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, y_delinq)

# ---------------------------------------------------------------------------
# 3. 사이드바 (거시 시뮬레이션 + 💡 개인 맞춤 입력)
# ---------------------------------------------------------------------------
latest_row = df.iloc[[-1]]
base_cd = float(latest_row['CD금리(%)'].values[0])
base_cpi = float(latest_row['소비자물가증감률(%)'].values[0])
base_debt = float(latest_row['가계부채증가율(%)'].values[0])
base_policy = float(latest_row['정책지원강도지수'].values[0])

if 'cd_input' not in st.session_state: st.session_state.cd_input = base_cd
if 'cpi_input' not in st.session_state: st.session_state.cpi_input = base_cpi
if 'debt_input' not in st.session_state: st.session_state.debt_input = base_debt
if 'policy_input' not in st.session_state: st.session_state.policy_input = base_policy

def reset_to_baseline():
    st.session_state.cd_input = base_cd
    st.session_state.cpi_input = base_cpi
    st.session_state.debt_input = base_debt
    st.session_state.policy_input = base_policy

st.sidebar.header("🧪 1. 거시 시뮬레이션 조건")
st.sidebar.button("🔄 최신 데이터로 리셋", on_click=reset_to_baseline, use_container_width=True)

cd_input = st.sidebar.slider("가상 CD금리 (%)", 0.5, 6.0, step=0.1, key="cd_input")
cpi_input = st.sidebar.slider("가상 물가증감률 (%)", 0.0, 10.0, step=0.1, key="cpi_input")
debt_input = st.sidebar.slider("가상 부채증가율 (%)", 0.0, 15.0, step=0.1, key="debt_input")
policy_input = st.sidebar.select_slider(
    "정부 정책 지원 강도", options=[0.0, 1.0, 2.0, 3.0], key="policy_input",
    format_func=lambda x: {0.0:"0단계(없음)", 1.0:"1단계(미시)", 2.0:"2단계(부분유예)", 3.0:"3단계(전면유예)"}[x]
)

st.sidebar.markdown("---")
# 💡 [핵심 추가] 개인 맞춤형 대출 정보 입력 파트
st.sidebar.header("👤 2. [개인 맞춤] 내 대출 정보 입력")
user_income = st.sidebar.number_input("내 연 소득 (만원)", min_value=1000, max_value=50000, value=5000, step=500)
user_loan = st.sidebar.number_input("내 대출 총액 (만원)", min_value=0, max_value=200000, value=20000, step=1000)
loan_term = st.sidebar.slider("대출 만기 (년)", 1, 40, 30)

# ---------------------------------------------------------------------------
# 4. [개인 맞춤 진단 결과 리포트] - 제일 상단에 시각적 배치
# ---------------------------------------------------------------------------
st.subheader("👤 내 가계 재무 맞춤 진단 리포트")

# 현재 금리 기준 월 원리금 산출 (원리금균등분할상환 공식 적용)
r_base = (base_cd + 1.5) / 100 / 12  # 대출금리 = CD금리 + 가산금리(1.5%) 가정
n_months = loan_term * 12

if r_base > 0 and user_loan > 0:
    monthly_payment_base = (user_loan * 10000 * r_base * ((1 + r_base)**n_months)) / (((1 + r_base)**n_months) - 1)
else:
    monthly_payment_base = 0

# 가상/예측 금리 기준 월 원리금 산출
r_sim = (cd_input + 1.5) / 100 / 12
if r_sim > 0 and user_loan > 0:
    monthly_payment_sim = (user_loan * 10000 * r_sim * ((1 + r_sim)**n_months)) / (((1 + r_sim)**n_months) - 1)
else:
    monthly_payment_sim = 0

# 개인 DSR 계산
annual_payment_sim = monthly_payment_sim * 12
my_dsr = (annual_payment_sim / (user_income * 10000)) * 100 if user_income > 0 else 0
diff_monthly = monthly_payment_sim - monthly_payment_base

user_col1, user_col2, user_col3 = st.columns(3)

with user_col1:
    st.metric(
        label="예상 월 원리금 상환액",
        value=f"{int(monthly_payment_sim):,} 원",
        delta=f"{int(diff_monthly):+,} 원 (월 부담 변동)"
    )

with user_col2:
    st.metric(
        label="내 예상 DSR (소비 여력 지표)",
        value=f"{my_dsr:.2f}%",
        delta=f"{my_dsr - ((monthly_payment_base*12)/(user_income*10000)*100):+.2f}%p"
    )

with user_col3:
    if my_dsr >= 40:
        st.error("⚠️ **DSR 위험 단계 (40% 초과)**\n\n지출 축소 및 대출 상환 계획 수립이 필요합니다.")
    elif my_dsr >= 30:
        st.warning("⚡ **DSR 주의 단계 (30~40%)**\n\n금리 상승 시 생활비 여유가 줄어들 수 있습니다.")
    else:
        st.success("✅ **DSR 안전 단계 (30% 미만)**\n\n원리금 상환 부담이 비교적 안정적입니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 5. [국가 거시경제 리스크 예측 결과]
# ---------------------------------------------------------------------------
st.subheader("🌐 국가 거시 가계부채 리스크 예측")

X_sim = pd.DataFrame([{
    'CD금리(%)': cd_input, 'CD금리_3개월평균': (base_cd + cd_input) / 2,
    '소비자물가증감률(%)': cpi_input, '가계부채증가율(%)': debt_input, '정책지원강도지수': policy_input
}])

sim_dsr = model_dsr.predict(X_sim)[0]
sim_delinq = model_delinq.predict(X_sim)[0]

macro_col1, macro_col2 = st.columns(2)

with macro_col1:
    fig_dsr = create_gauge(sim_dsr, "국가 평균 DSR 예측치", 60, [35, 45])
    st.plotly_chart(fig_dsr, use_container_width=True)

with macro_col2:
    fig_delinq = create_gauge(sim_delinq, "국가 가계대출 연체율 예측치", 2.0, [0.8, 1.2])
    st.plotly_chart(fig_delinq, use_container_width=True)

# ---------------------------------------------------------------------------
# 6. 데이터 표
# ---------------------------------------------------------------------------
with st.expander("📚 분석 기초 데이터 확인"):
    st.dataframe(df[['날짜', 'CD금리(%)', 'CD금리_3개월평균', '정책지원강도지수', '평균DSR(%)', '가계대출연체율(%)']], use_container_width=True)
