import streamlit as st
import requests

st.set_page_config(page_title="AI 阅读教练", layout="wide")
st.title("📚 AI 阅读教练 · 第一性原理视角")

# 初始化 session_state
if "report" not in st.session_state:
    st.session_state.report = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "messages" not in st.session_state:
    st.session_state.messages = []  # 存储 {"role": "user" or "assistant", "content": "..."}

uploaded_file = st.file_uploader("选择 PDF 文件", type="pdf")

# 分析按钮
if uploaded_file is not None and st.button("🚀 上传并分析"):
    with st.spinner("正在分析，可能需要 1-2 分钟..."):
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://localhost:8000/analyze", files=files)
        if response.status_code == 200:
            st.session_state.report = response.json()["report"]
            st.session_state.analyzed = True
            # 清空之前的对话历史（因为换了新书）
            st.session_state.messages = []
            st.success("分析完成！")
            st.rerun()
        else:
            st.error("分析失败，请确保后端已启动")

# 显示报告（如果已分析）
if st.session_state.analyzed and st.session_state.report:
    report = st.session_state.report
    with st.expander("📖 预处理", expanded=True):
        st.markdown(report["preprocess"])
    with st.expander("🔍 洞察ing", expanded=True):
        st.markdown(report["insight"])
    with st.expander("⚡ 批判ing", expanded=True):
        st.markdown(report["critique"])
    with st.expander("🚀 实践ing", expanded=True):
        st.markdown(report["practice"])
    with st.expander("🧠 内化ing", expanded=True):
        st.markdown(report["internalize"])
    
    st.subheader("💬 追问 （对话历史）")
    
    # 显示历史消息
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**你：** {msg['content']}")
        else:
            st.markdown(f"**AI：** {msg['content']}")
        st.divider()
    
    # 输入新问题
    question = st.text_input("输入你的问题", key="question_input")
    if st.button("提问") and question:
        with st.spinner("思考中..."):
            # 调用后端问答接口
            qr = requests.post(f"http://localhost:8000/ask_agent?question={question}")
            if qr.status_code == 200:
                answer = qr.json()["answer"]
                # 将用户问题和AI回答添加到历史
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.messages.append({"role": "assistant", "content": answer})
                # 清空输入框（通过重新运行刷新）
                st.rerun()
            else:
                st.error("提问失败")