import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面设置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制注入 MathJax 脚本（这是你公式显示成功的核心原因，绝对不动）
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# CSS 样式 (保持原样)
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
    这是你测试成功的渲染逻辑：识别 $...$ 并修复反斜杠
    """
    if not isinstance(text, str): return str(text)
    
    # 1. 修复反斜杠
    text = text.replace('\\\\', '\\')
    
    # 2. 强制在 $ 前后加空格（这是诱导 MathJax 渲染的关键）
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

# --- 3. 界面显示 ---
st.title("🧮 数学竞赛练习")

# 显示问题 (保持 st.write 逻辑)
st.write("### 题目：")
st.write(render_mixed_content(row['Front']))

if not st.session_state.show:
    if st.button("查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.write("---")
    st.write("### 解析：")
    st.write(render_mixed_content(row['Back']))
    
    # --- 重点修改：打分按钮 ---
    st.write("#### 掌握程度：")
    cols = st.columns(5)
    # 这里定义中文含义
    labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
    
    for i in range(5):
        # 按钮文案设为 "数字+中文"，例如 "1 不懂"
        button_label = f"{i+1} {labels[i]}"
        if cols[i].button(button_label):
            if st.session_state.idx < len(df) - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.balloons()
                st.success("本章完成！")
            st.rerun()

# 侧边栏辅助功能
if st.sidebar.button("下一题"):
    if st.session_state.idx < len(df) - 1:
        st.session_state.idx += 1
        st.session_state.show = False
        st.rerun()
