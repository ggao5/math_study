import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# --- 1. 页面与环境设置 ---
st.set_page_config(page_title="竞赛数学闪卡系统", page_icon="🧮", layout="wide")

# MathJax 渲染脚本 (保持你最满意的版本)
st.markdown("""
    <script>
    window.MathJax = {
      tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$']], processEscapes: true },
      options: { ignoreHtmlClass: 'tex2jax_ignore', processHtmlClass: 'tex2jax_process' }
    };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """, unsafe_allow_html=True)

# 样式修复
st.markdown("""
    <style>
    [data-testid="stSidebar"] button p { font-size: 14px !important; white-space: nowrap !important; font-weight: bold; }
    [data-testid="stSidebar"] button { padding: 0px 2px !important; min-width: 45px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据持久化逻辑 ---
USER_DATA_FILE = "user_progress.json"

def load_all_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    return text.replace('\\\\', '\\')

# --- 3. 登录界面 ---
if 'user' not in st.session_state:
    st.title("🔐 高老师数学竞赛练习系统")
    tab1, tab2 = st.tabs(["学生登录", "新同学注册"])
    
    all_users = load_all_user_data()
    
    with tab1:
        login_name = st.text_input("请输入姓名/学号", key="login_name")
        if st.button("进入学习"):
            if login_name in all_users:
                st.session_state.user = login_name
                st.rerun()
            else:
                st.error("未找到该用户，请先注册。")
                
    with tab2:
        new_name = st.text_input("设置你的姓名/学号")
        if st.button("立即注册"):
            if new_name and new_name not in all_users:
                all_users[new_name] = {"history": {}}
                save_user_data(all_users)
                st.success("注册成功！请切换到登录页。")
            else:
                st.warning("用户已存在或名字为空。")
    st.stop()

# --- 4. 数据加载 ---
user_id = st.session_state.user
all_data = load_all_user_data()
user_record = all_data[user_id]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
selected_file = st.sidebar.selectbox("📚 选择章节", sorted(csv_files))

@st.cache_data
def load_quiz(name):
    p = os.path.join(DATA_DIR, name)
    return pd.read_csv(p, encoding='utf-8', keep_default_na=False, escapechar=None)

df = load_quiz(selected_file)
total_questions = len(df)

# 初始化/恢复该章节的进度
chapter_key = selected_file
if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file
    # 从本地数据恢复已做过的分数
    st.session_state.scores = user_record["history"].get(chapter_key, {})
    # 转换为整数键（JSON存储后会变字符串）
    st.session_state.scores = {int(k): v for k, v in st.session_state.scores.items()}
    st.session_state.is_finished = False

# --- 5. 报告逻辑 ---
if st.session_state.is_finished:
    st.title(f"📊 {user_id} 的学习报告")
    num_scored = len(st.session_state.scores)
    st.subheader(f"完成进度：{num_scored} / {total_questions}")
    
    if num_scored > 0:
        avg = sum(st.session_state.scores.values()) / num_scored
        st.metric("本章平均分", f"{avg:.1f}")
        # 保存进度到本地
        user_record["history"][chapter_key] = st.session_state.scores
        all_data[user_id] = user_record
        save_user_data(all_data)
        st.success("进度已永久保存在系统。")
        
    if st.button("🔄 重新挑战本章"):
        st.session_state.scores = {}
        st.session_state.is_finished = False
        st.rerun()
    if st.button("🚪 退出登录"):
        del st.session_state.user
        st.rerun()
    st.stop()

# --- 6. 侧边栏与主界面 (保持你原有的优秀逻辑) ---
st.sidebar.write(f"👤 当前学生：**{user_id}**")
st.sidebar.subheader(f"进度: {len(st.session_state.scores)}/{total_questions}")

# ... (侧边栏按钮矩阵代码保持不变) ...
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

st.title("🧮 国际数学竞赛闪卡")
row = df.iloc[st.session_state.idx]
st.info(f"📍 第 {st.session_state.idx + 1} 题")
st.write(render_mixed_content(row['Front']))
st.divider()

# 打分逻辑
score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        # 每打一次分就异步保存一次
        user_record["history"][chapter_key] = st.session_state.scores
        all_data[user_id] = user_record
        save_user_data(all_data)
        
        if st.session_state.idx < total_questions - 1:
            st.session_state.idx += 1; st.session_state.show = False
        else: st.session_state.is_finished = True
        st.rerun()

if not st.session_state.show:
    if st.button("🔍 查看解析", use_container_width=True):
        st.session_state.show = True; st.rerun()
else:
    st.success("### 💡 解析参考：")
    st.write(render_mixed_content(row['Back']))

# --- 7. 导航按钮 ---
st.divider()
n1, n2, n3 = st.columns([1, 1, 2])
with n1:
    if st.button("⬅️ 上一题"):
        if st.session_state.idx > 0: st.session_state.idx -= 1; st.rerun()
with n2:
    if st.button("跳过 ➡️"):
        if st.session_state.idx < total_questions - 1: st.session_state.idx += 1; st.rerun()
with n3:
    if st.button("🏁 结束自测", type="primary"):
        st.session_state.is_finished = True; st.rerun()
