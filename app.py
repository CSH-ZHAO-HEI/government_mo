import streamlit as st
import pandas as pd
import random

# --- 頁面配置 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

# --- 數據載入 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answer.csv")
        # 統一格式
        df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"讀取 CSV 失敗，請確認 answer.csv 是否與代碼在同一資料夾。錯誤：{e}")
        return None

df = load_data()

# --- 初始化 Session State ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.wrong_list = []
    st.session_state.submitted = False # 標記是否已提交答案
    st.session_state.last_result = None # 儲存當前題目的對錯反饋

# --- 側邊欄控制 ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題回顧"])

if mode == "隨機測驗":
    num = st.sidebar.slider("抽取題數", 5, 100, 20)
    if st.sidebar.button("✨ 生成新考卷"):
        if df is not None:
            st.session_state.test_set = df.sample(n=min(num, len(df))).to_dict('records')
            st.session_state.current_idx = 0
            st.session_state.submitted = False
            st.session_state.last_result = None
            st.rerun()

# --- 主界面邏輯 ---


if mode == "隨機測驗":
    if not st.session_state.test_set:
        st.info("💡 準備好了嗎？在左側設定題數並點擊『生成新考卷』開始練習。")
    else:
        idx = st.session_state.current_idx
        
        # 檢查是否已做完
        if idx < len(st.session_state.test_set):
            q = st.session_state.test_set[idx]
            
            # 進度條
            progress = (idx) / len(st.session_state.test_set)
            st.progress(progress)
            st.write(f"**第 {idx + 1} / {len(st.session_state.test_set)} 題** (ID: {q.get('id', 'N/A')})")
            
            # 顯示題目
            st.subheader(q['question'])
            
            # 動態解析選項 (過濾掉 NaN)
            opts_map = {} # {'A': '內容', 'B': '內容'}
            for i in range(26): # 支持最多 A-Z
                col = f'選項{chr(65+i)}'
                if col in q and pd.notna(q[col]):
                    opts_map[chr(65+i)] = q[col]
            
            labels = list(opts_map.keys())
            options_text = [f"{k}. {v}" for k, v in opts_map.items()]
            
            # 如果還沒提交，顯示單選框
            if not st.session_state.submitted:
                user_choice_text = st.radio("請選擇：", options_text, key=f"radio_{idx}")
                
                if st.button("確認提交"):
                    user_label = user_choice_text[0] # 取出開頭的 A, B, C...
                    correct_label = str(q['正確答案'])
                    
                    st.session_state.submitted = True
                    if user_label == correct_label:
                        st.session_state.last_result = ("success", "✅ 回答正確！")
                    else:
                        st.session_state.last_result = ("error", f"❌ 回答錯誤！正確答案是：{correct_label}")
                        # 記錄到錯題本
                        if q not in st.session_state.wrong_list:
                            st.session_state.wrong_list.append(q)
                    st.rerun()
            
            # 提交後顯示結果與下一題按鈕
            else:
                res_type, res_msg = st.session_state.last_result
                if res_type == "success": st.success(res_msg)
                else: st.error(res_msg)
                
                # 選項靜態展示
                for k, v in opts_map.items():
                    color = "green" if k == q['正確答案'] else "black"
                    st.markdown(f"<span style='color:{color}'>{k}. {v}</span>", unsafe_allow_html=True)

                if st.button("下一題 ➡️"):
                    st.session_state.current_idx += 1
                    st.session_state.submitted = False
                    st.session_state.last_result = None
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 太棒了！你已經完成了本次所有題目。")
            if st.button("回首頁重新開始"):
                st.session_state.test_set = []
                st.rerun()

elif mode == "錯題回顧":
    st.header("📓 我的錯題本")
    if not st.session_state.wrong_list:
        st.write("目前沒有錯題記錄。繼續加油，保持零錯題！")
    else:
        st.write(f"累計錯題：{len(st.session_state.wrong_list)} 題")
        for i, wq in enumerate(st.session_state.wrong_list):
            with st.expander(f"錯題 {i+1}：{wq['question'][:30]}..."):
                st.write(f"**完整題目：**\n{wq['question']}")
                
                st.write("**選項：**")
                # 循環顯示所有非空的選項
                for char_code in range(65, 91): # A-Z
                    col_name = f"選項{chr(char_code)}"
                    if col_name in wq and pd.notna(wq[col_name]):
                        # 標註正確答案
                        prefix = "👉" if chr(char_code) == str(wq['正確答案']) else "　"
                        st.write(f"{prefix} {chr(char_code)}. {wq[col_name]}")
                
                st.info(f"正確答案：{wq['正確答案']}")

