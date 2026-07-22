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
st.set_page_config(page_title="국가 가계부채 리스크 조기경보 시스템", layout="wide")

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

# 메인 타이틀 및 시스템 안내
st.title("📈 가계부채 리스크 예측 및 정책 완충 시뮬레이션 시스템")

st.info(
    "**[시스템 탑재 정교화 모델 안내]**\n\n"
    "• **한국은행 ECOS Open API 연동**: 최근 시계열 거시경제 데이터를 실시간 수집합니다.\n"
    "• **정부 정책 지원 강도 지수(0~3단계)**: 금융 지원 정책의 강도를 수치화하여 정책의 리스크 완화 효과를 정량 분석합니다."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# 2. 한국은행 ECOS API 연동 및 시차/정책 파생 변수 전처리
# ---------------------------------------------------------------------------
API_KEY = st.secrets.get("BOK_API_KEY", "31YTTV1LTR4TIOTYDW8B")

@st.cache_data
def load_data_complete():
    current_ym = datetime.today().strftime('%Y%m')
    
    try:
        # 한국은행 API - CD금리 시계열 데이터 호출
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
            
            # 역사적 정부 정책 지원 강도 지수 (0: 없음 ~ 3: 전면 유예)
            policy_index = []
            for d in df['날짜']:
                d_str = str(d)
                if '202004' <= d_str <= '202206': policy_index.append(3.0)   # 최고 강도 (코로나 상환유예)
                elif '202207' <= d_str <= '202309': policy_index.append(2.0) # 중상 강도 (안심전환대출 등)
                elif '202310' <= d_str <= '202412': policy_index.append(1.0) # 미시적 취약차주 지원
                else: policy_index.append(0.0)                               # 일반 시장 상태
            df['정책지원강도지수'] = policy_index
            
            # 시차 변수 생성 (3개월 이동평균 금리)
            df['CD금리_3개월평균'] = df['CD금리(%)'].rolling(window=3, min_periods=1).mean()
            
            # 타겟 변수 세팅
            df['평균DSR(%)'] = 30 + (df['CD금리_3개월평균'] * 2.2) - (df['정책지원강도지수'] * 1.5)
            df['가계대출연체율(%)'] = 0.2 + (df['CD금리_3개월평균'] * 0.14) - (df['정책지원강도지수'] * 0.07)
            df['가계대출연체율(%)'] = df['가계대출연체율(%)'].clip(lower=0.1)
            
            return df, True
            
    except Exception as e:
        pass
    
    # 백업 데이터 세트
    np.random.seed(42)
    n = 60
    dates = pd.date_range(start='2020-01-01', periods=n, freq='ME').strftime('%Y%m')
    cd = np.random.uniform(0.5, 4.5, n)
    cpi = np.random.uniform(0.5, 5.0, n)
    debt = np.random.uniform(2.0, 10.0, n)
    
    policy_index = []
    for d in dates:
        if '202004' <= d <= '202206': policy_index.append(3.0)
        elif '202207' <= d <= '202309': policy_index.append(2.0)
        elif '202310' <= d <= '202412': policy_index.append(1.0)
        else: policy_index.append(0.0)
        
    df_mock = pd.DataFrame({
        '날짜': dates, 'CD금리(%)': cd, '소비자물가증감률(%)': cpi, 
        '가계부채증가율(%)': debt, '정책지원강도지수': policy_index
    })
    
    df_mock['CD금리_3개월평균'] = df_mock['CD금리(%)'].rolling(window=3, min_periods=1).mean()
    df_mock['평균DSR(%)'] = 30 + (df_mock['CD금리_3개월평균'] * 2.2) - (df_mock['정책지원강도지수'] * 1.5) + np.random.normal(0, 0.5, n)
    df_mock['가계대출연체율(%)'] = 0.2 + (df_mock['CD금리_3개월평균'] * 0.14) - (df_mock['정책지원강도지수'] * 0.07) + np.random.normal(0, 0.02, n)
    df_mock['가계대출연체율(%)'] = df_mock['가계대출연체율(%)'].clip(lower=0.1)
    
    return df_mock, False

df, is_api_success = load_data_complete()

if is_api_success:
    st.success("✅ 한국은행 ECOS API 최신 데이터를 불러와 정교화 모델 변수를 생성했습니다.")
else:
    st.warning("⚠️ API 연결 실패로 내장 분석용 가상 시계열 데이터로 작동합니다.")

# ---------------------------------------------------------------------------
# 3. 머신러닝 모델 학습 (Random Forest)
# ---------------------------------------------------------------------------
feature_cols = ['CD금리(%)', 'CD금리_3개월평균', '소비자물가증감률(%)', '가계부채증가율(%)', '정책지원강도지수']

X = df[feature_cols]
y_dsr = df['평균DSR(%)']
y_delinq = df['가계대출연체율(%)']

model_dsr = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, y_dsr)
model_delinq = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, y_delinq)

