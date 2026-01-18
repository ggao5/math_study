import streamlit as st
import pandas as pd
import os
import random

# 设置网页标题和图标
st.set_page_config(page_title="国际数学竞赛刷题助手", page_icon="🧮")

# 自定义 CSS 让界面在手机微信端更美观
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #f0f2f6; }
    .score-btn { margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 竞赛数学闪卡自测")
st.caption("根据课件生成，支持 LaTeX 数学公式")

# 1. 自动获取 data 文件夹下的所有 CSV 文件
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    st.warning(f"请在程序目录下创建 '{DATA_DIR}' 文件夹并放入 CSV 文件。")
    st.stop()

csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

if not csv_files:
    st.error("❌ 文件夹内没有找到 CSV 文件！")
    st.stop()

# 2. 侧边栏：选择章节
st.sidebar.header("课程目录")
selected_file = st.sidebar.selectbox("选择要复习的章节：", csv_files)

# 3. 读取数据
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(os.path.join(DATA_DIR, file_path))
    return df

df = load_data(selected_file)

# 初始化 Session State（记录当前题目索引和状态）
if 'card_index' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.card_index = 0
    st.session_state.show_answer = False
    st.session_state.last_file = selected_file
    st.session_state.scores = {} # 记录每道题的打分

total_cards = len(df)
current_idx = st.session_state.card_index

# 4. 显示进度条
progress = (current_idx + 1) / total_cards
st.progress(progress)
st.write(f"进度：{current_idx + 1} / {total_cards}")

# --- 闪卡主体 ---
st.divider()

# 获取当前行数据 (处理 CSV 里的 Front 和 Back 列)
row = df.iloc[current_idx]

# 显示正面
st.info("**【问题】**")
st.markdown(row['Front'])

# 5. 显示/隐藏答案
if st.button("🔍 查看解析 (Check Answer)"):
    st.session_state.show_answer = True

if st.session_state.show_answer:
    st.success("**【解析】**")
    st.markdown(row['Back'])
    
    st.divider()
    
    # 6. 打分制度
    st.write("📖 **请评估你对本题的掌握程度：**")
    cols = st.columns(5)
    score_labels = ["不懂", "模糊", "基本懂", "熟练", "秒杀"]
    
    for i, label in enumerate(score_labels):
        if cols[i].button(f"{i+1}\n{label}"):
            # 记录打分（你可以扩展这里，将数据保存到本地或数据库）
            st.session_state.scores[current_idx] = i + 1
            st.toast(f"已记录评分：{i+1} 分！")
            
            # 自动跳到下一题
            if current_idx < total_cards - 1:
                st.session_state.card_index += 1
                st.session_state.show_answer = False
                st.rerun()
            else:
                st.balloons()
                st.success("🎉 太棒了！本章节已复习完毕！")

# 7. 控制按钮
st.sidebar.divider()
col_prev, col_next = st.sidebar.columns(2)
if col_prev.button("⬅️ 上一题"):
    if st.session_state.card_index > 0:
        st.session_state.card_index -= 1
        st.session_state.show_answer = False
        st.rerun()

if col_next.button("下一题 ➡️"):
    if st.session_state.card_index < total_cards - 1:
        st.session_state.card_index += 1
        st.session_state.show_answer = False
        st.rerun()

# 8. 导出本日学习报告 (简单版)
if st.sidebar.button("📊 生成练习总结"):
    if st.session_state.scores:
        score_df = pd.DataFrame(list(st.session_state.scores.items()), columns=['题号', '得分'])
        avg_score = score_df['得分'].mean()
        st.sidebar.write(f"平均掌握度：{avg_score:.2f} / 5.0")
        st.sidebar.write("建议重点复习低于 3 分的题目。")
    else:
        st.sidebar.write("暂无评分数据")