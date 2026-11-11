import requests
import streamlit as st

FLASK_CHAT_URL = "http://127.0.0.1:5000/chat"
MAX_HISTORY = 20

st.set_page_config(page_title="웹 챗봇", page_icon="💬", layout="centered")
st.markdown(
    """
    <style>
    .block-container { max-width: 860px; padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("웹 챗봇")
st.caption("입력한 메시지는 Flask 서버를 거쳐 gpt-4o-mini에 전달됩니다.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "error" not in st.session_state:
    st.session_state.error = None

chat_area = st.container(height=520, border=True)
with chat_area:
    if not st.session_state.messages:
        st.caption("메시지를 입력하면 대화를 시작할 수 있습니다.")
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

if st.session_state.error:
    st.error(st.session_state.error)

with st.form("composer", clear_on_submit=True):
    message_col, button_col = st.columns([6, 1], vertical_alignment="bottom")
    user_text = message_col.text_input(
        "메시지",
        placeholder="메시지를 입력하세요",
        label_visibility="collapsed",
    )
    submitted = button_col.form_submit_button("전송", type="primary", use_container_width=True)

if submitted:
    text = user_text.strip()
    if not text:
        st.session_state.error = "메시지를 입력해 주세요."
        st.rerun()

    history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[-MAX_HISTORY:]
    ]
    st.session_state.messages.append({"role": "user", "content": text})
    st.session_state.error = None

    try:
        with st.spinner("답변을 작성하는 중..."):
            response = requests.post(
                FLASK_CHAT_URL,
                json={"message": text, "history": history},
                timeout=90,
            )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok:
            raise RuntimeError(data.get("error") or "요청에 실패했습니다.")
        reply = str(data.get("reply", "")).strip()
        if not reply:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")
        st.session_state.messages.append({"role": "assistant", "content": reply})
    except requests.RequestException:
        st.session_state.messages.pop()
        st.session_state.error = "Flask 서버에 연결하지 못했습니다. 터미널에서 python server.py 를 먼저 실행해 주세요."
    except RuntimeError as exc:
        st.session_state.messages.pop()
        st.session_state.error = str(exc)

    st.rerun()
