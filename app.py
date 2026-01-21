import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. 頁面配置 ---
st.set_page_config(page_title="澳門法例刷題助手", layout="centered")

st.markdown("""
    <style>
    .stRadio [role="radiogroup"] { margin-top: 10px; }
    .stButton button { width: 100%; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據核心邏輯 (Google Sheets 持久化) ---

# 建立 Google Sheets 連接
# ttl="0s" 確保每次讀取都是從雲端獲取最新數據，而不是緩存
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_gsheets():
    """將內存中的數據同步回 Google Sheets"""
    try:
        # 複製一份數據用於保存
        save_df = st.session_state.df.copy()
        # 移除僅供本地 UI 使用的「行號」欄位
        if 'original_index' in save_df.columns:
            save_df = save_df.drop(columns=['original_index'])
        
        # 寫回雲端表格
        conn.update(data=save_df)
        return True
    except Exception as e:
        st.error(f"雲端保存失敗，請檢查權限或 Secrets 設置。錯誤：{e}")
        return False

def initialize_data():
    """從雲端初始化數據"""
    if 'df' not in st.session_state:
        try:
            # 從 Google Sheets 讀取
            df = conn.read(ttl="0s")
            
            # 數據清洗
            if '正確答案' in df.columns:
                df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
            
            # 確保有錯誤計數欄位
            if 'wrong_count' not in df.columns:
                df['wrong_count'] = 0
            else:
                df['wrong_count'] = df['wrong_count'].fillna(0).astype(int)
            
            # 生成本地唯一行號標識
            df = df.reset_index(drop=True)
            df['original_index'] = df.index + 1
            
            st.session_state.df = df
        except Exception as e:
            st.error(f"無法讀取雲端數據：{e}")
            st.session_state.df = pd.DataFrame(columns=['question', '正確答案', 'wrong_count', 'original_index'])

initialize_data()

# --- 3. 狀態初始化 ---
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None
    st.session_state.score = {"correct": 0, "wrong": 0}

# --- 4. 側邊欄與導航 ---
st.sidebar.title("🎮 功能選單")
mode = st.sidebar.radio("請選擇模式", ["隨機測驗", "錯題本管理", "隨機錯題本測驗"])

def reset_test_state():
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.submitted = False
    st.session_state.last_result = None
    st.session_state.score = {"correct": 0, "wrong": 0}

if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    reset_test_state()
    st.session_state.last_mode = mode

# --- 5. 測驗組件渲染 ---

def render_quiz(quiz_data, mode_title, is_wrong_mode=False):
    if not quiz_data:
        st.info("💡 目前沒有題目。")
        return

    idx = st.session_state.current_idx
    if idx < len(quiz_data):
        q = quiz_data[idx]
        row_num = q.get('original_index', 'N/A')
        
        st.write(f"**[{mode_title}] 第 {idx + 1} / {len(quiz_data)} 題** (行號: {row_num})")
        st.subheader(q.get('question', '題目讀取中...'))
        
        # 提取選項
        opts = {chr(65+i): q[f'選項{chr(65+i)}'] for i in range(26) 
                if f'選項{chr(65+i)}' in q and pd.notna(q[f'選項{chr(65+i)}'])}
        options_text = [f"{k}. {v}" for k, v in opts.items()]
        
        user_choice = st.radio(
            "請選擇答案：", 
            options_text, 
            key=f"r_{idx}_{row_num}",
            disabled=st.session_state.submitted
        )
        
        st.write("---")
        
        if not st.session_state.submitted:
            if st.button("確認提交", type="primary"):
                st.session_state.submitted = True
                user_ans = user_choice[0] if user_choice else ""
                correct_ans = str(q.get('正確答案', ''))
                
                if user_ans == correct_ans:
                    st.session_state.score["correct"] += 1
                    st.session_state.last_result = ("success", f"✅ 正確！答案是 {correct_ans}")
                    # 如果在錯題模式答對，則歸零並同步雲端
                    if is_wrong_mode:
                        st.session_state.df.loc[st.session_state.df['original_index'] == row_num, 'wrong_count'] = 0
                        save_to_gsheets()
                else:
                    st.session_state.score["wrong"] += 1
                    st.session_state.last_result = ("error", f"❌ 錯誤！正確答案是：{correct_ans}")
                    # 答錯增加計數並同步雲端
                    st.session_state.df.loc[st.session_state.df['original_index'] == row_num, 'wrong_count'] += 1
                    save_to_gsheets()
                st.rerun()
        else:
            res_type, res_msg = st.session_state.last_result
            if res_type == "success": 
                st.success(res_msg)
                if is_wrong_mode: st.caption("✨ 此題已掌握，已從錯題本移除。")
            else: 
                st.error(res_msg)
            
            if st.button("下一題 ➡️"):
                st.session_state.current_idx += 1
                st.session_state.submitted = False
                st.session_state.last_result = None
                st.rerun()
    else:
        st.balloons()
        st.header("📊 測驗統計")
        c, w = st.session_state.score["correct"], st.session_state.score["wrong"]
        total = c + w
        acc = (c / total * 100) if total > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("答對", f"{c}")
        col2.metric("答錯", f"{w}")
        col3.metric("正確率", f"{acc:.1f}%")
        
        if st.button("完成並返回"):
            reset_test_state()
            st.rerun()

# --- 6. 主頁面邏輯 ---

if mode == "隨機測驗":
    st.header("📝 隨機全測驗")
    if not st.session_state.test_set:
        max_n = len(st.session_state.df)
        num = st.number_input("抽取題數", 1, max_n, min(10, max_n))
        if st.button("開始測驗", type="primary"):
            reset_test_state()
            st.session_state.test_set = st.session_state.df.sample(n=num).to_dict('records')
            st.rerun()
    else:
        if st.sidebar.button("❌ 放棄測驗"):
            reset_test_state()
            st.rerun()
        render_quiz(st.session_state.test_set, "隨機測驗", is_wrong_mode=False)

elif mode == "錯題本管理":
    st.header("📓 雲端題庫管理")
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 查看全部", "➕ 新增", "🗑️ 刪除", "❌ 錯題統計"])

    with tab1:
        st.dataframe(st.session_state.df[['original_index', 'question', '正確答案', 'wrong_count']], 
                     use_container_width=True, hide_index=True)
        if st.button("🔄 同步雲端最新數據"):
            del st.session_state.df
            st.rerun()

    with tab2:
        with st.form("add_q"):
            nq, na = st.text_area("題目"), st.text_input("答案")
            oA, oB = st.text_input("選項 A"), st.text_input("選項 B")
            if st.form_submit_button("上傳到雲端"):
                new_idx = (st.session_state.df['original_index'].max() + 1) if not st.session_state.df.empty else 1
                new_row = {'original_index': new_idx, 'question': nq, '正確答案': na.upper(), 
                           '選項A': oA, '選項B': oB, 'wrong_count': 0}
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                if save_to_gsheets():
                    st.success("已永久保存至雲端！")
                    st.rerun()

    with tab3:
        dt = st.number_input("刪除行號", step=1, min_value=1)
        if st.button("永久從雲端刪除", type="primary"):
            st.session_state.df = st.session_state.df[st.session_state.df['original_index'] != dt]
            if save_to_gsheets():
                st.warning(f"行號 {dt} 已刪除")
                st.rerun()

    with tab4:
        wrong_df = st.session_state.df[st.session_state.df['wrong_count'] > 0].sort_values('wrong_count', ascending=False)
        if wrong_df.empty:
            st.success("目前無錯題！")
        else:
            st.write(f"共有 {len(wrong_df)} 題存在錯誤記錄")
            st.dataframe(wrong_df[['original_index', 'wrong_count', 'question', '正確答案']], 
                         use_container_width=True, hide_index=True)
            if st.button("🔥 清空所有錯誤次數"):
                st.session_state.df['wrong_count'] = 0
                save_to_gsheets()
                st.rerun()

elif mode == "隨機錯題本測驗":
    st.header("🔥 錯題強化訓練")
    if not st.session_state.test_set:
        pool = st.session_state.df[st.session_state.df['wrong_count'] > 0]
        if pool.empty:
            st.info("✨ 錯題本空空如也。")
        else:
            st.write(f"錯題本共計 **{len(pool)}** 題。在此答對會自動移除記錄。")
            if st.button("開始強化訓練", type="primary"):
                reset_test_state()
                st.session_state.test_set = pool.sample(frac=1).to_dict('records')
                st.rerun()
    else:
        render_quiz(st.session_state.test_set, "錯題強化", is_wrong_mode=True)
