import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="서울 연평균 기온 분석", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("seoul_temperature.csv", encoding="utf-8-sig")
    df["날짜"] = df["날짜"].str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"])
    for col in ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()
df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month
df["일교차(℃)"] = df["최고기온(℃)"] - df["최저기온(℃)"]

# 연평균 = 결측 제외 평균 (1950~1953은 결측이라 공란)
annual = (
    df.groupby("연도")["평균기온(℃)"]
    .agg(연평균기온="mean", 유효일수="count")
    .reset_index()
)
annual.loc[annual["유효일수"] == 0, "연평균기온"] = float("nan")

# 선 그래프에서 공란으로 남길 연도
blank_years = [1907, 1950, 1953, 2026]
annual.loc[annual["연도"].isin(blank_years), "연평균기온"] = float("nan")

# 5년 이동평균 (결측 연도 포함 구간은 공란)
annual["5년 이동평균"] = annual["연평균기온"].rolling(5, center=True, min_periods=5).mean()

min_year = int(annual["연도"].min())
max_year = int(annual["연도"].max())

st.sidebar.title("메뉴 바로가기")
st.sidebar.markdown(
    '<a href="#annual-chart" style="display:block; margin-bottom:4px; color:#1f77b4; text-decoration:none; font-size:15px">📈 연평균기온 + 5년 이동평균 그래프</a>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<a href="#heatmap" style="display:block; margin-bottom:4px; color:#1f77b4; text-decoration:none; font-size:15px">🌡️ 월별 평균기온 히트맵</a>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<a href="#top-bottom-table" style="display:block; margin-bottom:4px; color:#1f77b4; text-decoration:none; font-size:15px">📋 평균기온 상위/하위 10일 표</a>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<a href="#daily-range-chart" style="display:block; margin-bottom:4px; color:#1f77b4; text-decoration:none; font-size:15px">📊 연도별 평균 일교차 그래프</a>',
    unsafe_allow_html=True,
)

st.sidebar.header("연도 범위 설정")
start_year, end_year = st.sidebar.slider(
    "시작 연도 ~ 끝 연도",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

sel = annual[(annual["연도"] >= start_year) & (annual["연도"] <= end_year)]
df_sel = df[(df["연도"] >= start_year) & (df["연도"] <= end_year)]

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

# 1) 연도별 평균기온 + 5년 이동평균 + 추세선
st.markdown('<div id="annual-chart"></div>', unsafe_allow_html=True)

st.title("서울 연평균기온과 5년 이동평균")
fig_annual = px.line(
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
sel_valid = sel.dropna(subset=["연평균기온"])
x = sel_valid["연도"].values.astype(float)
y = sel_valid["연평균기온"].values.astype(float)
trend_coef = np.polyfit(x, y, 1)
trend = np.polyval(trend_coef, x)
fig_annual.add_trace(
    go.Scatter(
        x=x,
        y=trend,
        mode="lines",
        name="추세선",
        line=dict(color="#d62728", dash="dash"),
        showlegend=True,
    )
)
fig_annual.update_layout(legend_title="지표", hovermode="x unified")
st.plotly_chart(fig_annual, use_container_width=True)

# 2) 월별 히트맵
st.markdown('<div id="heatmap"></div>', unsafe_allow_html=True)

st.subheader("월별 평균기온 히트맵")
monthly_avg = df.groupby(["연도", "월"])["평균기온(℃)"].mean().unstack("월")
monthly_avg_T = monthly_avg.T  # 행: 월(1~12), 열: 연도
fig_heatmap = px.imshow(
    monthly_avg_T,
    x=monthly_avg_T.columns,
    y=monthly_avg_T.index,
    labels={"x": "연도", "y": "월", "color": "평균기온"},
    color_continuous_scale="RdYlBu_r",
    title="월별 평균기온 히트맵",
)
fig_heatmap.update_xaxes(tickangle=-45)
st.plotly_chart(fig_heatmap, use_container_width=True)

# 3) 평균기온 상위 10일 / 하위 10일
st.markdown('<div id="top-bottom-table"></div>', unsafe_allow_html=True)

st.subheader("평균기온 상위 10일")
top10 = df.nlargest(10, "평균기온(℃)")[["날짜", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]].copy()
top10["날짜"] = top10["날짜"].dt.strftime("%Y-%m-%d")
st.dataframe(top10, use_container_width=True)

st.subheader("평균기온 하위 10일")
bottom10 = df.nsmallest(10, "평균기온(℃)")[["날짜", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]].copy()
bottom10["날짜"] = bottom10["날짜"].dt.strftime("%Y-%m-%d")
st.dataframe(bottom10, use_container_width=True)

# 4) 연도별 평균 일교차
st.markdown('<div id="daily-range-chart"></div>', unsafe_allow_html=True)

st.subheader("연도별 평균 일교차")
daily_range = df_sel.groupby("연도")["일교차(℃)"].mean().reset_index()
fig_range = px.line(
    daily_range,
    x="연도",
    y="일교차(℃)",
    markers=True,
    title="연도별 평균 일교차",
    labels={"연도": "연도", "일교차(℃)": "평균 일교차 (℃)"},
)
st.plotly_chart(fig_range, use_container_width=True)
