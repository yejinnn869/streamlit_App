# app.py

```python
import streamlit as st
import random

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="🍽️ 오늘 뭐 먹지?",
    page_icon="🍙",
    layout="centered"
)

# -----------------------------
# 귀여운 CSS
# -----------------------------
st.markdown("""
<style>

.stApp{
    background: linear-gradient(180deg,#FFF7F8,#FFFDF5);
}

h1,h2,h3{
    text-align:center;
    color:#FF69B4;
}

.menu-card{
    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0px 5px 15px rgba(0,0,0,0.15);
    margin-top:20px;
}

div.stButton > button{
    width:100%;
    height:55px;
    border:none;
    border-radius:15px;
    background:#FFB6C1;
    color:white;
    font-size:20px;
    font-weight:bold;
}

div.stButton > button:hover{
    background:#FF69B4;
    color:white;
}

.stSelectbox label{
    font-size:18px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# 제목
# -----------------------------
st.title("🍽️ 오늘 뭐 먹지?")
st.write("### 🌤️ 오늘의 날씨를 선택하면 메뉴를 추천해드려요!")

# -----------------------------
# 메뉴 데이터
# -----------------------------
menus = {

    "Clear":[
        {
            "name":"🥗 닭가슴살 샐러드",
            "img":"https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800",
            "kcal":"320 kcal",
            "nutrition":"탄수화물 18g | 단백질 25g | 지방 12g"
        },
        {
            "name":"🍚 비빔밥",
            "img":"https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=800",
            "kcal":"580 kcal",
            "nutrition":"탄수화물 67g | 단백질 24g | 지방 18g"
        }
    ],

    "Clouds":[
        {
            "name":"🍛 돈까스",
            "img":"https://images.unsplash.com/photo-1604909052743-94e838986d24?w=800",
            "kcal":"780 kcal",
            "nutrition":"탄수화물 65g | 단백질 32g | 지방 35g"
        },
        {
            "name":"🍜 우동",
            "img":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "kcal":"500 kcal",
            "nutrition":"탄수화물 72g | 단백질 18g | 지방 10g"
        }
    ],

    "Rain":[
        {
            "name":"🌶️ 김치찌개",
            "img":"https://images.unsplash.com/photo-1604908176997-4311d4d5d295?w=800",
            "kcal":"550 kcal",
            "nutrition":"탄수화물 40g | 단백질 28g | 지방 22g"
        },
        {
            "name":"🍲 칼국수",
            "img":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "kcal":"620 kcal",
            "nutrition":"탄수화물 78g | 단백질 20g | 지방 14g"
        }
    ],

    "Snow":[
        {
            "name":"🍢 어묵탕",
            "img":"https://images.unsplash.com/photo-1604908176997-4311d4d5d295?w=800",
            "kcal":"410 kcal",
            "nutrition":"탄수화물 20g | 단백질 34g | 지방 16g"
        },
        {
            "name":"🍜 라면",
            "img":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "kcal":"510 kcal",
            "nutrition":"탄수화물 68g | 단백질 12g | 지방 20g"
        }
    ]

}

# -----------------------------
# 날씨 선택
# -----------------------------
weather = st.selectbox(
    "🌤️ 오늘의 날씨를 선택하세요",
    ["☀️ 맑음", "☁️ 흐림", "🌧️ 비", "❄️ 눈"]
)

weather_map = {
    "☀️ 맑음":"Clear",
    "☁️ 흐림":"Clouds",
    "🌧️ 비":"Rain",
    "❄️ 눈":"Snow"
}

# -----------------------------
# 추천 버튼
# -----------------------------
if st.button("🍽️ 메뉴 추천받기"):

    menu = random.choice(
        menus[weather_map[weather]]
    )

    st.success(f"오늘의 날씨 : {weather}")

    st.markdown("<div class='menu-card'>", unsafe_allow_html=True)

    st.image(menu["img"], use_container_width=True)

    st.markdown(
        f"<h2>{menu['name']}</h2>",
        unsafe_allow_html=True
    )

    st.markdown(f"### 🔥 칼로리\n**{menu['kcal']}**")

    st.markdown(f"### 🥗 영양소\n{menu['nutrition']}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.balloons()
```

---

## requirements.txt

```text
streamlit
```
