import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ==========================================
# 1. 페이지 기본 설정 및 헤더
# ==========================================
st.set_page_config(
    page_title="행동경제학 기반 환율-주가 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 환율 변동과 기업 주가의 '합리적 무시' 실증 분석")
st.caption("공공 데이터(FinanceDataReader) 기반 거시경제-행동경제학 융합 탐구 대시보드")

# 이론적 배경 설명 상자
with st.expander("💡 행동경제학: '합리적 무시(Rational Inattention)' 이론이란?", expanded=True):
    st.write("""
    전통 경제학은 환율이나 가격이 소폭만 변해도 투자자와 소비자가 즉각 반응한다고 가정합니다. 
    그러나 **크리스토퍼 심스(Christopher Sims) 교수**의 **합리적 무시 이론**에 따르면, 인간은 **'정보 처리 비용'** 때문에 
    변동 폭이 자신만의 **임계값(Threshold)** 이하일 때는 변화를 감지하지 않거나 무시하며, **임계값을 초과할 때 비로소 민감하게 반응**합니다.
    """)

# ==========================================
# 2. 사이드바 (사용자 조작 컨트롤 패널)
# ==========================================
st.sidebar.header("⚙️ 분석 설정 패널")

# 2-1. 분석 대상 기업 선택
company_dict = {
    "삼성전자 (수출 중심 기업)": "005930",
    "CJ제일제당 (내수/수입 중심 기업)": "097950"
}
selected_company_name = st.sidebar.selectbox("1. 분석 기업 선택", list(company_dict.keys()))
selected_code = company_dict[selected_company_name]

# 2-2. 분석 기간 선택
today = datetime.date.today()
default_start = today - datetime.timedelta(days=365) # 기본값: 최근 1년
start_date = st.sidebar.date_input("2. 분석 시작일", default_start)
end_date = st.sidebar.date_input("3. 분석 종료일", today)

# 2-3. 합리적 무시 임계값 슬라이더
st.sidebar.subheader("3. 행동경제학 변수 설정")
threshold = st.sidebar.slider(
    "소비자/투자자 환율 인지 임계값 (%)",
    min_value=0.0,
    max_value=3.0,
    value=1.0,
    step=0.1,
    help="환율의 일간 변동률이 이 기준 이하이면 '무시 구간', 초과하면 '반응 구간'으로 분류합니다."
)

# ==========================================
# 3. 데이터 수집 및 전처리 (캐싱 적용)
# ==========================================
@st.cache_data
def load_data(stock_code, start, end):
    # 원/달러 환율 데이터 불러오기
    df_fx = fdr.DataReader('USD/KRW', start, end)[['Close']].rename(columns={'Close': 'FX_Price'})
    # 선택한 기업 주가 데이터 불러오기
    df_stock = fdr.DataReader(stock_code, start, end)[['Close']].rename(columns={'Close': 'Stock_Price'})
    
    # 두 데이터 병합 (날짜 기준)
    df = pd.merge(df_fx, df_stock, left_index=True, right_index=True, how='inner')
    
    # 일간 변동률 (%) 계산
    df['FX_Change'] = df['FX_Price'].pct_change().abs() * 100 # 환율은 절댓값 변동률
    df['Stock_Change'] = df['Stock_Price'].pct_change() * 100 # 주가 변동률
    
    return df.dropna()

# 데이터 로딩 상태 표시
with st.spinner('금융 데이터를 불러오는 중입니다...'):
    data = load_data(selected_code, start_date, end_date)

# 선택한 임계값 기준으로 구간 분류 (무시 구간 vs 반응 구간)
data['Group'] = data['FX_Change'].apply(
    lambda x: '반응 구간 (임계값 초과)' if x > threshold else '무시 구간 (임계값 이하)'
)

# ==========================================
# 4. 시각화 및 데이터 분석 리포트
# ==========================================

# --- [파트 1] 시계열 추이 비교 차트 (이중 축) ---
st.subheader("1. 원/달러 환율 추이 vs 기업 주가 추이")

fig1 = make_subplots(specs=[[{"secondary_y": True}]])

# 주가 그래프 (좌측 Y축)
fig1.add_trace(
    go.Scatter(x=data.index, y=data['Stock_Price'], name=selected_company_name, line=dict(color='#2b5c8f', width=2)),
    secondary_y=False
)
# 환율 그래프 (우측 Y축)
fig1.add_trace(
    go.Scatter(x=data.index, y=data['FX_Price'], name="원/달러 환율 (KRW)", line=dict(color='#e67e22', width=2, dash='dot')),
    secondary_y=True
)

fig1.update_layout(
    height=400,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig1.update_yaxes(title_text="주가 (원)", secondary_y=False)
fig1.update_yaxes(title_text="환율 (원)", secondary_y=True)

st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- [파트 2] 합리적 무시 실증 분석 및 리포트 ---
st.subheader("2. '합리적 무시' 임계점 기반 주가 변동성 비교")

# 통계 수치 계산
group_ignored = data[data['Group'] == '무시 구간 (임계값 이하)']
group_reacted = data[data['Group'] == '반응 구간 (임계값 초과)']

avg_vol_ignored = group_ignored['Stock_Change'].abs().mean()
avg_vol_reacted = group_reacted['Stock_Change'].abs().mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="무시 구간 평균 주가 변동폭",
        value=f"{avg_vol_ignored:.2f}%",
        delta=f"환율 변동 {threshold}% 이하 (총 {len(group_ignored)}일)",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="반응 구간 평균 주가 변동폭",
        value=f"{avg_vol_reacted:.2f}%",
        delta=f"환율 변동 {threshold}% 초과 (총 {len(group_reacted)}일)",
        delta_color="inverse"
    )

with col3:
    if avg_vol_ignored > 0:
        ratio = avg_vol_reacted / avg_vol_ignored
        st.metric(
            label="반응 민감도 증가율",
            value=f"{ratio:.1f} 배",
            help="임계값을 넘어섰을 때 주가 변동성이 몇 배 커지는지 나타냅니다."
        )
    else:
        st.metric(label="반응 민감도 증가율", value="계산 불가")

# --- [파트 3] 산점도 시각화 ---
fig2 = px.scatter(
    data,
    x='FX_Change',
    y='Stock_Change',
    color='Group',
    color_discrete_map={
        '무시 구간 (임계값 이하)': '#95a5a6',
        '반응 구간 (임계값 초과)': '#e74c3c'
    },
    labels={'FX_Change': '환율 일간 변동률 (%)', 'Stock_Change': '주가 일간 변동률 (%)'},
    title=f"환율 변동률에 따른 주가 변동 분포 (기준 임계값: {threshold}%)"
)

# 임계값 세로 수직선 추가
fig2.add_vline(x=threshold, line_width=2, line_dash="dash", line_color="red")

st.plotly_chart(fig2, use_container_width=True)

# 종합 인사이트 요약 상자
st.info(f"""
📌 **실증 분석 결과 요약**
* 현재 설정된 환율 인지 임계값 **({threshold}%)** 이하에서는 주가 일간 변동폭이 평균 **{avg_vol_ignored:.2f}%**로 비교적 안정적이었습니다.
* 그러나 환율 변동률이 임계값을 초과하는 **반응 구간**에 진입하면 주가 일간 변동폭이 평균 **{avg_vol_reacted:.2f}%**로 급증하는 비선형적 특성을 확인할 수 있습니다.
""")
