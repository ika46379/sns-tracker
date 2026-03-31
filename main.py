import streamlit as st
import requests
import json

st.set_page_config(page_title="SNS進捗トラッカー", layout="centered")

# ==========================================
# 「合言葉ロック」機能
# ==========================================
st.sidebar.title("🔒 セキュリティ")
password = st.sidebar.text_input("合言葉を入力してください", type="password")

if password != st.secrets["app_password"]:
    st.title("📱 SNS進捗トラッカー")
    st.warning("👈 左のメニューから合言葉を入力してください。（※運営メンバー専用です）")
    st.stop()  # 💡ここでプログラムの実行を完全にストップし、下の画面を見せません！
# ==========================================
# 合言葉が合っていれば、下の画面が表示される
# ==========================================

GAS_URL = "https://script.google.com/macros/s/AKfycbzAta0ND9DduFmx2STcBPANdm8hD2itXjIQTSngBs47th8CwOD1FuBV12wsdc4HIHUb/exec" # ここを忘れずに！

st.title("SNS進捗トラッカー")
st.write("最新の進捗を読み込んで更新できます。")

post_ids = ["未選択", "1", "2", "3", "4"]
selected_id = st.selectbox("どの投稿の進捗ですか？", post_ids)

if selected_id != "未選択":
    # --- スプレッドシートから現在の状況を読み込む ---
    if f"data_{selected_id}" not in st.session_state:
        with st.spinner('現在の状況を読み込み中...'):
            try:
                res = requests.get(GAS_URL, params={"id": selected_id})
                st.session_state[f"data_{selected_id}"] = res.json()
            except:
                st.session_state[f"data_{selected_id}"] = {}

    current_data = st.session_state[f"data_{selected_id}"]

    # 初期値をセット（スプシにデータがあればそれを使い、なければデフォルト値を設定）
    def get_default(key, options, default_val):
        val = current_data.get(key, default_val)
        return options.index(val) if val in options else 0

    st.subheader("1. 基本情報")
    members = ["未選択", "いちか", "ぐっさん", "みひろ", "ちはるん"]
    selected_name = st.selectbox("担当者名", members, index=get_default("name", members, "未選択"))
    
    title_val = current_data.get("title", "")
    title_input = st.text_input("タイトル案", value=title_val)
    
    st.write("---")
    st.subheader("2. 各タスクの進捗状況")
    
    tasks_keys = {
        "デザイン案": "design", "文章案": "text", 
        "デザイン依頼": "designReq", "最終確認": "check", "予約投稿": "reserve"
    }
    status_options = ["未対応", "対応中", "対応済"]
    status_dict = {}
    completed_count = 0
    
    for label, key in tasks_keys.items():
        # スプシの現在の値を初期値として表示！
        idx = get_default(key, status_options, "未対応")
        selected_status = st.selectbox(label, status_options, index=idx, key=label)
        status_dict[label] = selected_status
        if selected_status == "対応済": completed_count += 1
        elif selected_status == "対応中": completed_count += 0.5
            
    comment_val = current_data.get("comment", "")
    comment = st.text_area("コメント", value=comment_val)
    progress_percent = int((completed_count / 5.0) * 100)
    
    st.write("---")
    st.write(f"### ✨ 現在の進捗率：{progress_percent}％")
    st.progress(progress_percent / 100.0) # カラースケールバーを描画！
    st.write("---")
    
    # progress_percent = int((completed_count / 5.0) * 100)
    
    if st.button("🚀 提出してスプレッドシートを更新！"):
        with st.spinner('更新中...'):
            payload = {
                "id": selected_id, "name": selected_name, "title": title_input,
                "design": status_dict["デザイン案"], "text": status_dict["文章案"],
                "designReq": status_dict["デザイン依頼"], "check": status_dict["最終確認"],
                "reserve": status_dict["予約投稿"], "progress": f"{progress_percent}%", "comment": comment
            }
            requests.post(GAS_URL, data=json.dumps(payload))
            del st.session_state[f"data_{selected_id}"]
            
            # 100%なら風船を飛ばすギミックも復活！
            if progress_percent == 100:
                st.success("更新しました！すべてのタスクが完了です！お疲れ様でした！🎉")
                st.balloons()
            else:
                st.success("更新しました！画面を再読み込みすると最新状態が反映されます。")