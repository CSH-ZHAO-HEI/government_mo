import streamlit as st
import pandas as pd
import random

# --- 頁面配置 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

# --- 數據初始化 ---
def initialize_data():
    """初始化題庫數據，確保行號唯一且欄位完整"""
    if 'df' not in st.session_state:
        try:
            # 讀取 CSV
            df = pd.read_csv("answer.csv")
            
            # 1. 格式化正確答案
            if '正確答案' in df.columns:
                df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
            else:
                st.error("CSV 檔案中缺少 '正確答案' 欄位")
            
            # 2. 初始化錯誤計數
            if 'wrong_count' not in df.columns:
                df['wrong_count'] = 0
            
            # 3. 強制生成唯一的「行號」 (original_index)
            df = df.reset_index(drop=True) 
            df['original_index'] = df.index + 1  # 從 1 開始
            
            st.session_state.df = df
        except Exception as e:
            st.error(f"讀取 CSV 失敗，請確保 answer.csv 存在。錯誤：{e}")
            st.session_state.df = pd.DataFrame(columns=['question', '正確答案', 'wrong_count', 'original_index'])

initialize_data()

# --- Session State 初始化 ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None

# --- 側邊欄導航 ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題本管理", "隨機錯題本測驗"])

if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_mode = mode

# --- 核心組件：測驗渲染函數 ---
def render_quiz(quiz_data, mode_title):
    if not quiz_data:
        st.info("💡 目前沒有選定的題目。")
        return

    idx = st.session_state.current_idx
    if idx < len(quiz_data):
        q = quiz_data[idx]
        st.write(f"**[{mode_title}] 第 {idx + 1} / {len(quiz_data)} 題** (行號: {q.get('original_index', 'N/A')})")
        st.subheader(q.get('question', '題目內容缺失'))
        
        opts = {}
        for i in range(26):
            col = f'選項{chr(65+i)}'
            if col in q and pd.notna(q[col]):
                opts[chr(65+i)] = q[col]
        
        options_text = [f"{k}. {v}" for k, v in opts.items()]
        
        if not st.session_state.submitted:
            user_choice = st.radio("請選擇答案：", options_text, key=f"radio_{idx}_{q.get('original_index')}")
            if st.button("提交答案", key="submit_btn"):
                st.session_state.submitted = True
                user_ans = user_choice[0] if user_choice else ""
                correct_ans = str(q.get('正確答案', ''))
                
                if user_ans == correct_ans:
                    st.session_state.last_result = ("success", "✅ 正確！")
                else:
                    st.session_state.last_result = ("error", f"❌ 錯誤！正確答案是：{correct_ans}")
                    st.session_state.df.loc[st.session_state.df['original_index'] == q['original_index'], 'wrong_count'] += 1
                st.rerun()
        else:
            res_type, res_msg = st.session_state.last_result
            if res_type == "success": st.success(res_msg)
            else: st.error(res_msg)
            
            if st.button("下一題 ➡️", key="next_btn"):
                st.session_state.current_idx += 1
                st.session_state.submitted = False
                st.rerun()
    else:
        st.balloons()
        st.success("🎉 測驗完成！")
        if st.button("重置並返回首頁"):
            st.session_state.test_set = []
            st.session_state.current_idx = 0
            st.rerun()

# --- 主界面邏輯 ---

if mode == "隨機測驗":
    st.header("📝 隨機全測驗")
    if not st.session_state.test_set:
        max_num = len(st.session_state.df)
        num = st.number_input("抽取題數", 1, max_num, min(100, max_num))
        if st.button("開始測驗", type="primary"):
            sampled_df = st.session_state.df.sample(n=num)
            st.session_state.test_set = sampled_df.to_dict('records')
            st.session_state.current_idx = 0
            st.session_state.submitted = False
            st.rerun()
    else:
        if st.sidebar.button("❌ 終止測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "隨機測驗")

elif mode == "錯題本管理":
    st.header("📓 題庫管理中心")
    # 新增了「❌ 錯題統計檢視」分頁
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 查看所有題目", "➕ 新增題目", "🗑️ 刪除題目", "❌ 錯題統計檢視"])

    with tab1:
        st.dataframe(
            st.session_state.df[['original_index', 'question', '正確答案', 'wrong_count']], 
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("添加新題目")
        with st.form("add_form"):
            new_q = st.text_area("題目內容")
            new_a = st.text_input("正確答案 (例如: A)")
            new_optA = st.text_input("選項 A")
            new_optB = st.text_input("選項 B")
            if st.form_submit_button("確認新增"):
                new_row_idx = int(st.session_state.df['original_index'].max() + 1) if not st.session_state.df.empty else 1
                new_row = {
                    'original_index': new_row_idx, 'question': new_q, 
                    '正確答案': new_a.upper().strip(), '選項A': new_optA, '選項B': new_optB, 
                    'wrong_count': 0
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"題目已新增，獲配行號：{new_row_idx}")
                st.rerun()

    with tab3:
        st.subheader("按行號刪除題目")
        del_target = st.number_input("請輸入要刪除的題目「行號」", step=1, min_value=1)
        if st.button("確認永久刪除", type="primary"):
            if del_target in st.session_state.df['original_index'].values:
                st.session_state.df = st.session_state.df[st.session_state.df['original_index'] != del_target]
                st.warning(f"行號 {del_target} 的題目已移除。")
                st.rerun()
            else:
                st.error("找不到該行號。")

    with tab4:
        st.subheader("❌ 錯題本統計")
        # 篩選出錯誤次數大於 0 的題目
        wrong_only_df = st.session_state.df[st.session_state.df['wrong_count'] > 0].copy()
        
        if wrong_only_df.empty:
            st.success("目前沒有錯題記錄，太棒了！")
        else:
            # 按錯誤次數降序排列，讓最常錯的排在前面
            wrong_only_df = wrong_only_df.sort_values(by='wrong_count', ascending=False)
            
            st.write(f"目前共有 **{len(wrong_only_df)}** 道題目曾出錯。")
            
            # 顯示表格
            st.dataframe(
                wrong_only_df[['original_index', 'wrong_count', 'question', '正確答案']], 
                use_container_width=True,
                hide_index=True
            )
            
            # 提供一個清空單個錯題記錄的功能
            col1, col2 = st.columns([2, 1])
            with col1:
                reset_id = st.number_input("輸入要歸零錯誤數的行號", step=1, min_value=1, key="reset_idx")
            with col2:
                if st.button("重置該題錯誤數"):
                    st.session_state.df.loc[st.session_state.df['original_index'] == reset_id, 'wrong_count'] = 0
                    st.success(f"行號 {reset_id} 已從錯題本中移除")
                    st.rerun()

elif mode == "隨機錯題本測驗":
    st.header("🔥 錯題強化訓練")
    if not st.session_state.test_set:
        wrong_df = st.session_state.df[st.session_state.df['wrong_count'] > 0]
        if wrong_df.empty:
            st.info("✨ 太棒了！目前沒有任何錯題記錄。")
        else:
            st.write(f"目前錯題本中共計 **{len(wrong_df)}** 題。")
            if st.button("開始隨機抽題測驗", type="primary"):
                st.session_state.test_set = wrong_df.sample(frac=1).to_dict('records')
                st.session_state.current_idx = 0
                st.session_state.submitted = False
                st.rerun()
    else:
        if st.sidebar.button("❌ 結束測驗"):
            st.session_state.test_set = []
            st.rerun()
        render_quiz(st.session_state.test_set, "錯題測驗")
