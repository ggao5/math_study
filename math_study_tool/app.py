import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 脚本
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# 强制让按钮在移动端横向排列的 CSS
st.markdown("""
    <style>
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    .stButton button {
        padding: 0px 2px !important;
        font-size: 12px !important;
        white-space: pre-wrap !important;
        height: 60px !important;
    }
    /* 侧边栏题号小方块样式 */
    .status-box {
        display: inline-block;
        width: 25px;
        height: 25px;
        margin: 2px;
        text-align: center;
        line-height: 25px;
        border-radius: 4px;
        font-size: 12px;
        color: white;
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
    st.session_state.confirm_end = False # 用于结束确认

# --- 4. 报告页面 ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    num_scored = len(st.session_state.scores)
    
    # 要求的统计信息
    st.subheader(f"完成情况：{num_scored} / {total_questions}")
    
    if num_scored > 0:
        avg_score = sum(st.session_state.scores.values()) / num_scored
        st.metric("平均掌握度", f"{avg_score:.1f}")
        
        if avg_score >= 4.0:
            st.success(f"🌟 非常出色！掌握度 {avg_score:.1f}。建议继续保持！")
        elif avg_score >= 3.0:
            st.info(f"👍 表现不错。掌握度 {avg_score:.1f}。部分知识点可以再巩固。")
        else:
            st.warning(f"📖 掌握度 {avg_score:.1f}。建议回到课件重新复习基础。")
    else:
        st.warning("你没有对任何题目进行评分。")

    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.session_state.confirm_end = False
        st.rerun()
    st.stop()

# --- 5. 侧边栏：题目完成状态面板 ---
st.sidebar.divider()
st.sidebar.subheader("题号状态")
cols = st.sidebar.columns(5) # 每行显示5个
for i in range(total_questions):
    status_color = "#2E8B57" if i in st.session_state.scores else "#DDDDDD"
    text_color = "white" if i in st.session_state.scores else "#666666"
    # 用 html 做一个小方块，并在侧边栏提供跳转
    if st.sidebar.button(f"{i+1}", key=f"side_{i}", use_container_width=True):
        st.session_state.idx = i
        st.session_state.show = False
        st.rerun()

# --- 6. 主界面 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]
st.write(f"### 第 {st.session_state.idx + 1} 题：")
st.write(render_mixed_content(row['Front']))

st.divider()

# 打分按钮
st.write("🎯 **点击评分并自动进入下一题：**")
cols_score = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if cols_score[i].button(f"{i+1}\n{labels[i]}", key=f"score_{i}"):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
        else:
            st.session_state.is_finished = True
        st.rerun()

# 解析显示
if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True, type="secondary"):
        st.session_state.show = True
        st.rerun()
else:
    st.success("### 解析：")
    st.write(render_mixed_content(row['Back']))

# --- 7. 底部导航与结束自测逻辑 ---
st.divider()
col_nav1, col_nav2, col_end = st.columns([1, 1, 2])

with col_nav1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.session_state.show = False
            st.rerun()

with col_nav2:
    if st.button("跳过 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1
            st.session_state.show = False
            st.rerun()
        else:
            st.session_state.confirm_end = True # 最后一题跳过触发确认
            st.rerun()

with col_end:
    if st.button("🏁 结束自测看报告", use_container_width=True, type="primary"):
        unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
        if unanswered:
            st.session_state.confirm_end = True
        else:
            st.session_state.is_finished = True
        st.rerun()

# --- 8. 弹窗确认逻辑 ---
if st.session_state.confirm_end:
    unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
    st.warning(f"⚠️ **还有题目未完成自评！**")
    if unanswered:
        st.write(f"未评分题号：{', '.join(map(str, unanswered))}")
        st.info("提示：你可以点击侧边栏的数字直接跳转到对应题目。")
    
    c1, c2 = st.columns(2)
    if c1.button("直接生成报告", use_container_width=True):
        st.session_state.is_finished = True
        st.session_state.confirm_end = False
        st.rerun()
    if c2.button("继续做题", use_container_width=True):
        st.session_state.confirm_end = False
        st.rerun()

# 侧边栏滑条同步
st.sidebar.divider()
st.sidebar.subheader("🎯 快速跳转")
jump = st.sidebar.slider("跳至题号", 1, total_questions, st.session_state.idx + 1)
if jump != st.session_state.idx + 1:
    st.session_state.idx = jump - 1
    st.session_state.show = False
    st.rerun()
