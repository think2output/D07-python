import os
from datetime import datetime, timedelta, timezone

import requests
import streamlit as st
from dotenv import load_dotenv

API = {
    "rate": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 환율 (기준 USD)
}

# 통화 코드: (이름, 국기, 카드 색)
CURRENCIES = {
    "KRW": ("원", "🇰🇷", "#FF6B6B"),
    "USD": ("달러", "🇺🇸", "#4D96FF"),
    "JPY": ("엔", "🇯🇵", "#FF9F43"),
    "EUR": ("유로", "🇪🇺", "#6BCB77"),
    "CNY": ("위안", "🇨🇳", "#C77DFF"),
    "GBP": ("파운드", "🇬🇧", "#FFD93D"),
}

# 한눈에 보기: 이만큼이 몇 원인지 (엔은 100엔 단위로 보는 게 보통)
QUICK = [("USD", 1), ("JPY", 100), ("EUR", 1), ("CNY", 1)]

ERRORS = {
    "invalid-key": "환율 키가 틀렸어요",
    "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요",
    "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요",
}

KST = timezone(timedelta(hours=9))


# 1시간 동안은 저장해 둔 결과를 다시 씀 (무료 플랜은 한 달 1,500번)
@st.cache_data(ttl=3600)
def get_rates(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}  # 키는 주소가 아니라 헤더로 보냄
    try:
        res = requests.get(API["rate"], headers=headers, timeout=10)  # 🔌 API 호출
        data = res.json()
    except (requests.RequestException, ValueError):
        return {"error": "환율 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."}

    if data.get("result") != "success":  # data["result"] = "success" 또는 "error"
        error_type = data.get("error-type", "")  # data["error-type"] = 실패 이유
        return {"error": ERRORS.get(error_type, "환율을 불러오지 못했어요")}

    # data["time_last_update_utc"] = 환율 기준 시각 (영국 시간) → 한국 시간으로 바꿈
    updated = datetime.strptime(data["time_last_update_utc"], "%a, %d %b %Y %H:%M:%S %z").astimezone(KST)
    return {
        "rates": data["conversion_rates"],  # data["conversion_rates"]["KRW"] = 1달러가 몇 원
        "updated": updated.strftime("%Y년 %m월 %d일 %H:%M"),
    }


def convert(amount, src, dst, rates):
    # 모든 값이 1달러 기준이라: 달러로 바꾼 뒤 → 목표 통화로
    return amount / rates[src] * rates[dst]


def label(code):
    name, flag, _ = CURRENCIES[code]
    return f"{flag} {code} ({name})"


def card(color, top, big, bottom=""):
    return (
        f'<div style="background:{color};border-radius:16px;padding:16px 18px;margin:6px 0;'
        f'color:#fff;box-shadow:0 4px 12px rgba(0,0,0,.15);">'
        f'<div style="font-size:14px;opacity:.9;">{top}</div>'
        f'<div style="font-size:26px;font-weight:800;margin:4px 0;">{big}</div>'
        f'<div style="font-size:13px;opacity:.85;">{bottom}</div></div>'
    )


def money(value, code):
    # 원·엔은 소수점 없이, 나머지는 소수 둘째 자리까지
    digits = 0 if code in ("KRW", "JPY") else 2
    return f"{value:,.{digits}f} {CURRENCIES[code][0]}"


st.set_page_config(page_title="환율 계산기", page_icon="💱")
st.markdown(
    '<h1 style="background:linear-gradient(90deg,#FF6B6B,#FFD93D,#6BCB77,#4D96FF,#C77DFF);'
    '-webkit-background-clip:text;color:transparent;">💱 환율 계산기</h1>',
    unsafe_allow_html=True,
)

load_dotenv()
api_key = os.getenv("EXCHANGERATE_API_KEY")
if not api_key:
    st.error(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

result = get_rates(api_key)
if "error" in result:
    st.error(result["error"])
    st.stop()

rates = result["rates"]

# 계산기: 금액과 통화를 고르면 바로 계산
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    amount = st.number_input("금액", min_value=0.0, value=100.0, step=10.0)
with col2:
    src = st.selectbox("이 돈을", list(CURRENCIES), index=1, format_func=label)
with col3:
    dst = st.selectbox("이 돈으로", list(CURRENCIES), index=0, format_func=label)

converted = convert(amount, src, dst, rates)
st.markdown(
    card(
        "linear-gradient(135deg,#FF6B6B,#C77DFF,#4D96FF)",
        f"{CURRENCIES[src][1]} {money(amount, src)} 은(는)",
        f"{CURRENCIES[dst][1]} {money(converted, dst)}",
        f"1 {src} = {convert(1, src, dst, rates):,.4f} {dst}",
    ),
    unsafe_allow_html=True,
)

# 한눈에 보기: 주요 통화가 몇 원인지 색깔 카드로
st.subheader("🌈 한눈에 보기")
for col, (code, unit) in zip(st.columns(len(QUICK)), QUICK):
    name, flag, color = CURRENCIES[code]
    with col:
        st.markdown(
            card(color, f"{flag} {unit:,}{name}", money(convert(unit, code, "KRW", rates), "KRW")),
            unsafe_allow_html=True,
        )

st.divider()
st.caption(f"출처: 환율 ExchangeRate-API · 기준 시각 {result['updated']} (한국 시간) · 하루 한 번 갱신돼요")
