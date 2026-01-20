import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="澳門法例刷題助手", layout="centered")


# 載入數據
@st.cache_data
def load_data():
    df = pd.read_csv("answer.csv")
    # 確保答案是字串且大寫
    df['正確答案'] = df['正確答案'].astype(str).str.strip().str.upper()
    return df


df = load_data()

# 初始化狀態
if 'test_set' not in st.session_state:
    st.session_state.test_set = []
    st.session_state.current_idx = 0
    st.session_state.wrong_list = []
    st.session_state.history = {}

# 側邊欄：設定
st.sidebar.title("🎮 刷題設定")
mode = st.sidebar.radio("模式選擇", ["隨機測驗", "查看錯題本"])

if mode == "隨機測驗":
    num = st.sidebar.slider("抽取題數", 5, 50, 20)
    if st.sidebar.button("重新生成考卷"):
        st.session_state.test_set = df.sample(n=min(num, len(df))).to_dict('records')
        st.session_state.current_idx = 0
        st.rerun()

# 主介面
if mode == "隨機測驗":
    if not st.session_state.test_set:
        st.info("💡 請在左側設定題數並點擊『重新生成考卷』開始。")
    else:
        idx = st.session_state.current_idx
        if idx < len(st.session_state.test_set):
            q = st.session_state.test_set[idx]
            st.write(f"**進度：{idx + 1} / {len(st.session_state.test_set)}**")
            st.subheader(q['question'])

            # 動態獲取選項
            opts = [q[f'選項{chr(65 + i)}'] for i in range(7) if
                    f'選項{chr(65 + i)}' in q and pd.notna(q[f'選項{chr(65 + i)}'])]
            labels = [chr(65 + i) for i in range(len(opts))]

            user_ans = st.radio("你的選擇：", opts, key=f"q_{idx}")

            if st.button("提交答案"):
                correct_label = q['正確答案']
                user_label = labels[opts.index(user_ans)]

                if user_label == correct_label:
                    st.success("✅ 正確！")
                else:
                    st.error(f"❌ 錯誤！正確答案是：{correct_label}")
                    if q not in st.session_state.wrong_list:
                        st.session_state.wrong_list.append(q)

                if st.button("下一題"):
                    st.session_state.current_idx += 1
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 測驗完成！")

else:  # 錯題本模式
    st.header("📓 我的錯題本")
    if not st.session_state.wrong_list:
        st.write("目前沒有錯題，繼續保持！")
    else:
        for w in st.session_state.wrong_list:
            with st.expander(f"ID: {w['id']} | {w['question'][:20]}..."):
                st.write(w['question'])
                st.info(f"正確答案：{w['正確答案']}")