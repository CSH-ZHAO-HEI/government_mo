import streamlit as st
import pandas as pd
import os

# --- 1. 頁面配置與樣式 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

# 修正處：將 unsafe_index 改為 unsafe_allow_html
st.markdown("""
    <style>
    .stRadio [role="radiogroup"] { margin-top: 10px; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據核心邏輯 ---

def save_to_csv():
    """將當前內存中的 df 永久保存到檔案"""
    try:
        save_df = st.session_state.df.copy()
        if 'original_index' in save_df.columns:
            save_df = save_df.drop(columns=['original_index'])
        save_df.to_csv("answer.csv", index=False)
        return True
    except Exception as e:
        st.error(f"數據保存失敗：{e}")
        return False

def initialize_data():
    """初始化數據表，確保具備行號和錯誤統計功能"""
    if 'df' not in st.session_state:
        if os.path.exists("answer.csv"):
            try:
                df = pd.read_csv("answer.csv")
                if '正確答案' in df.columns:
                    df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
                if 'wrong_count' not in df.columns:
                    df['wrong_count'] = 0
                df = df.reset_index(drop=True)
                df['original_index'] = df.index + 1
                st.session_state.df = df
            except Exception as e:
                st.error(f"解析檔案出錯：{e}")
        else:
            st.warning("找不到 answer.csv，已建立空庫。")
            st.session_state.df = pd.DataFrame(columns=['question', '正確答案', 'wrong_count', 'original_index'])

initialize_data()

# --- 3. 狀態初始化 ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None

# --- 4. 側邊欄與導航 ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題本管理", "隨機錯題本測驗"])

if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_mode = mode

# --- 5. 測驗組件渲染 ---

def render_quiz(quiz_data, mode_title):
    if not quiz_data:
        st.info("💡 目前沒有題目。")
        return

    idx = st.session_state.current_idx
    if idx < len(quiz_data):
        q = quiz_data[idx]
        row_num = q.get('original_index', 'N/A')
        
        st.write(f"**[{mode_title}] 第 {idx + 1} / {len(quiz_data)} 題** (行號: {row_num})")
        st.subheader(q.get('question', '未命名題目'))
        
        opts = {chr(65+i): q[f'選項{chr(65+i)}'] for i in range(26) 
                if f'選項{chr(65+i)}' in q and pd.notna(q[f'選項{chr(65+i)}'])}
        options_text = [f"{k}. {v}" for k, v in opts.items()]
        
        if not st.session_state.submitted:
            user_choice = st.radio("請選擇答案：", options_text, key=f"r_{idx}_{row_num}")
            if st.button("提交答案", type="primary"):
                st.session_state.submitted = True
                user_ans = user_choice[0] if user_choice else ""
                correct_ans = str(q.get('正確答案', ''))
                
                if user_ans == correct_ans:
                    st.session_state.last_result = ("success", "✅ 正確！")
                else:
                    st.session_state.last_result = ("error", f"❌ 錯誤！正確答案是：{correct_ans}")
                    st.session_state.df.loc[st.session_state.df['original_index'] == row_num, 'wrong_count'] += 1
                    save_to_csv()
                st.rerun()
        else:
            res_type, res_msg = st.session_state.last_result
            if res_type == "success": st.success(res_msg)
            else: st.error(res_msg)
            
            if st.button("下一題 ➡️"):
                st.session_state.current_idx += 1
                st.session_state.submitted = False
                st.rerun()
    else:
        st.balloons()
        st.success("🎉 測驗完成！")
        if st.button("返回"):
            st.session_state.test_set = []
            st.session_state.current_idx = 0
            st.rerun()

# --- 6. 主頁面邏輯 ---

if mode == "隨機測驗":
    st.header("📝 隨機全測驗")
    if not st.session_state.test_set:
        max_num = len(st.session_state.df)
        num = st.number_input("抽取題數", 1, max_num, min(10, max_num))
        if st.button("開始測驗", type="primary"):
            st.session_state.test_set = st.session_state.df.sample(n=num).to_dict('records')
            st.session_state.current_idx = 0
            st.rerun()
    else:
        if st.sidebar.button("❌ 中止測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "隨機測驗")

elif mode == "錯題本管理":
    st.header("📓 題庫管理中心")
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 查看全部", "➕ 新增題目", "🗑️ 刪除題目", "❌ 錯題歸零管理"])

    with tab1:
        st.dataframe(st.session_state.df[['original_index', 'question', '正確答案', 'wrong_count']], 
                     use_container_width=True, hide_index=True)
        if st.button("💾 手動存檔至 CSV"):
            if save_to_csv(): st.toast("存檔成功！")

    with tab2:
        with st.form("add_form"):
            new_q = st.text_area("題目內容")
            new_a = st.text_input("正確答案 (A/B/C...)")
            col1, col2 = st.columns(2)
            optA = col1.text_input("選項 A")
            optB = col2.text_input("選項 B")
            if st.form_submit_button("確認新增"):
                new_idx = (st.session_state.df['original_index'].max() + 1) if not st.session_state.df.empty else 1
                new_row = {'original_index': new_idx, 'question': new_q, '正確答案': new_a.upper(), 
                           '選項A': optA, '選項B': optB, 'wrong_count': 0}
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                save_to_csv()
                st.success(f"已新增行號: {new_idx}")
                st.rerun()

    with tab3:
        del_target = st.number_input("欲刪除的題目行號", step=1, min_value=1)
        if st.button("永久刪除該題", type="primary"):
            st.session_state.df = st.session_state.df[st.session_state.df['original_index'] != del_target]
            save_to_csv()
            st.warning(f"行號 {del_target} 已刪除")
            st.rerun()

    with tab4:
        st.subheader("❌ 錯題統計與歸零")
        wrong_df = st.session_state.df[st.session_state.df['wrong_count'] > 0].sort_values('wrong_count', ascending=False)
        
        if wrong_df.empty:
            st.success("目前沒有任何錯題記錄！")
        else:
            st.write(f"目前有 {len(wrong_df)} 題存在錯誤記錄：")
            st.dataframe(wrong_df[['original_index', 'wrong_count', 'question', '正確答案']], 
                         use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                target_reset = st.number_input("歸零特定行號", step=1, min_value=1, key="reset_one")
                if st.button("歸零該題"):
                    st.session_state.df.loc[st.session_state.df['original_index'] == target_reset, 'wrong_count'] = 0
                    save_to_csv()
                    st.rerun()
            with c2:
                st.write("---")
                if st.button("🔥 清空所有錯題記錄"):
                    st.session_state.df['wrong_count'] = 0
                    save_to_csv()
                    st.rerun()

elif mode == "隨機錯題本測驗":
    st.header("🔥 錯題強化訓練")
    if not st.session_state.test_set:
        wrong_pool = st.session_state.df[st.session_state.df['wrong_count'] > 0]
        if wrong_pool.empty:
            st.info("✨ 暫無錯題，請去隨機測驗積累題目。")
        else:
            st.write(f"錯題本共計 **{len(wrong_pool)}** 題。")
            if st.button("開始抽題測驗", type="primary"):
                st.session_state.test_set = wrong_pool.sample(frac=1).to_dict('records')
                st.session_state.current_idx = 0
                st.rerun()
    else:
        if st.sidebar.button("❌ 結束測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "錯題強化")
