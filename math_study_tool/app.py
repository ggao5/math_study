import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="wide")

# 强制注入 MathJax 脚本
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# 强制 CSS 修复：题号水平显示 + 侧边栏样式
st.markdown("""
    <style>
    /* 1. 确保侧边栏数字水平显示，不换行 */
    [data-testid="stSidebar"] button p {
        font-size: 14px !important;
        white-space: nowrap !important;
        font-weight: bold;
    }
    
    [data-testid="stSidebar"] button {
        padding: 0px 2px !important;
        min-width: 45px !important;
    }

    /* 2. 评分按钮样式 */
    [data-testid="stMain"] .stButton button {
        white-space: pre-wrap !important;
        height: auto !important;
        min-height: 60px;
    }

    /* 3. 侧边栏列间距 */
    [data-testid="column"] {
        gap: 0.3rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    # 核心 LaTeX 预处理，保持不变
    text = text.replace('\\\\', '\\')
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    return text

# --- 2. 数据处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("路径错误，请检查 data 文件夹")
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
    st.session_state.confirm_end = False

# --- 4. 报告页面 ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    num_scored = len(st.session_state.scores)
    st.subheader(f"完成情况：{num_scored} / {total_questions}")
    
    if num_scored > 0:
        avg_score = sum(st.session_state.scores.values()) / num_scored
        st.metric("平均掌握度分数", f"{avg_score:.1f}")
        
        if avg_score >= 4.0:
            st.success(f"🌟 非常出色！平均分 {avg_score:.1f}。")
        elif avg_score >= 3.0:
            st.info(f"👍 表现不错。平均分 {avg_score:.1f}。")
        else:
            st.warning(f"📖 平均分 {avg_score:.1f}。建议复习。")
    
    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.session_state.confirm_end = False
        st.rerun()
    st.stop()

# --- 5. 侧边栏：紧凑型状态面板 (4列布局确保数字不竖排) ---
st.sidebar.divider()
st.sidebar.subheader(f"进度: {len(st.session_state.scores)}/{total_questions}")
st.sidebar.progress(len(st.session_state.scores) / total_questions)

cols_per_row = 4
rows = (total_questions // cols_per_row) + (1 if total_questions % cols_per_row != 0 else 0)

for r in range(rows):
    cols = st.sidebar.columns(cols_per_row)
    for c in range(cols_per_row):
        q_idx = r * cols_per_row + c
        if q_idx < total_questions:
            btn_type = "primary" if q_idx in st.session_state.scores else "secondary"
            if cols[c].button(f"{q_idx+1}", key=f"nav_{q_idx}", type=btn_type, use_container_width=True):
                st.session_state.idx = q_idx
                st.session_state.show = False
                st.rerun()

# --- 6. 主界面 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]

# --- 修复核心：恢复 st.write，不使用 HTML div ---
st.info(f"📍 当前题目：第 {st.session_state.idx + 1} 题")
st.write(render_mixed_content(row['Front']))

st.divider()

# 打分按钮
st.write("🎯 **请评估你对本题的掌握程度：**")
score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
        else:
            st.session_state.is_finished = True
        st.rerun()

# 解析
if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.success("### 💡 解析参考：")
    st.write(render_mixed_content(row['Back']))

# --- 7. 导航确认逻辑 ---
st.divider()
n1, n2, n3 = st.columns([1, 1, 2])
with n1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.session_state.show = False
            st.rerun()
with n2:
    if st.button("跳过 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
            st.rerun()
with n3:
    if st.button("🏁 结束自测查看报告", use_container_width=True, type="primary"):
        unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
        if unanswered:
            st.session_state.confirm_end = True
        else:
            st.session_state.is_finished = True
        st.rerun()

if st.session_state.confirm_end:
    unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
    st.warning(f"⚠️ **提醒：还有 {len(unanswered)} 道题目未进行评分！**")
    st.write(f"未评分题号：{', '.join(map(str, unanswered))}")
    ca, cb = st.columns(2)
    if ca.button("确认结束直接看报告", use_container_width=True):
        st.session_state.is_finished = True
        st.session_state.confirm_end = False
        st.rerun()
    if cb.button("返回题目继续评分", use_container_width=True):
        st.session_state.confirm_end = False
        st.rerun()
