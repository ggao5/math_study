import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="wide")

# 强制注入 MathJax 3.0。保持原有配置不动，确保 LaTeX 渲染优秀
st.markdown("""
    <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      },
      options: {
        ignoreHtmlClass: 'tex2jax_ignore',
        processHtmlClass: 'tex2jax_process'
      }
    };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# 侧边栏样式修复
st.markdown("""
    <style>
    [data-testid="stSidebar"] button p { font-size: 14px !important; white-space: nowrap !important; font-weight: bold; }
    [data-testid="stSidebar"] button { padding: 0px 2px !important; min-width: 45px !important; }
    [data-testid="stMain"] .stButton button { white-space: pre-wrap !important; height: auto !important; min-height: 60px; }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    text = text.replace('\\\\', '\\')
    return text

# --- 2. 数据处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    try: return pd.read_csv(p, encoding='utf-8', keep_default_na=False, escapechar=None)
    except: return pd.read_csv(p, encoding='gbk', keep_default_na=False, escapechar=None)

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
if not csv_files:
    st.error("请检查 data 文件夹")
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
    st.session_state.confirm_end = False # 新增：用于结束前的二次确认状态

# --- 4. 报告页面 ---
if st.session_state.is_finished:
    st.title("📊 学习成果报告")
    num_scored = len(st.session_state.scores)
    st.subheader(f"完成情况：{num_scored} / {total_questions}")
    
    if num_scored > 0:
        avg = sum(st.session_state.scores.values()) / num_scored
        st.metric("平均掌握度", f"{avg:.1f}")
        
        # 针对平均分的反馈建议
        if avg >= 4.0:
            st.success(f"🌟 非常出色！你的平均掌握度达到了 {avg:.1f}。看来你已经基本吃透了本章内容，请继续保持这种势头！")
        elif avg >= 3.0:
            st.info(f"👍 表现不错。你的平均掌握度为 {avg:.1f}。大部分知识点已掌握，建议针对“模糊”的题目再进行专项巩固。")
        else:
            st.warning(f"📖 掌握度较低 ({avg:.1f})。建议回到课件重新复习基础知识，并尝试重新推导解析中的公式。")
    else:
        st.write("未进行任何评分，暂无报告数据。")

    if st.button("🔄 重新开始本章"):
        st.session_state.idx = 0
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.session_state.confirm_end = False
        st.rerun()
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
st.title("🧮 高老师的国际数学竞赛闪卡练习")
row = df.iloc[st.session_state.idx]
st.info(f"📍 当前题目：第 {st.session_state.idx + 1} 题")

st.write(render_mixed_content(row['Front']))
st.divider()

# 打分按钮
score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1; st.session_state.show = False
        else:
            # 最后一题打完分后，自动进入完成状态
            st.session_state.is_finished = True 
        st.rerun()

# 解析显示
if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True; st.rerun()
else:
    st.success("### 💡 解析参考：")
    st.write(render_mixed_content(row['Back']))

# --- 7. 导航与确认逻辑 ---
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
        # 点击后进入二次确认阶段
        st.session_state.confirm_end = True
        st.rerun()

# --- 二次确认弹窗界面 ---
if st.session_state.confirm_end:
    unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
    
    st.markdown("---")
    if unanswered:
        st.warning(f"⚠️ **还有 {len(unanswered)} 道题未进行掌握度评分！**")
        st.write(f"未评分题号：{', '.join(map(str, unanswered))}")
    else:
        st.info("🎉 所有题目已完成评分！")

    c1, c2 = st.columns(2)
    if c1.button("✅ 确认结束并看报告", use_container_width=True):
        st.session_state.is_finished = True
        st.session_state.confirm_end = False
        st.rerun()
    if c2.button("🔙 返回继续练习", use_container_width=True):
        st.session_state.confirm_end = False
        st.rerun()
