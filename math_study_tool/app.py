import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 和 强制横排按钮及颜色的 CSS
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
    /* 1. 强制手机端不换行 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    [data-testid="column"] {
        flex: 1 !important;
        min-width: 0px !important;
    }
    
    /* 2. 统一按钮基础样式，解决透明问题 */
    .stButton button {
        width: 100% !important;
        height: 60px !important;
        border-radius: 8px !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        white-space: pre-wrap !important;
        line-height: 1.2 !important;
        opacity: 1 !important; /* 确保不透明 */
    }

    /* 3. 分级颜色定义 (从红色渐变到绿色) */
    /* 1-不懂: 红色 */
    div[data-testid="column"]:nth-of-type(1) button { background-color: #FF4B4B !important; }
    /* 2-模糊: 橙色 */
    div[data-testid="column"]:nth-of-type(2) button { background-color: #FFA500 !important; }
    /* 3-懂了: 黄色 (黑字更清晰) */
    div[data-testid="column"]:nth-of-type(3) button { background-color: #FFD700 !important; color: #31333F !important; }
    /* 4-熟练: 浅绿 */
    div[data-testid="column"]:nth-of-type(4) button { background-color: #90EE90 !important; color: #31333F !important; }
    /* 5-秒杀: 深绿 */
    div[data-testid="column"]:nth-of-type(5) button { background-color: #2E8B57 !important; }

    /* 修复按钮悬停时变透明的问题 */
    .stButton button:hover {
        opacity: 0.8 !important;
        color: inherit !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('\\\\', '\\')
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    return text

# --- 2. 数据处理 ---
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

# --- 3. 状态管理 ---
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file
    st.session_state.scores = {}
    st.session_state.is_finished = False

# --- 4. 报告页面 ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    if st.session_state.scores:
        avg_score = sum(st.session_state.scores.values()) / len(st.session_state.scores)
        count = len(st.session_state.scores)
    else:
        avg_score, count = 0, 0

    st.metric("平均掌握度", f"{avg_score:.1f}")
    if avg_score >= 4.0: st.success(f"🌟 非常出色！掌握度 {avg_score:.1f}。")
    elif avg_score >= 3.0: st.info(f"👍 表现不错。掌握度 {avg_score:.1f}。")
    else: st.warning(f"📖 掌握度 {avg_score:.1f}。建议重新复习。")

    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.rerun()
    st.stop()

# --- 5. 主界面内容 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]
st.write(f"### 第 {st.session_state.idx + 1} 题：")
st.write(render_mixed_content(row['Front']))

st.divider()

# --- 掌握程度按钮 (已应用颜色分级) ---
st.write("🎯 **掌握程度自评：**")
cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if cols[i].button(f"{i+1}\n{labels[i]}", key=f"eval_{i}"):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
        else:
            st.session_state.is_finished = True
        st.rerun()

# --- 解析区 ---
if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.info("### 解析：")
    st.write(render_mixed_content(row['Back']))

# --- 底部导航 ---
st.divider()
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.session_state.show = False
            st.rerun()
with c2:
    if st.button("跳过 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
        else:
            st.session_state.is_finished = True
        st.rerun()
with c3:
    if st.button("🏁 结束并看报告", use_container_width=True, type="primary"):
        st.session_state.is_finished = True
        st.rerun()
