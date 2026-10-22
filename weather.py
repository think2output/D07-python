import os
from datetime import datetime, timedelta, timezone

import requests
import streamlit as st
from dotenv import load_dotenv

API = {
    "weather": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
}

# 비교할 도시: 이름, 위도, 경도
CITIES = [
    ("서울", 37.5665, 126.9780),
    ("뉴욕", 40.7128, -74.0060),
]

ERRORS = {
    401: "날씨 키가 틀렸거나 아직 켜지지 않았어요(가입 후 최대 2시간)",
    404: "그 도시를 찾지 못했어요",
    429: "1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요",
}


# 10분 동안은 저장해 둔 결과를 다시 씀 (화면이 다시 그려질 때마다 API를 부르지 않게)
@st.cache_data(ttl=600)
def get_weather(api_key, lat, lon):
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "kr"}
    try:
        res = requests.get(API["weather"], params=params, timeout=10)  # 🔌 API 호출
    except requests.RequestException:
        return {"error": "날씨 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."}

    if res.status_code != 200:
        return {"error": ERRORS.get(res.status_code, f"날씨를 불러오지 못했어요 (오류 코드 {res.status_code})")}

    data = res.json()
    # 도시의 현지 시각 = 지금 UTC 시각 + 시차
    local_time = datetime.now(timezone.utc) + timedelta(seconds=data["timezone"])  # data["timezone"] = UTC와의 시차(초)
    return {
        "temp": data["main"]["temp"],  # data["main"]["temp"] = 지금 기온
        "feels_like": data["main"]["feels_like"],  # data["main"]["feels_like"] = 체감 온도
        "humidity": data["main"]["humidity"],  # data["main"]["humidity"] = 습도(%)
        "description": data["weather"][0]["description"],  # data["weather"][0]["description"] = 날씨 설명 (weather는 목록이라 [0])
        "local_time": local_time.strftime("%m월 %d일 %H:%M"),
    }


def show(name, w):
    st.subheader(f"📍 {name}")
    st.caption(f"현지 시각 {w['local_time']}")
    st.metric("기온", f"{w['temp']:.1f}℃")
    st.metric("체감 온도", f"{w['feels_like']:.1f}℃")
    st.metric("습도", f"{w['humidity']}%")
    st.write(f"날씨: **{w['description']}**")


def compare(a_name, a, b_name, b):
    st.subheader(f"🆚 {a_name} vs {b_name}")
    diff = a["temp"] - b["temp"]
    if abs(diff) < 0.5:
        st.write("- 기온: 두 도시가 거의 같아요")
    else:
        warmer, colder = (a_name, b_name) if diff > 0 else (b_name, a_name)
        st.write(f"- 기온: {warmer}이(가) {colder}보다 **{abs(diff):.1f}℃** 더 따뜻해요")

    feel = a["feels_like"] - b["feels_like"]
    st.write(f"- 체감 온도 차이: **{abs(feel):.1f}℃**")

    hum = a["humidity"] - b["humidity"]
    if hum == 0:
        st.write("- 습도: 두 도시가 같아요")
    else:
        wetter = a_name if hum > 0 else b_name
        st.write(f"- 습도: {wetter}이(가) **{abs(hum)}%p** 더 습해요")


st.set_page_config(page_title="서울 · 뉴욕 날씨", page_icon="🌤️")
st.title("🌤️ 서울 · 뉴욕 지금 날씨")

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")
if not api_key:
    st.error(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

# 이 버튼에서만 저장해 둔 결과를 지우고 새로 불러옴
if st.button("새로 불러오기"):
    st.cache_data.clear()

# 칸마다 따로 불러서 한 도시가 실패해도 다른 도시는 보이게
results = {}
for col, (name, lat, lon) in zip(st.columns(len(CITIES)), CITIES):
    with col:
        w = get_weather(api_key, lat, lon)
        if "error" in w:
            st.subheader(f"📍 {name}")
            st.error(w["error"])
        else:
            show(name, w)
            results[name] = w

# 두 도시를 모두 불러왔을 때만 비교
if len(results) == 2:
    st.divider()
    (a_name, a), (b_name, b) = results.items()
    compare(a_name, a, b_name, b)

st.divider()
st.caption("출처: 날씨 OpenWeather · 10분마다 새로 불러와요")
