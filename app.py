import streamlit as st
import pandas as pd
import random

# --- 頁面配置 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

# --- 數據初始化 ---
def initialize_data():
    if 'df' not in st.session_state:
        try:
            # 讀取 CSV
            df = pd.read_csv("answer.csv")
            # 統一格式
            df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
            
            # 初始化必要欄位
            if 'wrong_count' not in df.columns:
                df['wrong_count'] = 0
            
            # 我們不依賴 CSV 裡的 ID，直接使用 DataFrame 的 Index 作為「行號」
            # 為了方便後續抽題後還能找回原行號，我們複製一份索引到新欄位
            df['original_index'] = df.index + 1 # +1 讓用戶看起來是從第 1 行開始
            
            st.session_state.df = df
        except Exception as e:
            st.error(f"讀取 CSV 失敗：{e}")
            st.session_state.df = pd.DataFrame(columns=['question', '正確答案', 'wrong_count', 'original_index'])

initialize_data()

# --- Session State 初始化 ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None

# --- 側邊欄控制 ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題本管理", "隨機錯題本測驗"])

# 當切換模式時，清空當前測驗狀態
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.last_mode = mode

# --- 輔助函數：測驗組件 ---
def render_quiz(quiz_data, mode_title):
    if not quiz_data:
        st.info(f"💡 目前沒有題目。")
        return

    idx = st.session_state.current_idx
    if idx < len(quiz_data):
        q = quiz_data[idx]
        
        # 顯示行號而非重複的 ID
        st.write(f"**[{mode_title}] 第 {idx + 1} / {len(quiz_data)} 題** (行號: {q['original_index']})")
        st.subheader(q['question'])
        
        # 動態抓取選項
        opts = {}
        for i in range(26):
            col = f'選項{chr(65+i)}'
            if col in q and pd.notna(q[col]):
                opts[chr(65+i)] = q[col]
        
        options_text = [f"{k}. {v}" for k, v in opts.items()]
        
        if not st.session_state.submitted:
            user_choice = st.radio("請選擇答案：", options_text, key=f"q_{idx}_{q['original_index']}")
            if st.button("提交答案"):
                st.session_state.submitted = True
                user_ans = user_choice[0]
                correct_ans = str(q['正確答案'])
                
                if user_ans == correct_ans:
                    st.session_state.last_result = ("success", "✅ 正確！")
                else:
                    st.session_state.last_result = ("error", f"❌ 錯誤！正確答案是：{correct_ans}")
                    # 根據原始索引更新錯誤次數 (精確匹配某一行)
                    st.session_state.df.loc[st.session_state.df['original_index'] == q['original_index'], 'wrong_count'] += 1
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

if mode == "隨機測驗":
    st.header("📝 隨機全測驗")
    
    # --- 關鍵：如果沒在測驗中，顯示設置區域 ---
    if not st.session_state.test_set:
        num = st.number_input("抽取題數", 1, len(st.session_state.df), min(5, len(st.session_state.df)))
        if st.button("開始測驗"):
            # 轉為字典時包含 original_index
            st.session_state.test_set = st.session_state.df.sample(n=num).to_dict('records')
            st.session_state.current_idx = 0
            st.session_state.submitted = False
            st.rerun()
    else:
        # --- 如果已在測驗中，只顯示測驗內容，並提供一個放棄按鈕 ---
        if st.button("放棄本次測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "隨機測驗")

elif mode == "錯題本管理":
    st.header("📓 題庫管理")
    tab1, tab2, tab3 = st.tabs(["查看所有題目", "新增題目", "刪除題目"])

    with tab1:
        # 顯示 original_index 作為行號
        st.dataframe(st.session_state.df[['original_index', 'question', '正確答案', 'wrong_count']], use_container_width=True)

    with tab2:
        st.subheader("添加新題目")
        with st.form("add_form"):
            new_q = st.text_area("題目內容")
            new_a = st.text_input("正確答案 (如: A)")
            new_optA = st.text_input("選項 A")
            new_optB = st.text_input("選項 B")
            if st.form_submit_button("確認新增"):
                new_idx = int(st.session_state.df['original_index'].max() + 1) if not st.session_state.df.empty else 1
                new_row = {
                    'original_index': new_idx, 'question': new_q, '正確答案': new_a.upper(), 
                    '選項A': new_optA, '選項B': new_optB, 'wrong_count': 0
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"新題目已新增，行號為：{new_idx}")
                st.rerun()

    with tab3:
        st.subheader("刪除題目")
        # 這裡改為輸入行號（original_index）來刪除
        del_target = st.number_input("輸入要刪除的題目「行號」", step=1, min_value=1)
        if st.button("確認刪除題目", type="primary"):
            if del_target in st.session_state.df['original_index'].values:
                st.session_state.df = st.session_state.df[st.session_state.df['original_index'] != del_target]
                st.warning(f"行號 {del_target} 的題目已刪除")
                st.rerun()
            else:
                st.error("找不到該行號")

elif mode == "隨機錯題本測驗":
    st.header("🔥 錯題強化訓練")
    wrong_df = st.session_state.df[st.session_state.df['wrong_count'] > 0]
    
    if not st.session_state.test_set:
        if wrong_df.empty:
            st.info("太棒了！目前沒有任何錯題記錄。")
        else:
            st.write(f"目前錯題本中共計 {len(wrong_df)} 題。")
            if st.button("開始隨機抽題測驗"):
                st.session_state.test_set = wrong_df.sample(frac=1).to_dict('records')
                st.session_state.current_idx = 0
                st.session_state.submitted = False
                st.rerun()
    else:
        if st.button("結束測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "錯題測驗")
