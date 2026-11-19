import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="쇼핑 레이더", page_icon="🛒", layout="wide")

st.markdown("""
<style>
.stApp {background:#F6F8FC}
[data-testid="stMetric"] {background:white;padding:16px;border:1px solid #E8EDF5;border-radius:14px}
.hero {padding:26px 30px;border-radius:18px;background:linear-gradient(110deg,#172554,#2563EB);color:white;margin-bottom:18px}
.hero h1 {color:white;margin:0;font-size:30px}
.hero p {color:#DBEAFE;margin:7px 0 0}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def data():
    rng=np.random.default_rng(17)
    n=1500
    dates=pd.to_datetime("2025-01-01")+pd.to_timedelta(rng.integers(0,365,n),unit="D")
    cats=rng.choice(["패션","뷰티","식품","디지털","생활"],n,p=[.24,.2,.2,.16,.2])
    base={"패션":42000,"뷰티":26000,"식품":18000,"디지털":89000,"생활":31000}
    price=np.array([base[c] for c in cats])*rng.uniform(.65,1.45,n)
    qty=rng.choice([1,2,3],n,p=[.72,.23,.05])
    disc=rng.uniform(0,.35,n)
    df=pd.DataFrame({"주문일":dates,"카테고리":cats,"결제금액":(price*qty*(1-disc)).round(-2).astype(int),
                     "수량":qty,"할인율":disc,"채널":rng.choice(["앱","모바일 웹","PC"],n,p=[.58,.27,.15]),
                     "고객":rng.choice(["신규","재구매"],n,p=[.38,.62])})
    return df

df=data()
st.sidebar.title("🛒 쇼핑 레이더")
st.sidebar.caption("소비 패턴 탐색 대시보드")
period=st.sidebar.selectbox("분석 기간",["전체","상반기","하반기"])
cats=st.sidebar.multiselect("상품 카테고리",sorted(df["카테고리"].unique()),default=sorted(df["카테고리"].unique()))
channels=st.sidebar.multiselect("구매 채널",sorted(df["채널"].unique()),default=sorted(df["채널"].unique()))
if period=="상반기": df=df[df["주문일"].dt.month<=6]
elif period=="하반기": df=df[df["주문일"].dt.month>=7]
df=df[df["카테고리"].isin(cats)&df["채널"].isin(channels)]

st.markdown('<div class="hero"><h1>쇼핑 레이더</h1><p>무엇을 · 언제 · 어디서 구매할까?</p></div>',unsafe_allow_html=True)
if df.empty:
    st.info("선택한 조건에 맞는 데이터가 없습니다.")
    st.stop()

sales=df["결제금액"].sum()
a,b,c,d=st.columns(4)
a.metric("총 매출",f"₩{sales:,.0f}")
b.metric("주문 건수",f"{len(df):,}건")
c.metric("평균 구매액",f"₩{df['결제금액'].mean():,.0f}")
d.metric("재구매 고객 비중",f"{(df['고객'].eq('재구매').mean()*100):.1f}%")

st.subheader("1. 월별 매출은 어떻게 변할까?")
monthly=df.assign(월=df["주문일"].dt.to_period("M").astype(str)).groupby("월",as_index=False)["결제금액"].sum()
fig=px.line(monthly,x="월",y="결제금액",markers=True,title="월별 결제금액",template="plotly_white")
fig.update_traces(line_color="#2563EB",fill="tozeroy")
st.plotly_chart(fig,use_container_width=True)

left,right=st.columns(2)
with left:
    st.subheader("2. 인기 카테고리는?")
    cat=df.groupby("카테고리",as_index=False).agg(매출=("결제금액","sum"),주문수=("결제금액","count")).sort_values("매출",ascending=False)
    fig=px.bar(cat,x="카테고리",y="매출",color="매출",text_auto=".2s",color_continuous_scale="Blues",template="plotly_white")
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.subheader("3. 신규 고객과 재구매 고객")
    cust=df.groupby("고객",as_index=False)["결제금액"].sum()
    fig=px.pie(cust,names="고객",values="결제금액",hole=.55,color_discrete_sequence=["#60A5FA","#14B8A6"])
    st.plotly_chart(fig,use_container_width=True)

st.subheader("4. 어떤 채널에서 많이 구매할까?")
channel=df.groupby("채널",as_index=False).agg(주문수=("결제금액","count"),매출=("결제금액","sum"))
fig=px.bar(channel,x="채널",y="주문수",color="채널",text_auto=True,template="plotly_white")
st.plotly_chart(fig,use_container_width=True)

st.subheader("5. 데이터에서 발견한 점")
best=cat.iloc[0]
top_channel=channel.sort_values("주문수",ascending=False).iloc[0]
st.success(f"현재 필터 기준으로 **{best['카테고리']}** 카테고리의 매출이 가장 높습니다. 가장 많은 주문이 발생한 채널은 **{top_channel['채널']}**입니다.")
st.caption("※ 본 화면은 시연용 가상 데이터로 분석한 예시입니다. 실제 시장 통계로 해석하면 안 됩니다.")

with st.expander("분석 데이터 미리보기"):
    st.dataframe(df.sort_values("주문일",ascending=False),use_container_width=True,hide_index=True)
    st.download_button("CSV 다운로드",df.to_csv(index=False).encode("utf-8-sig"),"shopping_data.csv","text/csv")
