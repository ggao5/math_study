import streamlit as st
import pandas as pd
import os
import json

# --- 1. 页面与环境设置 ---
st.set_page_config(page_title="竞赛数学闪卡系统", page_icon="🧮", layout="wide")

# MathJax 渲染脚本 (保持渲染效果最优秀的配置)
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
    [data-testid="stMain"] .stButton button { white-space: pre-wrap !important; height: auto !important; min-height: 60px; }
    div[data-testid="stHorizontalBlock"] > div { display: flex; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据持久化逻辑 ---
USER_DATA_FILE = "user_progress.json"
ADMIN_USER = "Guanfeng Gao"
ADMIN_PASS = "pB10214025!"

def load_all_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def render_mixed_content(text):
    if not isinstance(text, str): return str(text)
    return text.replace('\\\\', '\\')

# --- 3. 登录/注册/管理界面 ---
if 'user' not in st.session_state:
    st.title("🔐 高老师数学竞赛练习系统")
    tab1, tab2, tab3 = st.tabs(["学生登录", "新同学注册", "教师端后台"])
    all_users = load_all_user_data()
    
    with tab1:
        login_name = st.text_input("请输入姓名/学号", key="login_input")
        login_pass = st.text_input("请输入密码", type="password", key="login_pass")
        if st.button("进入学习"):
            if login_name in all_users and all_users[login_name].get("password") == login_pass:
                st.session_state.user = login_name
                st.rerun()
            else: st.error("姓名或密码错误。")
            
    with tab2:
        new_name = st.text_input("设置你的姓名/学号", key="reg_input")
        new_pass = st.text_input("设置你的密码", type="password", key="reg_pass")
        if st.button("立即注册"):
            if new_name and new_name not in all_users and new_name != ADMIN_USER:
                all_users[new_name] = {"password": new_pass, "history": {}}
                save_user_data(all_users)
                st.success("注册成功！请切换到登录页。")
            else: st.warning("用户已存在或名字不合法。")

    with tab3:
        admin_name = st.text_input("管理员账号", key="admin_input")
        admin_pass = st.text_input("管理员密码", type="password", key="admin_pass")
        if st.button("登入后台"):
            if admin_name == ADMIN_USER and admin_pass == ADMIN_PASS:
                st.session_state.user = ADMIN_USER
                st.session_state.is_admin = True
                st.rerun()
            else: st.error("管理员权限验证失败。")
    st.stop()

# --- 4. 教师端后台显示 ---
if st.session_state.get("is_admin"):
    st.title("👨‍🏫 教师后台：学生进度管理")
    all_data = load_all_user_data()
    
    if not all_data:
        st.write("暂无学生注册。")
    else:
        for student, info in all_data.items():
            with st.expander(f"👤 学生：{student}"):
                history = info.get("history", {})
                if not history:
                    st.write("该学生尚未开始任何练习。")
                else:
                    for chapter, scores in history.items():
                        num_q = len(scores)
                        avg_s = sum(scores.values())/num_q if num_q > 0 else 0
                        st.write(f"📖 **{chapter}**: 已做 {num_q} 题，平均分 {avg_s:.1f}")
    
    if st.sidebar.button("🚪 退出管理端"):
        del st.session_state.user
        st.session_state.is_admin = False
        st.rerun()
    st.stop()

# --- 5. 章节选择与进度恢复选择 ---
user_id = st.session_state.user
all_data = load_all_user_data()
user_record = all_data[user_id]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
selected_file = st.sidebar.selectbox("📚 选择章节", sorted(csv_files))

# 【修改1】自动恢复进度选择
if 'current_chapter' not in st.session_state or st.session_state.current_chapter != selected_file:
    hist = user_record["history"].get(selected_file, {})
    if hist:
        st.warning(f"检测到您之前做过《{selected_file}》。")
        c1, c2 = st.columns(2)
        if c1.button("继续上次进度"):
            st.session_state.scores = {int(k): v for k, v in hist.items()}
            st.session_state.current_chapter = selected_file
            st.rerun()
        if c2.button("重头开始(清除记录)"):
            st.session_state.scores = {}
            st.session_state.current_chapter = selected_file
            st.rerun()
        st.stop()
    else:
        st.session_state.scores = {}
        st.session_state.current_chapter = selected_file

# --- 6. 正常练习逻辑 ---
df = pd.read_csv(os.path.join(DATA_DIR, selected_file), encoding='utf-8', keep_default_na=False, escapechar=None)
total_questions = len(df)

if 'idx' not in st.session_state or st.session_state.get('last_file') != selected_file:
    st.session_state.idx = 0
    st.session_state.show = False
    st.session_state.last_file = selected_file
    st.session_state.is_finished = False
    st.session_state.confirm_end = False

# --- 7. 报告页面 (含分级评价) ---
if st.session_state.is_finished:
    st.title(f"📊 {user_id} 的学习报告")
    num_scored = len(st.session_state.scores)
    st.subheader(f"完成进度：{num_scored} / {total_questions}")
    if num_scored > 0:
        avg = sum(st.session_state.scores.values()) / num_scored
        st.metric("本章平均分", f"{avg:.1f}")
        if avg >= 4.0: st.success(f"🌟 非常出色！你的平均分是 {avg:.1f}。高老师为你骄傲！")
        elif avg >= 3.0: st.info(f"👍 表现不错。平均分 {avg:.1f}。建议针对模糊点再巩固。")
        else: st.warning(f"📖 平均分 {avg:.1f} 偏低。建议重新复习基础。")
        user_record["history"][selected_file] = st.session_state.scores
        all_data[user_id] = user_record
        save_user_data(all_data)
    if st.button("🔄 重新练习本章"):
        st.session_state.scores = {}; st.session_state.is_finished = False; st.rerun()
    if st.button("🚪 退出登录"):
        del st.session_state.user; st.rerun()
    st.stop()

# --- 8. 侧边栏与主界面 ---
st.sidebar.write(f"👤 学生：**{user_id}**")
st.sidebar.subheader(f"进度: {len(st.session_state.scores)}/{total_questions}")
cols_per_row = 4
for r in range((total_questions // cols_per_row) + (1 if total_questions % cols_per_row != 0 else 0)):
    cols = st.sidebar.columns(cols_per_row)
    for c in range(cols_per_row):
        q_idx = r * cols_per_row + c
        if q_idx < total_questions:
            t = "primary" if q_idx in st.session_state.scores else "secondary"
            if cols[c].button(f"{q_idx+1}", key=f"nav_{q_idx}", type=t, use_container_width=True):
                st.session_state.idx = q_idx; st.session_state.show = False; st.rerun()

st.title("🧮 高老师的国际数学竞赛闪卡练习")
row = df.iloc[st.session_state.idx]
st.info(f"📍 当前题目：第 {st.session_state.idx + 1} 题")
st.write(render_mixed_content(row['Front']))
st.divider()

score_cols = st.columns(5)
labels = ["不懂", "模糊", "懂了", "熟练", "秒杀"]
for i in range(5):
    if score_cols[i].button(f"{i+1}\n{labels[i]}", key=f"s_{i}", use_container_width=True):
        st.session_state.scores[st.session_state.idx] = i + 1
        user_record["history"][selected_file] = st.session_state.scores
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

# --- 9. 底部导航与确认逻辑 ---
st.divider()
n1, n2, n3 = st.columns(3)
with n1:
    if st.button("⬅️ 上一题", use_container_width=True):
        if st.session_state.idx > 0: st.session_state.idx -= 1; st.session_state.show = False; st.rerun()
with n2:
    if st.button("跳过 ➡️", use_container_width=True):
        if st.session_state.idx < total_questions - 1: st.session_state.idx += 1; st.session_state.show = False; st.rerun()
with n3:
    if st.button("🏁 结束自测", use_container_width=True, type="primary"):
        st.session_state.confirm_end = True; st.rerun()

if st.session_state.confirm_end:
    st.markdown("---")
    unanswered = [i + 1 for i in range(total_questions) if i not in st.session_state.scores]
    if unanswered:
        st.warning(f"⚠️ **还有 {len(unanswered)} 道题目没有评分！**")
        st.write(f"未完成题号：{', '.join(map(str, unanswered))}")
    else: st.info("🎉 所有题目已评分完成。")
    ca, cb = st.columns(2)
    if ca.button("确认结束", use_container_width=True):
        st.session_state.is_finished = True; st.session_state.confirm_end = False; st.rerun()
    if cb.button("返回继续", use_container_width=True):
        st.session_state.confirm_end = False; st.rerun()
