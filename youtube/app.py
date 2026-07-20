import re
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from wordcloud import WordCloud
from konlpy.tag import Okt
from kiwipiepy import Kiwi

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="🎬",
    layout="wide"
)

FONT_PATH = "NanumGothic.ttf"  # 깃허브 리포지토리에 위치한 폰트 파일명

# --- Secrets에서 API 키 로드 ---
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("Streamlit Secrets에 'YOUTUBE_API_KEY'가 설정되지 않았습니다.")
    st.stop()

# --- 유튜브 URL에서 Video ID 추출 ---
def extract_video_id(url):
    pattern = r'(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/details\?id=|^https?:\/\/youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# --- 댓글 수집 함수 ---
@st.cache_data(show_spinner=False)
def get_youtube_comments(video_id, max_comments=100):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_comments, 100),
            order="relevance"
        )
        
        while request and len(comments) < max_comments:
            response = request.execute()
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": snippet["authorDisplayName"],
                    "text": snippet["textDisplay"],
                    "published_at": snippet["publishedAt"],
                    "like_count": snippet["likeCount"]
                })
                if len(comments) >= max_comments:
                    break
            
            # 다음 페이지 토큰 확인
            if "nextPageToken" in response and len(comments) < max_comments:
                request = youtube.commentThreads().list_next(previous_request=request, previous_response=response)
            else:
                break

    except Exception as e:
        st.error(f"댓글을 불러오는 중 오류가 발생했습니다: {e}")
        return None

    return pd.DataFrame(comments)

# --- 메인 UI ---
st.title("🎬 유튜브 댓글 분석기")
st.write("유튜브 영상 링크를 입력하고 댓글을 다각도로 분석해보세요!")

url = st.text_input("유튜브 영상 URL을 입력하세요", placeholder="https://www.youtube.com/watch?v=...")
max_count = st.slider("수집할 댓글 개수 선택", min_value=10, max_value=500, value=100, step=10)

if url:
    video_id = extract_video_id(url)
    
    if not video_id:
        st.warning("올바른 유튜브 URL을 입력해 주세요.")
    else:
        # 영상 임베드 및 데이터 처리 영역
        col_video, col_info = st.columns([1, 1])
        
        with col_video:
            st.subheader("📺 영상 보기")
            st.video(f"https://www.youtube.com/watch?v={video_id}")

        with st.spinner("댓글 수집 및 분석 중..."):
            df = get_youtube_comments(video_id, max_count)

        if df is not None and not df.empty:
            df["published_at"] = pd.to_datetime(df["published_at"])

            with col_info:
                st.subheader("📊 댓글 요약")
                st.metric("수집된 댓글 수", f"{len(df)}개")
                st.metric("총 좋아요 수", f"{df['like_count'].sum():,}개")
                st.metric("최대 좋아요 댓글 수", f"{df['like_count'].max():,}개")

            st.divider()

            # --- 1. 시간대별 댓글 작성 추이 ---
            st.subheader("📈 시간대별 댓글 작성 추이")
            df_time = df.copy()
            df_time.set_index("published_at", inplace=True)
            # 일단위 또는 시간단위 리샘플링
            time_resampled = df_time.resample("D").size().reset_index(name="count")
            
            fig_time = px.line(
                time_resampled, 
                x="published_at", 
                y="count", 
                labels={"published_at": "날짜", "count": "작성 수"},
                title="일별 댓글 작성 추이"
            )
            st.plotly_chart(fig_time, use_container_width=True)

            # --- 2. 댓글 반응도 (좋아요 분포) ---
            st.subheader("🔥 댓글 반응도 (좋아요 수 상위 댓글)")
            top_comments = df.sort_values(by="like_count", ascending=False).head(10)
            
            fig_likes = px.bar(
                top_comments,
                x="like_count",
                y="author",
                orientation="h",
                text="like_count",
                labels={"like_count": "좋아요 수", "author": "작성자"},
                title="상위 10개 공감 댓글"
            )
            fig_likes.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_likes, use_container_width=True)

            # --- 3. 한글 워드 클라우드 ---
            st.subheader("☁️ 댓글 한글 워드클라우드")

            all_text = " ".join(df["text"].fillna("").astype(str))

            cleaned_text = re.sub(r"[^가-힣\s]", " ", all_text)

            kiwi = Kiwi()
            tokens = kiwi.tokenize(cleaned_text)
            nouns = [t.form for t in tokens if t.tag.startswith("NN") and len(t.form) > 1]
            
            
            # 한글 및 공백만 남기기
            cleaned_text = re.sub(r'[^가-힣\s]', '', all_text)
            
            # 명사 추출
            nouns = okt.nouns(cleaned_text)
            nouns = [n for n in nouns if len(n) > 1]  # 1글자 단어 제외
            
            if nouns:
                text_for_wc = " ".join(nouns)
                
                try:
                    wc = WordCloud(
                        font_path=FONT_PATH,
                        background_color="white",
                        width=800,
                        height=400
                    ).generate(text_for_wc)

                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)
                except OSError:
                    st.error(f"폰트 파일({FONT_PATH})을 찾을 수 없습니다. 깃허브에 업로드했는지 확인해 주세요.")
            else:
                st.info("워드클라우드를 생성할 한글 명사 데이터가 부족합니다.")

            # --- 데이터 테이블 표시 ---
            with st.expander("📝 전체 댓글 데이터 보기"):
                st.dataframe(df[["author", "text", "like_count", "published_at"]])
