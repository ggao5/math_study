import streamlit as st
import pandas as pd
import os
import re

# --- 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 脚本，确保浏览器级别的公式渲染
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# CSS 美化
st.markdown("""
    <style>
    .card-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    """
    终极渲染函数：识别文本中的 $...$ 并确保 Streamlit 能够正确处理。
    """
    if not isinstance(text, str): return str(text)
    
    # 1. 修复 NotebookLM 的双反斜杠问题
    text = text.replace('\\\\', '\\')
    
    # 2. 核心修复：Streamlit 的 markdown 要求 $ 符号前后必须有空格才能触发 LaTeX
    # 我们用正则在 $ 外侧强制加空格
    text = re.sub(r'(\d)\$', r'\1 $', text) # 数字后跟$加空格
    text = re.sub(r'\$(\d)', r'$ \1', text) # $后跟数字加空格
    
    return text

# --- 路径处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("请确保 GitHub 仓库中有 data 文件夹")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
if not csv_files:
    st.warning("data 文件夹里没看到 CSV 文件")
    st.stop()

selected_file = st.sidebar.selectbox("选择章节：", sorted(csv_files))

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    try: return pd.read_csv(p, encoding='utf-8')
    except: return pd.read_csv(p, encoding='gbk')

df = load_data(selected_file)

if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file

row = df.iloc[st.session_state.idx]

# --- 界面显示 ---
st.title("🧮 数学竞赛练习")

# 显示问题
st.write("### 题目：")
# 这里直接使用 st.write，它对混合 LaTeX 的处理比 st.markdown 有时更稳
st.write(render_mixed_content(row['Front']))

if not st.session_state.show:
    if st.button("查看解析"):
        st.session_state.show = True
        st.rerun()
else:
    st.write("---")
    st.write("### 解析：")
    st.write(render_mixed_content(row['Back']))
    
    # 打分按钮
    st.write("#### 掌握程度：")
    cols = st.columns(5)
    for i in range(5):
        if cols[i].button(f"{i+1}"):
            if st.session_state.idx < len(df) - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.success("本章完成！")
            st.rerun()

if st.sidebar.button("下一题"):
    if st.session_state.idx < len(df) - 1:
        st.session_state.idx += 1
        st.session_state.show = False
        st.rerun()
