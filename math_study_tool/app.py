import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入渲染脚本和“绝对优先级”着色 CSS
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
    /* 1. 强制手机端横向排列 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    [data-testid="column"] {
        flex: 1 !important;
        min-width: 0px !important;
    }
    
    /* 2. 强制按钮样式：不透明、带阴影、固定高度 */
    .stButton > button {
        width: 100% !important;
        height: 65px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: all 0.2s !important;
        opacity: 1 !important;
        display: block !important;
    }

    /* 3. 使用属性选择器强制涂色 (避开 nth-child 的结构偏差) */
    /* 红色 - 不懂 */
    div[data-testid="column"]:nth-child(1) button { background-color: #ff4b4b !important; color: white !important; }
    /* 橙色 - 模糊 */
    div[data-testid="column"]:nth-child(2) button { background-color: #ffa500 !important; color: white !important; }
    /* 黄色 - 懂了 */
    div[data-testid="column"]:nth-child(3) button { background-color: #ffd700 !important; color: #31333F !important; }
    /* 浅绿 - 熟练 */
    div[data-testid="column"]:nth-child(4) button { background-color: #90ee90 !important; color: #31333F !important; }
    /* 深绿 - 秒杀 */
    div[data-testid="column"]:nth-child(5) button { background-color: #2e8b57 !important; color: white !important; }

    /* 解决点击瞬间变透明的问题 */
    .stButton > button:active, .stButton > button:focus, .stButton > button:hover {
        opacity: 0.9 !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('\\\\', '\\')
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    return text

# --- 2. 目录处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("请确保 GitHub 中有 data 文件夹")
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
    st.title("📊 学习报告")
    if st.session_state.scores:
        avg = sum(st.session_state.scores.values()) / len(st.session_state.scores)
    else: avg = 0
    st.metric("平均掌握度", f"{avg:.1f}")
    if avg >= 4.0: st.success("🌟 掌握得非常好！")
    elif avg >= 3.0: st.info("👍 表现稳定，继续保持。")
    else: st.warning("📖 建议针对薄弱章节加强复习。")
    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.rerun()
    st.stop()

# --- 5. 主界面 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]
st.write(f"### 第 {st.session_state.idx + 1} 题：")
st.write(render_mixed_content(row['Front']))

st.divider()

# --- 掌握程度评分 (强制横排 + 强制着色) ---
st.write("🎯 **掌握程度自评：**")
cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]

for i in range(5):
    # 使用 st.button 并配合 CSS 定位涂色
    if cols[i].button(f"{i+1}\n{labels[i]}", key=f"eval_btn_{i}"):
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
            st.rerun()
        else:
            st.session_state.is_finished = True
            st.rerun()
with c3:
    if st.button("🏁 结束自测", use_container_width=True, type="primary"):
        st.session_state.is_finished = True
        st.rerun()
