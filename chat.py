import os

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

API = {
    "chat": "https://api.openai.com/v1",  # 🔌 OpenAI 채팅 API + 모델 목록 API
}

# 기본 모델. 화면 왼쪽 사이드바에서 바꿀 수 있음
DEFAULT_MODEL = "gpt-4o-mini"

# 모델 목록에서 채팅용이 아닌 것(그림·음성·임베딩 등)은 뺌
NOT_CHAT = ("embedding", "tts", "whisper", "dall-e", "image", "audio", "realtime",
            "moderation", "transcribe", "search", "davinci", "babbage", "sora")

ERRORS = {
    openai.BadRequestError: "이 모델은 채팅 방식으로 쓸 수 없거나 요청이 맞지 않아요. 다른 모델을 골라 주세요",
    openai.AuthenticationError: "OpenAI 키가 틀렸어요. .env의 OPENAI_API_KEY를 확인해 주세요",
    openai.PermissionDeniedError: "이 키로는 그 모델을 쓸 수 없어요",
    openai.NotFoundError: "그 모델 이름을 찾지 못했어요. 모델 이름을 확인해 주세요",
    openai.RateLimitError: "너무 많이 불렀거나 크레딧이 부족해요. 잠시 뒤에 하거나 결제 상태를 확인해 주세요",
    openai.APIConnectionError: "OpenAI 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요",
}

st.set_page_config(page_title="챗봇", page_icon="💬")
st.title("💬 나의 챗봇")

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

client = OpenAI(api_key=api_key, base_url=API["chat"])


# 내 키로 쓸 수 있는 모델을 OpenAI에 직접 물어봄 → 새 모델이 나와도 코드 수정 없이 목록에 뜸
# 1시간 동안은 저장해 둔 목록을 다시 씀
@st.cache_data(ttl=3600)
def get_models(_client):
    try:
        models = _client.models.list()  # 🔌 API 호출 (모델 목록)
    except openai.OpenAIError:
        return [DEFAULT_MODEL]
    # models.data[i].id = 모델 이름
    names = sorted(m.id for m in models.data if not any(word in m.id for word in NOT_CHAT))
    return names or [DEFAULT_MODEL]


# 사이드바: 모델 고르기 + 직접 입력 + 대화 지우기
with st.sidebar:
    st.header("⚙️ 설정")
    choices = get_models(client)
    if DEFAULT_MODEL not in choices:
        choices.insert(0, DEFAULT_MODEL)
    model = st.selectbox("모델", choices, index=choices.index(DEFAULT_MODEL))
    st.caption(f"내 키로 쓸 수 있는 채팅 모델 {len(choices)}개")
    if st.button("모델 목록 새로 불러오기"):
        get_models.clear()
        st.rerun()
    custom = st.text_input("목록에 없는 모델 직접 입력 (비우면 위에서 고른 모델)")
    if custom.strip():
        model = custom.strip()
    system_prompt = st.text_area("챗봇 성격", "너는 친절한 한국어 도우미야. 쉽고 짧게 답해 줘.")
    if st.button("대화 지우기"):
        st.session_state["messages"] = []

# 대화 기록: Streamlit은 입력할 때마다 파일을 처음부터 다시 실행하므로 session_state에 보관
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("메시지를 입력하세요")
if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(  # 🔌 API 호출 (질문할 때마다 한 번)
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + st.session_state["messages"],
                stream=True,
            )
            # 답을 한 글자씩 받아서 바로바로 보여 줌
            answer = st.write_stream(stream)
            st.session_state["messages"].append({"role": "assistant", "content": answer})
        except openai.OpenAIError as e:
            message = next((text for kind, text in ERRORS.items() if isinstance(e, kind)), "답을 받지 못했어요. 잠시 뒤에 다시 해 주세요")
            st.error(message)

st.caption(f"출처: OpenAI · 지금 모델: {model}")
