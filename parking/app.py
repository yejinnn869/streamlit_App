import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울 공영주차장",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 서울시 공영주차장 안내")
st.caption("서울시 공영주차장 위치 및 요금 정보")

# CSV 읽기
df = pd.read_csv(
    "서울시 공영주차장 안내 정보.csv",
    encoding="cp949"
)

# 위도·경도 없는 데이터 제거
df = df.dropna(subset=["위도", "경도"])

# 숫자로 변환
df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

df = df.dropna(subset=["위도", "경도"])

# 무료 여부 판별
def is_free(row):
    try:
        fee = float(row["기본 주차 요금"])
        return fee == 0
    except:
        return False

df["무료"] = df.apply(is_free, axis=1)

st.sidebar.header("검색")

only_free = st.sidebar.checkbox("무료 주차장만 보기")

if only_free:
    df = df[df["무료"]]

selected = st.sidebar.selectbox(
    "주차장 선택",
    ["전체 보기"] + list(df["주차장명"])
)

# 서울 중심
m = folium.Map(
    location=[37.5665,126.9780],
    zoom_start=11
)

if selected == "전체 보기":

    for _, row in df.iterrows():

        color = "green" if row["무료"] else "blue"

        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=f"""
            <b>{row['주차장명']}</b><br>
            {row['주소']}<br>
            기본요금 : {row['기본 주차 요금']}원
            """,
            icon=folium.Icon(color=color)
        ).add_to(m)

else:

    row = df[df["주차장명"]==selected].iloc[0]

    folium.Marker(
        [row["위도"],row["경도"]],
        popup=row["주차장명"],
        icon=folium.Icon(color="red",icon="info-sign")
    ).add_to(m)

    m.location=[row["위도"],row["경도"]]
    m.zoom_start=16

    st.subheader(row["주차장명"])

    c1,c2=st.columns(2)

    with c1:
        st.write("📍 주소")
        st.write(row["주소"])

        st.write("☎ 전화번호")
        st.write(row["전화번호"])

        st.write("🕒 운영시간")
        st.write(row["평일 운영 시작시각"], "~", row["평일 운영 종료시각"])

    with c2:
        st.write("💰 기본요금")
        st.write(f"{row['기본 주차 요금']} 원")

        st.write("➕ 추가요금")
        st.write(f"{row['추가 단위 요금']} 원")

        st.write("🚗 무료 여부")
        st.write("무료" if row["무료"] else "유료")

st_folium(
    m,
    width=1000,
    height=650
)