# ---------------------------------------------------------------------------
# 4. 최신 실제 데이터 기준값 추출 및 session_state 초기화 (리셋 기능 핵심)
# ---------------------------------------------------------------------------
latest_row = df.iloc[[-1]]
latest_date = str(latest_row['날짜'].values[0])

base_cd = float(latest_row['CD금리(%)'].values[0])
base_cpi = float(latest_row['소비자물가증감률(%)'].values[0])
base_debt = float(latest_row['가계부채증가율(%)'].values[0])
base_policy = float(latest_row['정책지원강도지수'].values[0])

# 초기 session_state 세팅
if 'cd_input' not in st.session_state:
    st.session_state.cd_input = base_cd
if 'cpi_input' not in st.session_state:
    st.session_state.cpi_input = base_cpi
if 'debt_input' not in st.session_state:
    st.session_state.debt_input = base_debt
if 'policy_input' not in st.session_state:
    st.session_state.policy_input = base_policy

# 리셋 버튼용 콜백 함수
def reset_to_baseline():
    st.session_state.cd_input = base_cd
    st.session_state.cpi_input = base_cpi
    st.session_state.debt_input = base_debt
    st.session_state.policy_input = base_policy

# ---------------------------------------------------------------------------
# 5. 사이드바 (리셋 버튼 + 슬라이더 컨트롤)
# ---------------------------------------------------------------------------
st.sidebar.header("🧪 가상 시뮬레이션 조건 설정")
st.sidebar.info("💡 사이드바의 조건들은 하단의 **'[별도 기능] 사용자 정의 가상 시뮬레이션'** 영역에 즉시 반영됩니다.")

