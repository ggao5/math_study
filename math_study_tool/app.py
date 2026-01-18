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

# --- 3. 状态管理 ---
# 增加了 scores 用于存储得分，is_finished 用于控制报告显示
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file
    st.session_state.scores = {}  # 格式: {题号: 分数}
    st.session_state.is_finished = False

# --- 4. 报告页面显示逻辑 ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    st.write(f"章节：**{selected_file.replace('.csv', '')}**")
    
    # 计算得分
    if st.session_state.scores:
        actual_scores = list(st.session_state.scores.values())
        avg_score = sum(actual_scores) / len(actual_scores)
        count = len(actual_scores)
    else:
        avg_score = 0
        count = 0

    col1, col2 = st.columns(2)
    col1.metric("已练习题目", f"{count} / {total_questions}")
    col2.metric("平均掌握度", f"{avg_score:.1f}")

    st.divider()
    
    # 个性化评价建议
    if avg_score >= 4.5:
        st.success(f"🌟 **太棒了！** 你的平均分是 {avg_score:.1f}。你已经近乎完美地掌握了本章内容，简直是数学小天才！可以放心挑战下一章了。")
        st.balloons()
    elif avg_score >= 4.0:
        st.success(f"👏 **表现出色！** 平均分 {avg_score:.1f} 说明你基本达到了“熟练”水平。再针对不稳的地方复习下，你就是最强的。")
    elif avg_score >= 3.0:
        st.info(f"👍 **继续努力！** 平均分 {avg_score:.1f}。你已经掌握了核心逻辑，但部分题目还需通过练习提高速度和准确度。")
    else:
        st.warning(f"📖 **需要加强哦！** 平均分只有 {avg_score:.1f}。建议你点击下方“重新开始”，对照解析再次仔细复习课件，把基础打牢。")

    if st.button("🔄 重新开始本章自测"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.rerun()
    st.stop() # 停止运行后续题目代码

# --- 5. 侧边栏题目跳转 ---
st.sidebar.divider()
st.sidebar.subheader("🎯 题目跳转")
jump_idx = st.sidebar.slider("选择题号", 1, total_questions, st.session_state.idx + 1)
if jump_idx != st.session_state.idx + 1:
    st.session_state.idx = jump_idx - 1
    st.session_state.show = False
    st.rerun()

# --- 6. 主界面题目显示 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]

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
            st.session_state.scores[st.session_state.idx] = i + 1
            if st.session_state.idx < total_questions - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.session_state.is_finished = True # 全部做完自动结束
            st.rerun()

# --- 7. 底部导航与结束按钮 ---
st.divider()
col_nav1, col_nav2, col_end = st.columns([1, 1, 2])

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

with col_end:
    # 允许学生提前结束自测看报告
    if st.button("🏁 结束自测并看报告", use_container_width=True, type="primary"):
        st.session_state.is_finished = True
        st.rerun()

st.sidebar.caption(f"总进度: {len(st.session_state.scores)} / {total_questions}")
