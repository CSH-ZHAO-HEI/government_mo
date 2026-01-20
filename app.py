import streamlit as st
import pandas as pd
import random

# --- 頁面配置 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

# --- 數據初始化 ---
def initialize_data():
    if 'df' not in st.session_state:
        try:
            # 讀取初始 CSV
            df = pd.read_csv("answer.csv")
            # 統一格式並增加「錯誤次數」欄位
            df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
            if 'wrong_count' not in df.columns:
                df['wrong_count'] = 0
            if 'id' not in df.columns:
                df['id'] = range(1, len(df) + 1)
            st.session_state.df = df
        except Exception as e:
            st.error(f"讀取 CSV 失敗，請確保 answer.csv 存在。錯誤：{e}")
            # 若無檔案則建立空表
            st.session_state.df = pd.DataFrame(columns=['id', 'question', '正確答案', 'wrong_count'])

initialize_data()

# --- Session State 用於測驗流程 ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None

# --- 側邊欄控制 (三個模式) ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題本管理", "隨機錯題本測驗"])

# --- 輔助函數：測驗組件 ---
def render_quiz(quiz_data, mode_title):
    if not quiz_data:
        st.info(f"💡 目前沒有題目可以進行 {mode_title}。")
        return

    idx = st.session_state.current_idx
    if idx < len(quiz_data):
        q = quiz_data[idx]
        st.write(f"**[{mode_title}] 第 {idx + 1} / {len(quiz_data)} 題** (ID: {q['id']})")
        st.subheader(q['question'])
        
        # 動態抓取選項
        opts = {}
        for i in range(26):
            col = f'選項{chr(65+i)}'
            if col in q and pd.notna(q[col]):
                opts[chr(65+i)] = q[col]
        
        options_text = [f"{k}. {v}" for k, v in opts.items()]
        
        if not st.session_state.submitted:
            user_choice = st.radio("請選擇答案：", options_text, key=f"q_{idx}")
            if st.button("提交答案"):
                st.session_state.submitted = True
                user_ans = user_choice[0]
                correct_ans = str(q['正確答案'])
                
                if user_ans == correct_ans:
                    st.session_state.last_result = ("success", "✅ 正確！")
                else:
                    st.session_state.last_result = ("error", f"❌ 錯誤！正確答案是：{correct_ans}")
                    # 更新原始 DataFrame 中的錯誤次數
                    st.session_state.df.loc[st.session_state.df['id'] == q['id'], 'wrong_count'] += 1
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
        if st.button("重置並返回"):
            st.session_state.test_set = []
            st.session_state.current_idx = 0
            st.rerun()

# --- 主界面邏輯 ---

# 模式 1: 隨機測驗 (全部題目)
if mode == "隨機測驗":
    st.header("📝 隨機全測驗")
    num = st.number_input("抽取題數", 1, len(st.session_state.df), 5)
    if st.button("開始測驗"):
        st.session_state.test_set = st.session_state.df.sample(n=num).to_dict('records')
        st.session_state.current_idx = 0
        st.session_state.submitted = False
        st.rerun()
    
    if st.session_state.test_set and mode == "隨機測驗":
        render_quiz(st.session_state.test_set, "隨機測驗")

# 模式 2: 錯題本 (包含查看、新增、刪除)
elif mode == "錯題本管理":
    st.header("📓 錯題本中心")
    tab1, tab2, tab3 = st.tabs(["查看所有題目", "新增題目", "刪除題目"])

    with tab1:
        st.write("目前的題庫狀態：")
        # 顯示時只選取部分欄位以免過長
        display_df = st.session_state.df[['id', 'question', '正確答案', 'wrong_count']]
        st.dataframe(display_df, use_container_width=True)

    with tab2:
        st.subheader("添加新題目")
        with st.form("add_form"):
            new_q = st.text_area("題目內容")
            new_a = st.text_input("正確答案 (如: A)")
            new_optA = st.text_input("選項 A")
            new_optB = st.text_input("選項 B")
            submitted = st.form_submit_button("確認新增")
            if submitted:
                new_id = int(st.session_state.df['id'].max() + 1) if not st.session_state.df.empty else 1
                new_row = {
                    'id': new_id, 'question': new_q, '正確答案': new_a.upper(), 
                    '選項A': new_optA, '選項B': new_optB, 'wrong_count': 0
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"題目 ID {new_id} 已新增")
                st.rerun()

    with tab3:
        st.subheader("刪除題目")
        del_id = st.number_input("輸入要刪除的題目 ID", step=1)
        if st.button("確認刪除", type="primary"):
            st.session_state.df = st.session_state.df[st.session_state.df['id'] != del_id]
            st.warning(f"ID {del_id} 已被刪除")
            st.rerun()

# 模式 3: 隨機錯題本測驗
elif mode == "隨機錯題本測驗":
    st.header("🔥 錯題強化訓練")
    # 篩選錯誤次數 > 0 的題目
    wrong_df = st.session_state.df[st.session_state.df['wrong_count'] > 0]
    
    if wrong_df.empty:
        st.info("太棒了！目前沒有任何錯題記錄。")
    else:
        st.write(f"目前錯題本中共計 {len(wrong_df)} 題。")
        if st.button("開始隨機抽題測驗"):
            # 全部錯題隨機排序
            st.session_state.test_set = wrong_df.sample(frac=1).to_dict('records')
            st.session_state.current_idx = 0
            st.session_state.submitted = False
            st.rerun()
        
        if st.session_state.test_set and mode == "隨機錯題本測驗":
            render_quiz(st.session_state.test_set, "錯題測驗")
