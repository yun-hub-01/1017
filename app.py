import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="서울 연평균 기온 분석", layout="wide")

# ---------- 데이터 로드 ----------
@st.cache_data
def load_data():
    df = pd.read_csv("seoul_temperature.csv", encoding="utf-8-sig")
    # 날짜 값 앞의 탭 문자 제거
    df["날짜"] = df["날짜"].str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 기온 컬럼을 숫자로 변환 (결측치는 NaN 처리)
    for col in ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 1950~1953년의 결측치 행은 그래프에서 제외
    df = df.dropna(subset=["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"])
    return df

df = load_data()

# 연도 컬럼 추가
df["연도"] = df["날짜"].dt.year

# ---------- 연도별 평균기온 및 5년 이동평균 ----------
annual = (
    df.groupby("연도")["평균기온(℃)"]
    .mean()
    .reset_index()
    .rename(columns={"평균기온(℃)": "연평균기온"})
)
annual["5년 이동평균"] = annual["연평균기온"].rolling(5, center=True, min_periods=1).mean()

min_year = int(annual["연도"].min())
max_year = int(annual["연도"].max())

# ---------- 사이드바: 연도 범위 슬라이더 ----------
st.sidebar.header("연도 범위 설정")
start_year, end_year = st.sidebar.slider(
    "시작 연도 ~ 끝 연도",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

# 선택 구간 필터
sel = annual[(annual["연도"] >= start_year) & (annual["연도"] <= end_year)]

# ---------- 선택 구간 통계 ----------
mean_temp = sel["연평균기온"].mean()
max_temp = sel["연평균기온"].max()
min_temp = sel["연평균기온"].min()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("선택 구간 평균기온", f"{mean_temp:.2f} ℃")
with col2:
    st.metric("선택 구간 최고기온", f"{max_temp:.2f} ℃")
with col3:
    st.metric("선택 구간 최저기온", f"{min_temp:.2f} ℃")

# ---------- 그래프 ----------
st.title("서울 연평균기온과 5년 이동평균")
st.caption(f"선택 구간: {start_year}년 ~ {end_year}년 (전체 데이터: {min_year}~{max_year}년)")
st.info("1950~1953년의 결측치 행은 그래프에서 제외했습니다.")

fig = px.line(
    sel,
    x="연도",
    y=["연평균기온", "5년 이동평균"],
    markers=True,
    title="연도별 평균기온",
    labels={
        "연평균기온": "평균기온 (℃)",
        "5년 이동평균": "5년 이동평균 (℃)",
        "연도": "연도",
    },
    color_discrete_map={"연평균기온": "#1f77b4", "5년 이동평균": "#ff7f0e"},
)
fig.update_layout(legend_title="지표", hovermode="x unified")

st.plotly_chart(fig, use_container_width=True)
