import streamlit as st
import pandas as pd
import os
import re

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# 强制加载 MathJax 脚本（这是公式显示的“救命稻草”）
st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

def render_mixed_content(text):
    """
    这是你刚刚觉得“显示是对的”那个核心逻辑
    """
    if not isinstance(text, str): return str(text)
    # 修复反斜杠
    text = text.replace('\\\\', '\\')
    # 强制在 $ 符号前后加空格，诱导引擎识别 LaTeX
    text = re.sub(r'(\d)\$', r'\1 $', text)
    text = re.sub(r'\$(\d)', r'$ \1', text)
    # 针对你提到的 a, a+1, \dots, b 的特殊处理
    text = text.replace('$', ' $ ') 
    return text

# --- 2. 目录处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("请确保 GitHub 中有 data 文件夹")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
selected_file = st.sidebar.selectbox("选择章节：", sorted(csv_files))

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    try: return pd.read_csv(p, encoding='utf-8')
    except: return pd.read_csv(p, encoding='gbk')

df = load_data(selected_file)

# 状态初始化
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file

row = df.iloc[st.session_state.idx]

# --- 3. 界面显示 ---
st.title("🧮 数学竞赛练习")

# 使用 st.write 而不是 st.markdown 来确保公式渲染稳定
st.write("### 题目：")
st.write(render_mixed_content(row['Front']))

if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.write("---")
    st.write("### 解析：")
    st.write(render_mixed_content(row['Back']))
    
    st.write("#### 🎯 掌握程度：")
    # 重新加回来的 1-5 分和中文说明
    cols = st.columns(5)
    labels = ["不懂", "模糊", "基本懂", "熟练", "秒杀"]
    
    for i in range(5):
        # 按钮文案采用 数字+中文
        if cols[i].button(f"{i+1}\n{labels[i]}"):
            if st.session_state.idx < len(df) - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.balloons()
                st.success("恭喜完成本章！")
            st.rerun()

# 侧边栏辅助功能
if st.sidebar.button("下一题 ➡️"):
    if st.session_state.idx < len(df) - 1:
        st.session_state.idx += 1
        st.session_state.show = False
        st.rerun()

st.sidebar.caption(f"进度: {st.session_state.idx + 1} / {len(df)}")
