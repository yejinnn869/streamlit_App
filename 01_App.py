import streamlit as st
import requests
import random

st.set_page_config(
    page_title="오늘 뭐 먹지? 🍙",
    page_icon="🍜",
    layout="centered"
)

# -------------------------
# 귀여운 CSS
# -------------------------
st.markdown("""
<style>

.stApp{
    background: linear-gradient(180deg,#FFF7F8,#FFFDF5);
}

h1{
    text-align:center;
    color:#ff69b4;
}

.card{
    background:white;
    border-radius:20px;
    padding:20px;
    box-shadow:0 5px 20px rgba(0,0,0,0.1);
}

div.stButton > button{
    background:#ffb6c1;
    color:white;
    border:none;
    border-radius:15px;
    height:50px;
    font-size:18px;
}

div.stButton > button:hover{
    background:#ff69b4;
}

</style>
""", unsafe_allow_html=True)

st.title("🍜 오늘 뭐 먹지?")
st.caption("날씨에 따라 메뉴를 추천해드려요 💖")

# -------------------------
# 메뉴 데이터
# -------------------------

menus = {

    "Rain":[
        {
            "name":"김치찌개",
            "img":"https://images.unsplash.com/photo-1604908176997-4311d4d5d295?w=800",
            "kcal":"550 kcal",
            "nutrition":"탄수화물 40g | 단백질 28g | 지방 22g"
        },
        {
            "name":"칼국수",
            "img":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "kcal":"620 kcal",
            "nutrition":"탄수화물 78g | 단백질 20g | 지방 14g"
        }
    ],

    "Clear":[
        {
            "name":"비빔밥",
            "img":"https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=800",
            "kcal":"580 kcal",
            "nutrition":"탄수화물 67g | 단백질 24g | 지방 18g"
        },
        {
            "name":"샐러드",
            "img":"https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800",
            "kcal":"320 kcal",
            "nutrition":"탄수화물 18g | 단백질 23g | 지방 12g"
        }
    ],

    "Clouds":[
        {
            "name":"돈까스",
            "img":"https://images.unsplash.com/photo-1604909052743-94e838986d24?w=800",
            "kcal":"780 kcal",
            "nutrition":"탄수화물 65g | 단백질 32g | 지방 35g"
        },
        {
            "name":"우동",
            "img":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "kcal":"500 kcal",
            "nutrition":"탄수화물 72g | 단백질 18g | 지방 10g"
        }
    ],

    "Snow":[
        {
            "name":"어묵탕",
            "img":"https://images.unsplash.com/photo-1604908176997-4311d4d5d295?w=800",
            "kcal":"410 kcal",
            "nutrition":"탄수화물 20g | 단백질 34g | 지방 16g"
        }
    ],

    "Default":[
        {
            "name":"제육볶음",
            "img":"https://images.unsplash.com/photo-1604908176997-4311d4d5d295?w=800",
            "kcal":"690 kcal",
            "nutrition":"탄수화물 48g | 단백질 39g | 지방 27g"
        }
    ]

}

# -------------------------
# 도시 입력
# -------------------------

city = st.text_input(
    "📍 도시 이름을 입력하세요",
    value="Seoul"
)

# -------------------------
# 버튼
# -------------------------

if st.button("🍽️ 메뉴 추천받기"):

    API_KEY = st.secrets["OPENWEATHER_API_KEY"]

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()

        weather = data["weather"][0]["main"]
        temp = data["main"]["temp"]

        st.success(f"현재 날씨 : {weather}")
        st.info(f"현재 기온 : {temp:.1f}℃")

        if weather in menus:
            menu = random.choice(menus[weather])
        else:
            menu = random.choice(menus["Default"])

        st.markdown("<div class='card'>",unsafe_allow_html=True)

        st.subheader("🍴 오늘의 추천 메뉴")

        st.image(menu["img"])

        st.header(menu["name"])

        st.write("🔥 **칼로리**")
        st.write(menu["kcal"])

        st.write("🥗 **영양정보**")
        st.write(menu["nutrition"])

        st.markdown("</div>",unsafe_allow_html=True)

    else:
        st.error("도시를 찾을 수 없습니다.")
