import streamlit as st
import pandas as pd
import os

# --- 页面配置 ---
st.set_page_config(page_title="竞赛数学闪卡自测", page_icon="🧪", layout="centered")

# 自定义 CSS：美化卡片和按钮，适配微信手机端
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    .card-box {
        padding: 25px;
        border-radius: 15px;
        background-color: white;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        min-height: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 路径处理 ---
# 自动定位到当前脚本目录下的 data 文件夹
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 检查 data 目录
if not os.path.exists(DATA_DIR):
    st.error(f"❌ 未找到 'data' 文件夹。请在 GitHub 仓库根目录创建 data 文件夹。")
    st.stop()

# 获取所有 CSV 文件，过滤掉隐藏文件和文件夹
csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]

if not csv_files:
    st.warning("⚠️ data 文件夹内没有找到任何 .csv 文件，请检查上传。")
    st.stop()

# --- 侧边栏：章节选择 ---
st.sidebar.title("📚 课程章节")
selected_file = st.sidebar.selectbox("请选择要复习的课件：", sorted(csv_files))

# --- 加载数据 ---
@st.cache_data
def load_data(file_name):
    path = os.path.join(DATA_DIR, file_name)
    # 使用 utf-8 编码读取，防止中文乱码
    try:
        return pd.read_csv(path)
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
st.title("🧮 数学竞赛练习")
st.write(f"当前章节：**{selected_file.replace('.csv', '')}**")

total_cards = len(df)
current_idx = st.session_state.card_index

# 进度条
progress = (current_idx + 1) / total_cards
st.progress(progress)
st.caption(f"进度：{current_idx + 1} / {total_cards}")

# --- 题目卡片显示 ---
row = df.iloc[current_idx]

st.markdown("### 📝 问题 (Question)")
st.markdown(f'<div class="card-box">{row["Front"]}</div>', unsafe_allow_html=True)

# 按钮：查看答案
if not st.session_state.show_answer:
    if st.button("👁️ 点击查看解析"):
        st.session_state.show_answer = True
        st.rerun()

# 答案区域
if st.session_state.show_answer:
    st.markdown("### 💡 解析 (Analysis)")
    st.markdown(f'<div class="card-box" style="border-left: 5px solid #28a745;">{row["Back"]}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # --- 掌握度打分制度 ---
    st.write("🎯 **这道题你掌握得如何？**")
    cols = st.columns(5)
    score_labels = ["不懂", "吃力", "基本懂", "熟练", "秒杀"]
    
    for i in range(5):
        if cols[i].button(f"{i+1}\n{score_labels[i]}"):
            # 记录得分
            st.session_state.scores[current_idx] = i + 1
            # 自动进入下一题
            if current_idx < total_cards - 1:
                st.session_state.card_index += 1
                st.session_state.show_answer = False
            else:
                st.balloons()
                st.success("🏁 恭喜！本章已全部练习完毕！")
            st.rerun()

# --- 底部导航栏 ---
st.sidebar.divider()
col_prev, col_reset, col_next = st.sidebar.columns(3)

if col_prev.button("⬅️ 上一题"):
    if st.session_state.card_index > 0:
        st.session_state.card_index -= 1
        st.session_state.show_answer = False
        st.rerun()

if col_reset.button("🔄 重置"):
    st.session_state.card_index = 0
    st.session_state.show_answer = False
    st.session_state.scores = {}
    st.rerun()

if col_next.button("下一题 ➡️"):
    if st.session_state.card_index < total_cards - 1:
        st.session_state.card_index += 1
        st.session_state.show_answer = False
        st.rerun()

# --- 学习报告摘要 ---
if st.session_state.scores:
    st.sidebar.divider()
    st.sidebar.subheader("📊 本章统计")
    scores_list = list(st.session_state.scores.values())
    avg_score = sum(scores_list) / len(scores_list)
    st.sidebar.write(f"已完成题目：{len(scores_list)}")
    st.sidebar.write(f"平均熟练度：{avg_score:.1f} / 5.0")
