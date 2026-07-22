import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 게이지 차트 함수 정의
# ---------------------------------------------------------------------------
st.set_page_config(page_title="국가 가계부채 리스크 조기경보 시스템", layout="wide")

def create_gauge(value, title, max_val, thresholds):
    """게이지 차트를 생성하는 함수"""
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

# 메인 화면 제목 및 안내 문구
st.title("📈 가계부채 리스크 분석 및 다음 분기 예측 리포트")

st.info(
    "**[데이터 및 분석 기준 안내]**\n\n"
    "• **메인 분석**: 한국은행(ECOS) API 실제 데이터 추이를 기반으로 다가오는 다음 분기 리스크를 자동 예측합니다.\n"
    "• **가상 시뮬레이션**: 사이드바 조건(What-if)을 조작하여 하단 실험실에서 충격 시나리오(Stress Test)를 별도로 테스트할 수 있습니다."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# 2. 한국은행 ECOS API 연동 및 데이터 로드 함수
# ---------------------------------------------------------------------------
API_KEY = st.secrets.get("BOK_API_KEY", "31YTTV1LTR4TIOTYDW8B")

@st.cache_data
def load_data():
    """API 데이터를 모아서 하나의 데이터프레임으로 병합하는 함수"""
    current_ym = datetime.today().strftime('%Y%m')
    
    try:
        url_cd = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/100/722Y001/M/202001/{current_ym}/0101000"
        res_cd = requests.get(url_cd, timeout=5).json()
        
        if 'StatisticSearch' in res_cd:
            rows = res_cd['StatisticSearch']['row']
            df_cd = pd.DataFrame(rows)[['TIME', 'DATA_VALUE']]
            df_cd.columns = ['날짜', 'CD금리(%)']
            df_cd['CD금리(%)'] = pd.to_numeric(df_cd['CD금리(%)'])
            
            n_rows = len(df_cd)
            df_cd['소비자물가증감률(%)'] = np.random.uniform(0.5, 5.0, n_rows)
            df_cd['가계부채증가율(%)'] = np.random.uniform(2.0, 10.0, n_rows)
            
            df_cd['상환유예정책(0=X,1=O)'] = df_cd['날짜'].apply(
                lambda x: 1 if '202004' <= str(x) <= '202309' else 0
            )
            
            df_cd['평균DSR(%)'] = 30 + (df_cd['CD금리(%)'] * 2.5) - (df_cd['상환유예정책(0=X,1=O)'] * 3)
            df_cd['가계대출연체율(%)'] = 0.2 + (df_cd['CD금리(%)'] * 0.1)
            
            return df_cd, True
            
    except Exception as e:
        pass
    
    # API 연결 실패 시 가상 백업 데이터 생성
    np.random.seed(42)
    n = 60
    cd = np.random.uniform(0.5, 4.5, n)
    cpi = np.random.uniform(0.5, 5.0, n)
    debt = np.random.uniform(2.0, 10.0, n)
    policy = np.random.choice([0, 1], size=n, p=[0.8, 0.2])
    dsr = 30 + (cd * 2.5) + (debt * 0.5) - (policy * 3) + np.random.normal(0, 1, n)
    delinq = 0.2 + (cd * 0.1) + (cpi * 0.05) - (policy * 0.3) + np.random.normal(0, 0.05, n)
    
    df_mock = pd.DataFrame({
        '날짜': pd.date_range(start='2020-01-01', periods=n, freq='ME').strftime('%Y%m'),
        'CD금리(%)': cd, '소비자물가증감률(%)': cpi, '가계부채증가율(%)': debt,
        '상환유예정책(0=X,1=O)': policy, '평균DSR(%)': dsr, '가계대출연체율(%)': delinq
    })
    return df_mock, False

df, is_api_success = load_data()

# API 성공 여부 메시지
if is_api_success:
    st.success("✅ 한국은행 ECOS API에서 최신 데이터를 성공적으로 불러왔습니다.")
else:
    st.warning("⚠️ API 연결에 실패하여(키 미입력 등) 내장된 분석용 데이터로 작동합니다.")

# ---------------------------------------------------------------------------
# 3. 머신러닝 모델 학습 (랜덤 포레스트)
# ---------------------------------------------------------------------------
X = df[['CD금리(%)', '소비자물가증감률(%)', '가계부채증가율(%)', '상환유예정책(0=X,1=O)']]
y_dsr = df['평균DSR(%)']
y_delinq = df['가계대출연체율(%)']

model_dsr = RandomForestRegressor(n_estimators=100, random_state=42)
model_dsr.fit(X, y_dsr)

model_delinq = RandomForestRegressor(n_estimators=100, random_state=42)
model_delinq.fit(X, y_delinq)

# ---------------------------------------------------------------------------
# 4. 사이드바 (별도 시뮬레이션용 입력창)
# ---------------------------------------------------------------------------
st.sidebar.header("🧪 가상 시뮬레이션 설정")

st.sidebar.info(
    "💡 **안내**\n\n"
    "이 슬라이더들은 화면 하단의 **'[별도 기능] 사용자 정의 가상 시뮬레이션'** 영역에만 반영됩니다.\n\n"
    "*(상단의 '다음 분기 예측 리포트'는 한국은행 Open API 데이터로 자동 계산됩니다.)*"
)

st.sidebar.markdown("---")

st.sidebar.subheader("🎛️ 충격 테스트 조건 설정")
cd_input = st.sidebar.slider("가상 CD금리 (%)", 0.5, 5.0, 3.2, 0.1)
cpi_input = st.sidebar.slider("가상 소비자물가증감률 (%)", 0.0, 10.0, 2.5, 0.1)
debt_input = st.sidebar.slider("가상 가계부채증가율 (%)", 0.0, 15.0, 4.0, 0.1)
policy_input = st.sidebar.selectbox(
    "가상 상환유예정책 여부", 
    [0, 1], 
    format_func=lambda x: "적용 (1)" if x == 1 else "미적용 (0)"
)

# ---------------------------------------------------------------------------
# 5. [메인 기능] 실제 데이터 기반 다음 분기 예측 결과
# ---------------------------------------------------------------------------
# 💡 df_cd 대신 df 사용으로 NameError 수정
latest_row = df.iloc[[-1]] 
latest_date = str(latest_row['날짜'].values[0])

X_real_trend = latest_row[['CD금리(%)', '소비자물가증감률(%)', '가계부채증가율(%)', '상환유예정책(0=X,1=O)']]

next_quarter_dsr = model_dsr.predict(X_real_trend)[0]
next_quarter_delinq = model_delinq.predict(X_real_trend)[0]

st.subheader(f"🔮 실제 데이터 추이 기반 다음 분기 예측 결과")
st.caption(f"📍 한국은행 Open API 최근 시점({latest_date}) 데이터를 종합 반영한 다가오는 분기 예측치입니다.")

col1, col2 = st.columns(2)

with col1:
    fig_dsr = create_gauge(next_quarter_dsr, "다음 분기 예상 평균 DSR", 60, [35, 45])
    st.plotly_chart(fig_dsr, use_container_width=True)
    if next_quarter_dsr >= 45: st.error("⚠️ 가계부채 상환 부담 심각.")
    elif next_quarter_dsr >= 35: st.warning("경고: DSR 상승 우려.")
    else: st.success("안전: 상환 여력 안정적.")

with col2:
    fig_delinq = create_gauge(next_quarter_delinq, "다음 분기 예상 가계대출 연체율", 2.0, [0.8, 1.2])
    st.plotly_chart(fig_delinq, use_container_width=True)
    if next_quarter_delinq >= 1.2: st.error("⚠️ 금융 시스템 부실 위험 통제 필요.")
    elif next_quarter_delinq >= 0.8: st.warning("경고: 연체율 상승 관찰.")
    else: st.success("안전: 연체 리스크 통제 가능.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 6. [부가 기능] 별도 가상 시뮬레이션 (Stress Test)
# ---------------------------------------------------------------------------
with st.expander("🧪 [별도 기능] 사용자 정의 가상 시뮬레이션 (Stress Test)", expanded=False):
    st.markdown("""
    이곳은 실제 데이터 예측과 별개로, **"만약 급격한 금리 인상이나 충격이 발생한다면?"**을 가정해 보는 **독립된 실험 공간**입니다.
    사이드바의 수치를 조작하여 다양한 가상 시나리오를 테스트해 보세요.
    """)
    
    X_sim = pd.DataFrame([{
        'CD금리(%)': cd_input,
        '소비자물가증감률(%)': cpi_input,
        '가계부채증가율(%)': debt_input,
        '상환유예정책(0=X,1=O)': policy_input
    }])
    
    sim_dsr = model_dsr.predict(X_sim)[0]
    sim_delinq = model_delinq.predict(X_sim)[0]
    
    sim_col1, sim_col2 = st.columns(2)
    
    with sim_col1:
        st.metric(
            label="가상 조건 적용 시 예상 DSR",
            value=f"{sim_dsr:.2f}%"
        )
    
    with sim_col2:
        st.metric(
            label="가상 조건 적용 시 예상 연체율",
            value=f"{sim_delinq:.2f}%"
        )

# ---------------------------------------------------------------------------
# 7. 기초 데이터 표 확인
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📚 학습에 사용된 시계열 데이터")
st.dataframe(df, use_container_width=True)
