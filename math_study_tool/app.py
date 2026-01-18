import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 和 强制横排按钮的 CSS
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
    /* 核心修复：强迫 st.columns 在手机端也不换行 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
    }
    [data-testid="column"] {
        width: 20% !important; /* 均分 5 份 */
        min-width: 0px !important;
        flex-shrink: 1 !important;
    }
    
    /* 按钮美化与颜色分级 */
    .stButton button {
        width: 100% !important;
        padding: 5px 2px !important;
        font-size: 11px !important;
        height: 55px !important;
        white-space: pre-wrap !important;
        border: none !important;
        color: white !important;
    }
    
    /* 针对 1-5 分的特定颜色设置 */
    /* 不懂-深红, 模糊-橙色, 懂了-黄色, 熟练-浅绿, 秒杀-深绿 */
    div[data-testid="column"]:nth-of-type(1) button { background-color: #e63946 !important; }
    div[data-testid="column"]:nth-of-type(2) button { background-color: #f4a261 !important; }
    div[data-testid="column"]:nth-of-type(3) button { background-color: #e9c46a !important; color: black !important; }
    div[data-testid="column"]:nth-of-type(4) button { background-color: #2a9d8f !important; }
    div[data-testid="column"]:nth-of-type(5) button { background-color: #1d3557 !important; }
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

# --- 4. 报告展示逻辑 ---
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

# --- 关键点：五个掌握程度按钮 ---
st.write("🎯 **掌握程度自评 (点击自动下一题)：**")
# 使用 columns 配合 CSS 强制不换行
cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    # 这里通过 key 来区分按钮，CSS 负责给这些按钮上色
    if cols[i].button(f"{i+1}\n{labels[i]}", key=f"btn_{i}"):
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
