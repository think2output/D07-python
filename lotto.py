import random
from datetime import datetime, timedelta

import streamlit as st

# 동행복권 공 색상 규칙: 번호 구간마다 색이 정해져 있음
COLORS = [
    (10, "#FBC400"),  # 1~10 노랑
    (20, "#69C8F2"),  # 11~20 파랑
    (30, "#FF7272"),  # 21~30 빨강
    (40, "#AAAAAA"),  # 31~40 회색
    (45, "#B0D840"),  # 41~45 초록
]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def ball_color(n):
    for limit, color in COLORS:
        if n <= limit:
            return color


def make_sets(count=5):
    # 1~45 중 겹치지 않게 6개를 뽑고 작은 수부터 정렬
    return [sorted(random.sample(range(1, 46), 6)) for _ in range(count)]


def next_draw_date(now):
    # 추첨은 매주 토요일 20:35. 토요일 추첨 이후면 다음 주 토요일
    days = (5 - now.weekday()) % 7
    if days == 0 and now.hour * 60 + now.minute >= 20 * 60 + 35:
        days = 7
    return now + timedelta(days=days)


def format_date(d):
    return f"{d:%Y년 %m월 %d일} ({WEEKDAYS[d.weekday()]})"


def ball_html(n):
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:44px;height:44px;margin:4px;border-radius:50%;'
        f'background:{ball_color(n)};color:#fff;font-weight:700;font-size:18px;'
        f'text-shadow:0 1px 2px rgba(0,0,0,.35);">{n}</span>'
    )


st.set_page_config(page_title="로또 번호 생성기", page_icon="🎱")
st.title("🎱 로또 번호 생성기")

now = datetime.now()
st.write(f"📅 오늘: **{format_date(now)}**")
st.write(f"🗓️ 다음 추첨일: **{format_date(next_draw_date(now))} 20:35**")

if st.button("번호 뽑기", type="primary"):
    st.session_state["sets"] = make_sets()
    st.session_state["made_at"] = now

# 버튼을 누르기 전에는 안내만, 누른 뒤에는 결과를 계속 보여 줌
if "sets" in st.session_state:
    st.caption(f"생성 시각: {st.session_state['made_at']:%Y-%m-%d %H:%M:%S}")
    for i, numbers in enumerate(st.session_state["sets"]):
        label = chr(ord("A") + i)  # A, B, C, D, E 세트
        balls = "".join(ball_html(n) for n in numbers)
        st.markdown(
            f'<div style="display:flex;align-items:center;flex-wrap:wrap;margin:6px 0;">'
            f'<b style="width:28px;font-size:18px;">{label}</b>{balls}</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("버튼을 누르면 6개 숫자 × 5세트가 나와요.")

st.divider()
st.caption("색상: 1~10 노랑 · 11~20 파랑 · 21~30 빨강 · 31~40 회색 · 41~45 초록")
