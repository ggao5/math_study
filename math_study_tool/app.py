import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
# 设为 wide 模式以充分利用电脑屏幕空间
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="wide")

# 强制注入渲染脚本和 CSS 修复逻辑
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
    /* 1. 修复侧边栏题号竖着显示的问题 */
    [data-testid="stSidebar"] button p {
        font-size: 14px !important;
        white-space: nowrap !important; /* 强制不换行，确保数字水平显示 */
        font-weight: bold;
    }
    
    /* 2. 移除侧边栏按钮的默认内边距，给数字更多空间 */
    [data-testid="stSidebar"] button {
        padding: 0px 2px !important;
        min-width: 40px !important; /* 确保能装下三位数 */
    }

    /* 3. 主界面 5 个评分按钮样式 */
    [data-testid="stMain"] .stButton button {
        height: auto !important;
        min-height: 50px;
        padding: 10px !important;
    }

    /* 4. 侧边栏按钮列间距微调 */
    [data-testid="column"] {
        gap: 0.3rem !important;
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
    st.error("路径错误，请检查仓库结构")
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
    st.subheader(f"完成进度：{num_scored} / {total_questions}")
    
    if num_scored > 0:
        avg_score = sum(st.session_state.scores.values()) / num_scored
        st.metric("平均掌握度", f"{avg_score:.1f}")
        
        if avg_score >= 4.0:
            st.success(f"🌟 非常出色！平均分 {avg_score:.1f}。")
        elif avg_score >= 3.0:
            st.info(f"👍 表现稳健。平均分 {avg_score:.1f}。")
        else:
            st.warning(f"📖 平均分 {avg_score:.1f}，建议复习。")
    
    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.show = False
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.session_state.confirm_end = False
        st.rerun()
    st.stop()

# --- 5. 侧边栏：紧凑型状态面板 (电脑端优化版) ---
st.sidebar.divider()
st.sidebar.subheader(f"总进度: {len(st.session_state.scores)}/{total_questions}")
st.sidebar.progress(len(st.session_state.scores) / total_questions)

# 为了让 35 这样的数字不竖着排，我们控制列数，并在 CSS 中强制不换行
cols_per_row = 4  # 侧边栏列数改为 4，给数字留更多横向宽度
rows = (total_questions // cols_per_row) + (1 if total_questions % cols_per_row != 0 else 0)

for r in range(rows):
    cols = st.sidebar.columns(cols_per_row)
    for c in range(cols_per_row):
        q_idx = r * cols_per_row + c
        if q_idx < total_questions:
            # 状态颜色：primary(彩色/已评), secondary(灰色/未评)
            btn_type = "primary" if q_idx in st.session_state.scores else "secondary"
            if cols[c].button(f"{q_idx+1}", key=f"nav_{q_idx}", type=btn_type, use_container_width=True):
                st.session_state.idx = q_idx
                st.session_state.show = False
                st.rerun()

# --- 6. 主界面 ---
st.title("🧮 数学竞赛练习")
row = df.iloc[st.session_state.idx]
st.info(f"📍 当前进度：第 {st.session_state.idx + 1} 题")

st.markdown(f"""<div style='padding:20px; border:1px solid #ddd; border-radius:10px; background-color:#f9f9f9;'>
    {render_mixed_content(row['Front'])}
</div>""", unsafe_allow_html=True)

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
    if st.button("🏁 结束自测并看报告", use_container_width=True, type="primary"):
        unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
        if unanswered:
            st.session_state.confirm_end = True
        else:
            st.session_state.is_finished = True
        st.rerun()

if st.session_state.confirm_end:
    unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
    st.warning(f"⚠️ **还有 {len(unanswered)} 道题目未进行掌握度评分！**")
    st.write(f"未评分题号：{', '.join(map(str, unanswered))}")
    ca, cb = st.columns(2)
    if ca.button("确认结束并看报告", use_container_width=True):
        st.session_state.is_finished = True
        st.session_state.confirm_end = False
        st.rerun()
    if cb.button("返回题目继续评分", use_container_width=True):
        st.session_state.confirm_end = False
        st.rerun()
