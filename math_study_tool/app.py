import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="wide")

# 强制注入 MathJax 3.0 配置，确保它能扫描到动态生成的 DOM
st.markdown("""
    <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        packages: {'[+]': ['base', 'ams', 'noerrors', 'noundefined']}
      },
      options: {
        renderActions: {
          addMenu: [] // 禁用右键菜单以减少干扰
        }
      },
      loader: {load: ['[tex]/ams']}
    };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# 强制 CSS 修复
st.markdown("""
    <style>
    [data-testid="stSidebar"] button p { font-size: 14px !important; white-space: nowrap !important; font-weight: bold; }
    [data-testid="stSidebar"] button { padding: 0px 2px !important; min-width: 45px !important; }
    [data-testid="column"] { gap: 0.3rem !important; }
    /* 解析区域字体稍微调大，增加阅读舒适度 */
    .latex-container { font-size: 1.1rem; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    
    # 核心保护逻辑：
    # 1. 先把 CSV 中可能存在的转义双斜杠 \\ 还原成单斜杠 \
    text = text.replace('\\\\', '\\')
    
    # 2. 关键修复：Streamlit 的 Markdown 引擎在处理 LaTeX 时，
    # 往往需要双反斜杠 \\ 才能正确传递给前端 MathJax。
    # 我们用正则找到所有 $ $ 内部的内容，并将里面的 \ 替换为 \\
    def latex_replacer(match):
        formula = match.group(0)
        # 将公式内部的所有单斜杠 \ 变成双斜杠 \\ 供 Markdown 传输
        # 但不要重复增加已经有的双斜杠
        fixed_formula = formula.replace('\\', '\\\\')
        return fixed_formula

    # 匹配 $...$ (行内公式) 和 $$...$$ (独立公式)
    text = re.sub(r'\$\$.*?\$\$|\$.*?\$', latex_replacer, text, flags=re.DOTALL)
    
    return text

# --- 2. 数据处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    # 使用 keep_default_na=False 避免将空单元格识别为 NaN
    try: return pd.read_csv(p, encoding='utf-8', keep_default_na=False)
    except: return pd.read_csv(p, encoding='gbk', keep_default_na=False)

# 选择文件逻辑保持不变...
csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
if not csv_files:
    st.error("Data 文件夹下没有 CSV 文件")
    st.stop()
selected_file = st.sidebar.selectbox("📚 选择章节", sorted(csv_files))
df = load_data(selected_file)
total_questions = len(df)

# --- 3. 状态管理 ---
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file
    st.session_state.scores = {}
    st.session_state.is_finished = False

# --- 4. 报告页面 (保持不变) ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    num_scored = len(st.session_state.scores)
    st.subheader(f"完成情况：{num_scored} / {total_questions}")
    if num_scored > 0:
        avg = sum(st.session_state.scores.values()) / num_scored
        st.metric("平均掌握度", f"{avg:.1f}")
    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0; st.session_state.scores = {}; st.session_state.is_finished = False; st.rerun()
    st.stop()

# --- 5. 侧边栏 (保持不变) ---
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
# 题目显示
st.markdown(render_mixed_content(row['Front']))

st.divider()

# 打分按钮
score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1; st.session_state.show = False
        else: st.session_state.is_finished = True
        st.rerun()

# --- 解析显示逻辑 (增加重渲染保护) ---
if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.success("### 💡 解析参考：")
    # 使用容器包装解析内容，确保样式独立
    with st.container():
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
        st.session_state.is_finished = True; st.rerun()
