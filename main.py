import streamlit as st
import requests
import json
import datetime

st.set_page_config(page_title="進捗報告フォーム", layout="centered")

# ==========================================
# 🔒 ここから：内輪専用の「合言葉ロック」機能
# ==========================================
st.sidebar.title("🔒 セキュリティ")
password = st.sidebar.text_input("合言葉を入力してください", type="password")

try:
    correct_password = st.secrets["app_password"]
except:
    correct_password = "test"

if password != correct_password: 
    st.title("進捗報告フォーム")
    st.warning("👈 左のメニューから合言葉を入力してください。（ローカルテスト時は test と入力）")
    st.stop()
# ==========================================

# ▼新しいGASのURLを貼り付け！
GAS_URL = "https://script.google.com/macros/s/AKfycbzPmwOZX06KaIM71rEXuuLssiBS5g7e9QEpFdA6kx6y2wWXHn6akGWIUIsPmdnJSEY0/exec"

st.title("進捗報告フォーム")

# 🌟 ステップ1：報告する媒体（シート）を選択
sheet_options = ["Instagram_通常投稿", "Instagram_ストーリー", "note", "Youtube"]
selected_sheet = st.selectbox("📌 報告する媒体（シート）を選択してください", sheet_options)

st.write("---")

# 🌟 ステップ2：選ばれた媒体によって表示を切り替える
if selected_sheet == "Instagram_通常投稿":
    st.write(f"【{selected_sheet}】の進捗管理画面です。")

    # セッション情報のキーにシート名を混ぜる（シートごとにデータを分けるため）
    list_key = f"existing_ids_{selected_sheet}"
    
    # 通し番号の取得（GASにシート名も一緒に送る！）
    if list_key not in st.session_state:
        with st.spinner(f'{selected_sheet} のデータを読み込み中...'):
            try:
                res = requests.get(GAS_URL, params={"action": "get_ids", "sheet_name": selected_sheet})
                st.session_state[list_key] = res.json()
            except:
                st.session_state[list_key] = []

    post_ids = ["未選択", "✨ 新規追加 (新しい通し番号を作成)"] + st.session_state[list_key]
    selected_id_option = st.selectbox("どの投稿を編集・追加しますか？ (A列)", post_ids)

    if selected_id_option != "未選択":
        is_new = selected_id_option.startswith("✨ 新規追加")
        data_key = f"data_{selected_sheet}_{selected_id_option}"
        
        if is_new:
            current_data = {}
            st.info("💡 提出すると、スプレッドシートの最終行に新しい番号で追加されます！")
        else:
            if data_key not in st.session_state:
                with st.spinner('現在の状況を読み込み中...'):
                    try:
                        res = requests.get(GAS_URL, params={"action": "get_data", "id": selected_id_option, "sheet_name": selected_sheet})
                        st.session_state[data_key] = res.json()
                    except:
                        st.session_state[data_key] = {}
            current_data = st.session_state[data_key]

        def get_default(key, options, default_val):
            val = current_data.get(key, default_val)
            return options.index(val) if val in options else 0

        st.subheader("1. 基本情報")
        # members = ["未選択", "いちか", "ぐっさん", "みひろ", "ちはるん"]
        # selected_name = st.selectbox("担当者名 (B列)", members, index=get_default("name", members, "未選択"))
        # 複数選べるmultiselectに変更！
        selected_names = st.multiselect("担当者を選択（複数選択可）", ["未定", "いちか", "ぐっさん", "みひろ", "ちはるん"])

        # 選んだ名前のリストを「、」でくっつけて1つの文字にする
        name = "、".join(selected_names) 

        # タイトル案        
        title_input = st.text_input("タイトル案 (C列)", value=current_data.get("title", ""))
        
        # 📅 日付入力をカレンダーに！
        date_val = current_data.get("date", str(datetime.date.today()))
        try:
            parsed_date = datetime.datetime.strptime(date_val[:10], "%Y-%m-%d").date()
        except:
            parsed_date = datetime.date.today()
            
        post_date = st.date_input("投稿予定日 (D列)", value=parsed_date)
        post_date = str(post_date)
        
        purpose_input = st.text_area("投稿目的 (E列)", value=current_data.get("purpose", ""))
        
        targets = ["未選択", "実行委員", "全世界"]
        selected_target = st.radio("投稿対象者 (F列)", targets, index=get_default("target", targets, "未選択"))
        
        st.write("---")
        st.subheader("2. 各タスクの進捗状況")
        
        tasks_keys = {
            "デザイン案 (G列)": "design", "文章案 (H列)": "text", 
            "デザイン依頼 (I列)": "designReq", "最終確認 (J列)": "check", "予約投稿 (K列)": "reserve"
        }
        status_options = ["未対応", "対応中", "対応済"]
        status_dict = {}
        completed_count = 0
        
        for label, key in tasks_keys.items():
            idx = get_default(key, status_options, "未対応")
            selected_status = st.selectbox(label, status_options, index=idx, key=label)
            status_dict[label] = selected_status
            if selected_status == "対応済": completed_count += 1
            elif selected_status == "対応中": completed_count += 0.5
                
        st.write("---")
        st.subheader("3. その他")
        comment = st.text_area("コメント (M列)", value=current_data.get("comment", ""))
        
        progress_percent = int((completed_count / 5.0) * 100)
        st.write(f"### ✨ 現在の進捗率 (L列)：{progress_percent}％")
        st.progress(progress_percent / 100.0)

        if st.button("🚀 提出してスプレッドシートを更新！"):
            with st.spinner('更新中...'):
                payload = {
                    "sheet_name": selected_sheet, # 🌟 送信データに「シート名」を追加！
                    "id": "新規追加" if is_new else selected_id_option,
                    "name": name, "title": title_input, "date": post_date,
                    "purpose": purpose_input, "target": selected_target,
                    "design": status_dict["デザイン案 (G列)"], "text": status_dict["文章案 (H列)"],
                    "designReq": status_dict["デザイン依頼 (I列)"], "check": status_dict["最終確認 (J列)"],
                    "reserve": status_dict["予約投稿 (K列)"], "progress": f"{progress_percent}%",
                    "comment": comment
                }
                
                requests.post(GAS_URL, data=json.dumps(payload))
                
                if list_key in st.session_state:
                    del st.session_state[list_key]
                if not is_new and data_key in st.session_state:
                    del st.session_state[data_key]
                    
                st.success("スプレッドシートを更新しました！リロードするとリストに新しい番号が反映されます！🎉")

# Instagram_通常投稿 以外の媒体が選ばれた場合の処理
else:
    st.info(f"🚧 「{selected_sheet}」の入力項目は現在準備中です！")
    st.write("今後、項目が決まり次第ここに入力フォームが追加されます。")