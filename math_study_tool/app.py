import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 脚本（公式显示的核心，保持不动）
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# CSS 样式
st.markdown("""
    <style>
    .card-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        font-size: 1.1em;
    }
    /* 让按钮更适合手机点击 */
    .stButton>button {
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('\\\\', '\\')
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    return text

# --- 2. 路径与数据处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("请确保 GitHub 仓库中有 data 文件夹")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
selected_file = st.sidebar.selectbox("📚 选择章节", sorted(csv_files))

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    try: return pd.read_csv(p, encoding='utf-8')
    except: return pd.read_csv(p, encoding='gbk')

df = load_data(selected_file)
total_questions = len(df)

# --- 状态管理 ---
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file

# --- 新增功能：侧边栏题目跳转 ---
st.sidebar.divider()
st.sidebar.subheader("🎯 题目跳转")
# 使用 slider (滑动条) 或 selectbox (下拉框) 
jump_idx = st.sidebar.slider("选择题号", 1, total_questions, st.session_state.idx + 1)
if jump_idx != st.session_state.idx + 1:
    st.session_state.idx = jump_idx - 1
    st.session_state.show = False
    st.rerun()

# --- 3. 界面显示 ---
st.title("🧮 数学竞赛练习")
st.caption(f"当前章节：{selected_file}")

row = df.iloc[st.session_state.idx]

# 显示问题
st.write(f"### 第 {st.session_state.idx + 1} 题：")
st.write(render_mixed_content(row['Front']))

if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.write("---")
    st.write("### 解析：")
    st.write(render_mixed_content(row['Back']))
    
    st.write("#### 掌握程度：")
    cols = st.columns(5)
    labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
    for i in range(5):
        if cols[i].button(f"{i+1} {labels[i]}"):
            if st.session_state.idx < total_questions - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.balloons()
                st.success("本章完成！")
            st.rerun()

# --- 新增功能：上一题 与 下一题 按钮 ---
st.divider()
col_nav1, col_nav2 = st.columns(2)

with col_nav1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.session_state.show = False
            st.rerun()

with col_nav2:
    if st.button("下一题 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
            st.rerun()

st.sidebar.caption(f"总进度: {st.session_state.idx + 1} / {total_questions}")
