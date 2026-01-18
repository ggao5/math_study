import streamlit as st
import pandas as pd
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="竞赛数学闪卡", page_icon="🧮")

# --- 2. 核心公式清洗函数 ---
def clean_latex(text):
    if not isinstance(text, str):
        return str(text)
    # 修复 NotebookLM 常见的双反斜杠转义
    text = text.replace('\\\\', '\\')
    # 秘诀：在 $ 符号前后强行加空格，防止文字紧贴公式导致不渲染
    text = text.replace('$', ' $ ')
    return text

# --- 3. 路径处理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 自动获取 CSV 文件
if os.path.exists(DATA_DIR):
    csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
else:
    st.error("未找到 data 文件夹")
    st.stop()

if not csv_files:
    st.warning("data 文件夹里没有 CSV 文件")
    st.stop()

# 侧边栏
selected_file = st.sidebar.selectbox("选择章节：", sorted(csv_files))

@st.cache_data
def load_data(name):
    p = os.path.join(DATA_DIR, name)
    try:
        return pd.read_csv(p, encoding='utf-8')
    except:
        return pd.read_csv(p, encoding='gbk')

df = load_data(selected_file)

# 状态初始化
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file

row = df.iloc[st.session_state.idx]

# --- 4. 页面显示 ---
st.title("🏆 数学竞赛自测")
st.caption(f"当前章节：{selected_file}")

# 题目显示：直接使用 st.write，不要加任何 HTML 标签
st.subheader("问题：")
st.write(clean_latex(row['Front']))

st.divider()

if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True
        st.rerun()
else:
    st.subheader("解析：")
    st.write(clean_latex(row['Back']))
    
    st.write("---")
    st.write("🎯 **掌握程度评价：**")
    
    # 恢复你要求的带中文解释的 1-5 分按钮
    cols = st.columns(5)
    labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
    
    for i in range(5):
        if cols[i].button(f"{i+1}\n{labels[i]}"):
            if st.session_state.idx < len(df) - 1:
                st.session_state.idx += 1
                st.session_state.show = False
            else:
                st.balloons()
                st.success("本章练习完成！")
            st.rerun()

# 侧边栏进度控制
st.sidebar.write(f"进度: {st.session_state.idx + 1} / {len(df)}")
if st.sidebar.button("下一题 ➡️"):
    if st.session_state.idx < len(df) - 1:
        st.session_state.idx += 1
        st.session_state.show = False
        st.rerun()
