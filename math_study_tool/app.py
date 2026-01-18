import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="wide")

# 强制注入 MathJax 配置，增强对复杂公式的识别
st.markdown("""
    <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      }
    };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 侧边栏数字不换行 */
    [data-testid="stSidebar"] button p {
        font-size: 14px !important;
        white-space: nowrap !important;
        font-weight: bold;
    }
    [data-testid="stSidebar"] button {
        padding: 0px 2px !important;
        min-width: 45px !important;
    }
    [data-testid="column"] { gap: 0.3rem !important; }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    
    # 步骤1: 修复双反斜杠问题（CSV读取常有的坑）
    text = text.replace('\\\\', '\\')
    
    # 步骤2: 关键修复 - 保护 LaTeX 反斜杠
    # 确保像 \frac, \pi, \sqrt 这种字符前面的反斜杠是干净的
    # 我们通过正则在 $ 符号包裹的内容中做轻微调整
    def fix_latex(match):
        content = match.group(0)
        # 移除可能误加的转义
        return content.replace('\\', '\\\\') 

    # 步骤3: 统一美元符号间距
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    
    return text

# --- 2. 数据处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("路径错误")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
selected_file = st.sidebar.selectbox("📚 选择章节", sorted(csv_files))

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    # 读取时显式处理转义字符
    try: return pd.read_csv(p, encoding='utf-8', escapechar=None)
    except: return pd.read_csv(p, encoding='gbk', escapechar=None)

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
        st.metric("平均掌握度", f"{avg_score:.1f}")
        if avg_score >= 4.0: st.success("🌟 非常出色！")
        elif avg_score >= 3.0: st.info("👍 表现不错。")
        else: st.warning("📖 建议复习。")
    if st.button("🔄 重新开始"):
        st.session_state.idx = 0; st.session_state.scores = {}; st.session_state.is_finished = False; st.rerun()
    st.stop()

# --- 5. 侧边栏 ---
st.sidebar.subheader(f"进度: {len(st.session_state.scores)}/{total_questions}")
cols_per_row = 4
rows = (total_questions // cols_per_row) + (1 if total_questions % cols_per_row != 0 else 0)
for r in range(rows):
    cols = st.sidebar.columns(cols_per_row)
    for c in range(cols_per_row):
        q_idx = r * cols_per_row + c
        if q_idx < total_questions:
            t = "primary" if q_idx in st.session_state.scores else "secondary"
            if cols[c].button(f"{q_idx+1}", key=f"nav_{q_idx}", type=t, use_container_width=True):
                st.session_state.idx = q_idx; st.session_state.show = False; st.rerun()

# --- 6. 主界面 ---
st.title("🧮 国际数学竞赛闪卡练习")
row = df.iloc[st.session_state.idx]
st.info(f"📍 当前题目：第 {st.session_state.idx + 1} 题")

# 使用 Markdown 渲染，并明确指定处理 LaTeX
st.markdown(render_mixed_content(row['Front']))

st.divider()

# 打分与解析
score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1; st.session_state.show = False
        else: st.session_state.is_finished = True
        st.rerun()

if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True; st.rerun()
else:
    st.success("### 💡 解析参考：")
    st.markdown(render_mixed_content(row['Back']))

# --- 7. 导航 ---
st.divider()
n1, n2, n3 = st.columns([1, 1, 2])
with n1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0: st.session_state.idx -= 1; st.session_state.show = False; st.rerun()
with n2:
    if st.button("跳过 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1: st.session_state.idx += 1; st.session_state.show = False; st.rerun()
with n3:
    if st.button("🏁 结束自测", use_container_width=True, type="primary"):
        if [i for i in range(total_questions) if i not in st.session_state.scores]: st.session_state.confirm_end = True
        else: st.session_state.is_finished = True
        st.rerun()

if st.session_state.confirm_end:
    st.warning("⚠️ 还有题目未评分！")
    if st.button("确认结束", use_container_width=True): st.session_state.is_finished = True; st.rerun()
    if st.button("返回继续", use_container_width=True): st.session_state.confirm_end = False; st.rerun()
