import streamlit as st
import random

st.set_page_config(
    page_title="서울 오늘 뭐 먹지?",
    page_icon="🍜"
)

st.markdown("""
<style>
.stApp{
    background:linear-gradient(#FFF8FC,#FFEFF7);
}

.title{
    text-align:center;
    color:#ff66aa;
}

.foodcard{
    background:white;
    padding:20px;
    border-radius:20px;
    box-shadow:0px 3px 15px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>🍴 서울 오늘 뭐 먹지?</h1>", unsafe_allow_html=True)

st.write("### 📍 지역 : 서울")

weather = st.radio(
    "오늘의 날씨를 선택하세요.",
    ["☀️ 맑음","☁️ 흐림","🌧️ 비","❄️ 눈"]
)

foods = {

"☀️ 맑음":[
{
"name":"냉모밀",
"image":"https://picsum.photos/600/400?1",
"cal":"450 kcal",
"nut":"탄수화물 65g / 단백질 16g / 지방 7g"
},
{
"name":"비빔국수",
"image":"https://picsum.photos/600/400?2",
"cal":"510 kcal",
"nut":"탄수화물 73g / 단백질 14g / 지방 8g"
}
],

"☁️ 흐림":[
{
"name":"돈까스",
"image":"https://picsum.photos/600/400?3",
"cal":"850 kcal",
"nut":"탄수화물 70g / 단백질 33g / 지방 40g"
},
{
"name":"제육볶음",
"image":"https://picsum.photos/600/400?4",
"cal":"700 kcal",
"nut":"탄수화물 30g / 단백질 35g / 지방 30g"
}
],

"🌧️ 비":[
{
"name":"김치찌개",
"image":"https://picsum.photos/600/400?5",
"cal":"580 kcal",
"nut":"탄수화물 41g / 단백질 30g / 지방 23g"
},
{
"name":"칼국수",
"image":"https://picsum.photos/600/400?6",
"cal":"620 kcal",
"nut":"탄수화물 79g / 단백질 18g / 지방 13g"
}
],

"❄️ 눈":[
{
"name":"떡국",
"image":"https://picsum.photos/600/400?7",
"cal":"650 kcal",
"nut":"탄수화물 81g / 단백질 25g / 지방 17g"
},
{
"name":"우동",
"image":"https://picsum.photos/600/400?8",
"cal":"500 kcal",
"nut":"탄수화물 68g / 단백질 17g / 지방 9g"
}
]

}

if st.button("🍽️ 메뉴 추천"):

    menu = random.choice(foods[weather])

    st.image(menu["image"], use_container_width=True)

    st.markdown(f"""
    <div class='foodcard'>

    ## 🍴 {menu['name']}

    🔥 **칼로리**

    {menu['cal']}

    🥗 **영양소**

    {menu['nut']}

    </div>
    """, unsafe_allow_html=True)

    st.balloons()