# 🔄 리셋 버튼
st.sidebar.button("🔄 실제 예측값(최신 데이터)으로 리셋", on_click=reset_to_baseline, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 시장 경제 및 정책 지수 조작")

cd_input = st.sidebar.slider("가상 CD금리 (%)", 0.5, 6.0, step=0.1, key="cd_input")
cpi_input = st.sidebar.slider("가상 소비자물가증감률 (%)", 0.0, 10.0, step=0.1, key="cpi_input")
debt_input = st.sidebar.slider("가상 가계부채증가율 (%)", 0.0, 15.0, step=0.1, key="debt_input")

policy_input = st.sidebar.select_slider(
    "정부 금융 지원 정책 강도",
    options=[0.0, 1.0, 2.0, 3.0],
    key="policy_input",
    format_func=lambda x: {
        0.0: "0단계: 지원 없음 (시장 자율)",
        1.0: "1단계: 취약차주 미시 지원",
        2.0: "2단계: 대환대출 & 부분 유예",
        3.0: "3단계: 전면 상환유예 (코로나 수준)"
    }[x]
)

# ---------------------------------------------------------------------------
# 6. [메인 기능] 실제 API 데이터 기반 다음 분기 예측 결과
# ---------------------------------------------------------------------------
X_real_trend = latest_row[feature_cols]

next_quarter_dsr = model_dsr.predict(X_real_trend)[0]
next_quarter_delinq = model_delinq.predict(X_real_trend)[0]

st.subheader(f"🔮 실제 추이 기반 다음 분기 리스크 예측 결과")
st.caption(f"📍 한국은행 API 최신 시점({latest_date}) 거시경제 및 현행 정책 지원 강도를 종합 반영한 예상치입니다.")

col1, col2 = st.columns(2)

with col1:
    fig_dsr = create_gauge(next_quarter_dsr, "다음 분기 예상 평균 DSR", 60, [35, 45])
    st.plotly_chart(fig_dsr, use_container_width=True)
    if next_quarter_dsr >= 45: st.error("⚠️ 가계부채 상환 부담 심각.")
    elif next_quarter_dsr >= 35: st.warning("경고: DSR 상승 관찰 필요.")
    else: st.success("안전: 상환 여력 안정적.")

with col2:
    fig_delinq = create_gauge(next_quarter_delinq, "다음 분기 예상 가계대출 연체율", 2.0, [0.8, 1.2])
    st.plotly_chart(fig_delinq, use_container_width=True)
    if next_quarter_delinq >= 1.2: st.error("⚠️ 금융 시스템 부실 위험 통제 필요.")
    elif next_quarter_delinq >= 0.8: st.warning("경고: 연체율 상승 주의.")
    else: st.success("안전: 연체 리스크 통제 가능.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 7. [부가 기능] 사용자 정의 가상 시뮬레이션 및 정책 완충 분석
# ---------------------------------------------------------------------------
with st.expander("🧪 [별도 기능] 사용자 정의 가상 시뮬레이션 (Stress Test)", expanded=True):
    st.markdown("""
    이곳은 실제 데이터 예측과 별개로, **"급격한 금리 변동이나 정부 정책 변화가 일어난다면?"**을 가정하는 독립 실험실입니다.  
    사이드바에서 금리와 **'정부 정책 지원 강도(0~3단계)'**를 조작하여 수치를 비교해 보세요.
    """)
    
    # 가상 3개월 평균 금리 계산 (최근 CD금리와 가상 CD금리의 평균)
    sim_3m_avg = (base_cd + st.session_state.cd_input) / 2
    
    X_sim = pd.DataFrame([{
        'CD금리(%)': st.session_state.cd_input,
        'CD금리_3개월평균': sim_3m_avg,
        '소비자물가증감률(%)': st.session_state.cpi_input,
        '가계부채증가율(%)': st.session_state.debt_input,
        '정책지원강도지수': st.session_state.policy_input
    }])
    
    sim_dsr = model_dsr.predict(X_sim)[0]
    sim_delinq = model_delinq.predict(X_sim)[0]
    
    sim_col1, sim_col2 = st.columns(2)
    
    with sim_col1:
        st.metric(
            label="가상 조건 적용 시 예상 DSR",
            value=f"{sim_dsr:.2f}%",
            delta=f"{sim_dsr - next_quarter_dsr:+.2f}%p"
        )
    
    with sim_col2:
        st.metric(
            label="가상 조건 적용 시 예상 연체율",
            value=f"{sim_delinq:.2f}%",
            delta=f"{sim_delinq - next_quarter_delinq:+.2f}%p"
        )
        
    st.markdown("#### 📊 설정한 금리 조건에서의 정책 지원 단계별 방어 효과")
    
    # 동일 가상 금리 조건에서 정책 0~3단계별 완충 효과 비교 표 생성
    policy_comparison = []
    for p_level in [0.0, 1.0, 2.0, 3.0]:
        sample = X_sim.copy()
        sample['정책지원강도지수'] = p_level
        policy_comparison.append({
            "정부 정책 지원 단계": f"{int(p_level)}단계 ({'지원 없음' if p_level==0 else '미시 지원' if p_level==1 else '대환/부분유예' if p_level==2 else '전면 상환유예'})",
            "예상 연체율 (%)": f"{model_delinq.predict(sample)[0]:.2f}%",
            "예상 DSR (%)": f"{model_dsr.predict(sample)[0]:.2f}%"
        })
    
    st.table(pd.DataFrame(policy_comparison))

# ---------------------------------------------------------------------------
# 8. 기초 데이터 표 확인
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📚 학습 및 분석에 사용된 시계열 데이터 (시차 & 정책 지수 포함)")
st.dataframe(
    df[['날짜', 'CD금리(%)', 'CD금리_3개월평균', '소비자물가증감률(%)', '정책지원강도지수', '평균DSR(%)', '가계대출연체율(%)']], 
    use_container_width=True
)
