import streamlit as st
import pandas as pd
import os
import re

# --- 页面配置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮", layout="centered")

# 自定义 CSS：美化卡片和按钮，适配微信手机端
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    .card-box {
        padding: 20px;
        border-radius: 15px;
        background-color: white;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        font-size: 1.1em;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心函数：修复 LaTeX 显示问题 ---
def fix_latex(text):
    """
    处理 CSV 中的 LaTeX 转义问题。
    1. 将双反斜杠还原为单反斜杠 (\\dots -> \dots)
    2. 确保 $ 符号周围没有干扰字符
    """
    if not isinstance(text, str):
        return str(text)
    
    # 还原转义的反斜杠
    text = text.replace('\\\\', '\\')
    
    # NotebookLM 导出的 LaTeX 经常使用 $...$
    # Streamlit 的 markdown 对 $ 比较敏感，我们确保它能被正确识别
    return text

# --- 路径处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("❌ 目录下未找到 'data' 文件夹")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]

if not csv_files:
    st.warning("⚠️ data 文件夹内没有 .csv 文件")
    st.stop()

# --- 侧边栏 ---
st.sidebar.title("📚 课程目录")
selected_file = st.sidebar.selectbox("选择章节：", sorted(csv_files))

# --- 加载数据 ---
@st.cache_data
def load_data(file_name):
    path = os.path.join(DATA_DIR, file_name)
    try:
        # 尝试常用编码
        return pd.read_csv(path, encoding='utf-8')
    except:
        return pd.read_csv(path, encoding='gbk')

df = load_data(selected_file)

# --- 状态管理 ---
if 'card_index' not in st.session_state or st.session_state.get('current_chapter') != selected_file:
    st.session_state.card_index = 0
    st.session_state.show_answer = False
    st.session_state.current_chapter = selected_file
    st.session_state.scores = {}

# --- 页面主体 ---
st.title("🧮 国际数学竞赛自测")
st.write(f"当前章节：**{selected_file.replace('.csv', '')}**")

total_cards = len(df)
current_idx = st.session_state.card_index
row = df.iloc[current_idx]

# 进度条
st.progress((current_idx + 1) / total_cards)
st.caption(f"题目进度：{current_idx + 1} / {total_cards}")

# --- 题目显示 ---
st.markdown("#### 📝 问题：")
# 重点：处理 LaTeX 后再显示
q_content = fix_latex(row['Front'])
st.markdown(f'<div class="card-box">{q_content}</div>', unsafe_allow_html=True)

if not st.session_state.show_answer:
    if st.button("🔍 查看解析"):
        st.session_state.show_answer = True
        st.rerun()

# --- 答案与打分 ---
if st.session_state.show_answer:
    st.markdown("#### 💡 解析：")
    a_content = fix_latex(row['Back'])
    st.markdown(f'<div class="card-box" style="border-left: 5px solid #28a745;">{a_content}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.write("🎯 **请评价你的掌握程度：**")
    cols = st.columns(5)
    labels = ["完全不会", "有点懵", "基本懂", "熟练", "秒杀"]
    for i in range(5):
        if cols[i].button(f"{i+1}\n{labels[i]}"):
            st.session_state.scores[current_idx] = i + 1
            if current_idx < total_cards - 1:
                st.session_state.card_index += 1
                st.session_state.show_answer = False
            else:
                st.balloons()
                st.success("🎉 本章练习完成！")
            st.rerun()

# --- 底部控制 ---
st.sidebar.divider()
c1, c2 = st.sidebar.columns(2)
if c1.button("⬅️ 上一题"):
    if st.session_state.card_index > 0:
        st.session_state.card_index -= 1
        st.session_state.show_answer = False
        st.rerun()
if c2.button("下一题 ➡️"):
    if st.session_state.card_index < total_cards - 1:
        st.session_state.card_index += 1
        st.session_state.show_answer = False
        st.rerun()
