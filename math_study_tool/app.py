import streamlit as st
import pandas as pd
import os
import re

# --- 页面设置 ---
st.set_page_config(page_title="国际数学竞赛自测", page_icon="🧮", layout="centered")

# CSS 美化：增加卡片质感，优化移动端间距
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; margin-bottom: 5px; }
    .card-box {
        padding: 24px;
        border-radius: 15px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        font-size: 1.15em;
        line-height: 1.6;
    }
    .score-text { font-size: 0.8em; color: #666; display: block; }
    </style>
    """, unsafe_allow_html=True)

def fix_latex_format(text):
    """
    处理数学公式：
    1. 修复双反斜杠
    2. 确保 $ 符号前后有空格，否则 Streamlit 的 Markdown 引擎不识别
    """
    if not isinstance(text, str): return str(text)
    text = text.replace('\\\\', '\\')
    # 在 $ 符号前后强制增加空格，这是 Streamlit 渲染成功的秘诀
    text = text.replace('$', ' $ ')
    return text

# --- 目录处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    st.error("❌ 找不到 data 文件夹")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
if not csv_files:
    st.warning("⚠️ data 文件夹内为空")
    st.stop()

# 侧边栏
selected_file = st.sidebar.selectbox("📖 选择章节", sorted(csv_files))

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
    st.session_state.history = {}

total = len(df)
curr = st.session_state.idx
row = df.iloc[curr]

# --- 界面 ---
st.title("🏆 竞赛数学闪卡")
st.write(f"当前章节：**{selected_file.replace('.csv', '')}**")
st.progress((curr + 1) / total)

# 问题区
st.markdown("#### 📝 问题")
q_text = fix_latex_format(row['Front'])
st.markdown(f'<div class="card-box">{q_text}</div>', unsafe_allow_html=True)

if not st.session_state.show:
    if st.button("🔍 查看解析"):
        st.session_state.show = True
        st.rerun()
else:
    # 解析区
    st.markdown("#### 💡 解析")
    a_text = fix_latex_format(row['Back'])
    st.markdown(f'<div class="card-box" style="border-left: 5px solid #28a745;">{a_text}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # 打分评价区（带中文标签）
    st.write("🎯 **请评估掌握程度：**")
    cols = st.columns(5)
    # 分数对应的中文释义
    labels = ["不懂", "吃力", "基本懂", "熟练", "秒杀"]
    
    for i in range(5):
        # 按钮显示为：数字 + 换行 + 中文
        btn_label = f"{i+1}\n{labels[i]}"
        if cols[i].button(btn_label):
            st.session_state.history[curr] = i + 1
            if curr < total - 1:
                st.session_state.idx += 1
                st.session_state.show = False
                st.rerun()
            else:
                st.balloons()
                st.success("🎉 本章练习已完成！")

# 侧边栏控制
st.sidebar.divider()
if st.sidebar.button("⬅️ 上一题"):
    if st.session_state.idx > 0:
        st.session_state.idx -= 1
        st.session_state.show = False
        st.rerun()

if st.sidebar.button("🔄 重置进度"):
    st.session_state.idx = 0
    st.session_state.show = False
    st.rerun()
