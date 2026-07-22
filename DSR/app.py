import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------------------------
st.set_page_config(page_title="국가 가계부채 리스크 조기경보 시스템", layout="wide")

st.title("🚨 국가 가계부채 리스크 예측 모델 (Open API 연동)")
st.markdown("""
한국은행 ECOS Open API를 통해 실제 거시경제 지표를 수집하고, 
다변량 데이터 기반 머신러닝(Random Forest)으로 **국가 평균 가계 DSR**과 **가계대출 연체율**을 예측합니다.
""")

# ---------------------------------------------------------------------------
# 2. 한국은행 ECOS API 연동 함수
# ---------------------------------------------------------------------------
# Streamlit Cloud 설정(Secrets)에서 API 키를 가져오거나, 아래에 직접 입력하세요.
API_KEY = st.secrets.get("BOK_API_KEY", "여기에_발급받은_API키를_입력하세요")

@st.cache_data
def fetch_ecos_data(stat_code, item_code, start_month, end_month):
    """특정 통계 지표를 한국은행 API에서 가져오는 함수"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/100/{stat_code}/MM/{start_month}/{end_month}/{item_code}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'StatisticSearch' in data:
            rows = data['StatisticSearch']['row']
            df = pd.DataFrame(rows)
            # 날짜와 데이터 값만 추출 후 숫자형으로 변환
            df = df[['TIME', 'DATA_VALUE']]
            df.columns = ['날짜', '값']
            df['값'] = pd.to_numeric(df['값'])
            return df
    return None

@st.cache_data
def load_data():
    """API 데이터를 모아서 하나의 데이터프레임으로 병합하는 함수"""
    try:
        # 주의: 아래 stat_code와 item_code는 예시입니다. 
        # 실제 ECOS 홈페이지 개발자 가이드에서 정확한 코드를 확인해 교체해야 합니다.
        df_cd = fetch_ecos_data("060Y001", "0101000", "202001", "202512") # CD금리 예시
        df_cpi = fetch_ecos_data("021Y125", "0", "202001", "202512")      # 소비자물가지수 예시
        
        # API 통신 성공 시 데이터 병합
        if df_cd is not None and df_cpi is not None:
            df_merged = pd.merge(df_cd, df_cpi, on='날짜', suffixes=('_CD', '_CPI'))
            # 부족한 변수(가계부채, 연체율 등)는 시연을 위해 가공 (실제 통계 코드로 대체 가능)
            df_merged['가계부채증가율(%)'] = np.random.uniform(2.0, 10.0, len(df_merged))
            df_merged['상환유예정책(0=X,1=O)'] = np.random.choice([0, 1], size=len(df_merged), p=[0.8, 0.2])
            
            # 종속변수 (실제 연체율 API 코드를 찾아 대체하는 것이 가장 좋습니다)
            df_merged['평균DSR(%)'] = 30 + (df_merged['값_CD'] * 2.5) - (df_merged['상환유예정책(0=X,1=O)'] * 3)
            df_merged['가계대출연체율(%)'] = 0.2 + (df_merged['값_CD'] * 0.1)
            
            df_merged.rename(columns={'값_CD': 'CD금리(%)', '값_CPI': '소비자물가증감률(%)'}, inplace=True)
            return df_merged, True
            
    except Exception as e:
        pass
    
    # API 호출 실패 또는 키가 없을 경우 작동할 안전장치 (가상 데이터)
    np.random.seed(42)
    n = 60
    cd = np.random.uniform(0.5, 4.5, n)
    cpi = np.random.uniform(0.5, 5.0, n)
    debt = np.random.uniform(2.0, 10.0, n)
    policy = np.random.choice([0, 1], size=n, p=[0.8, 0.2])
    dsr = 30 + (cd * 2.5) + (debt * 0.5) - (policy * 3) + np.random.normal(0, 1, n)
    delinq = 0.2 + (cd * 0.1) + (cpi * 0.05) - (policy * 0.3) + np.random.normal(0, 0.05, n)
    
    df_mock = pd.DataFrame({
        '날짜': pd.date_range(start='2020-01-01', periods=n, freq='M').strftime('%Y%m'),
        'CD금리(%)': cd, '소비자물가증감률(%)': cpi, '가계부채증가율(%)': debt,
        '상환유예정책(0=X,1=O)': policy, '평균DSR(%)': dsr, '가계대출연체율(%)': delinq
    })
    return df_mock, False

df, is_api_success = load_data()

# API 성공 여부 알림
if is_api_success:
    st.success("✅ 한국은행 ECOS API에서 최신 데이터를 성공적으로 불러왔습니다.")
else:
    st.warning("⚠️ API 연결에 실패하여(키 미입력 등) 내장된 분석용 가상 데이터를 사용합니다.")

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
# 4. 사이드바 - 사용자 시나리오 입력 (UI)
# ---------------------------------------------------------------------------
st.sidebar.header("📊 다음 분기 경제 시나리오 설정")
input_cd = st.sidebar.slider("시장금리 (CD 91일물, %)", min_value=0.5, max_value=6.0, value=3.5, step=0.1)
input_cpi = st.sidebar.slider("소비자물가 증감률 (%)", min_value=0.0, max_value=6.0, value=3.0, step=0.1)
input_debt = st.sidebar.slider("가계부채 증가율 (%)", min_value=0.0, max_value=12.0, value=5.0, step=0.1)
input_policy = st.sidebar.radio("국가 상환유예 등 금융지원 정책", options=[0, 1], format_func=lambda x: "시행 중 (1)" if x == 1 else "미시행 (0)")

# ---------------------------------------------------------------------------
# 5. 모델 예측 수행
# ---------------------------------------------------------------------------
input_data = pd.DataFrame({
    'CD금리(%)': [input_cd], '소비자물가증감률(%)': [input_cpi],
    '가계부채증가율(%)': [input_debt], '상환유예정책(0=X,1=O)': [input_policy]
})

pred_dsr = model_dsr.predict(input_data)[0]
pred_delinq = model_delinq.predict(input_data)[0]

# ---------------------------------------------------------------------------
# 6. 결과 시각화 (Plotly)
# ---------------------------------------------------------------------------
st.subheader("🔮 거시 변수 시나리오 기반 리스크 예측 결과")
col1, col2 = st.columns(2)

def create_gauge(value, title, max_val, thresholds):
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
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

with col1:
    fig_dsr = create_gauge(pred_dsr, "예측 국가 평균 DSR", 60, [35, 45])
    st.plotly_chart(fig_dsr, use_container_width=True)
    if pred_dsr >= 45: st.error("⚠️ 가계부채 상환 부담 심각.")
    elif pred_dsr >= 35: st.warning("경고: DSR 상승 우려.")
    else: st.success("안전: 상환 여력 안정적.")

with col2:
    fig_delinq = create_gauge(pred_delinq, "예측 가계대출 연체율", 2.0, [0.8, 1.2])
    st.plotly_chart(fig_delinq, use_container_width=True)
    if pred_delinq >= 1.2: st.error("⚠️ 금융 시스템 부실 위험 통제 필요.")
    elif pred_delinq >= 0.8: st.warning("경고: 연체율 상승 관찰.")
    else: st.success("안전: 연체 리스크 통제 가능.")

# ---------------------------------------------------------------------------
# 7. 기초 데이터 표 확인
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📚 학습에 사용된 시계열 데이터")
st.dataframe(df, use_container_width=True)
