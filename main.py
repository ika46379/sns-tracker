import streamlit as st
import requests
import json
import datetime
import pandas as pd  # 🌟 表を表示するために追加！

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
    st.warning("👈 左のメニューから合言葉を入力してください。")
    st.stop()
# ==========================================

# ▼新しいGASのURLを貼り付け！
GAS_URL = "https://script.google.com/macros/s/AKfycbzvUNk534Grp0EJULYs6OPVrNDIQKIAg6OoxS9GMEo1lLjqVJAerB3A7Bj4VYb2BCo-/exec"

st.title("進捗報告フォーム")

# 🌟 ステップ1：報告する媒体（シート）を選択
sheet_options = ["Instagram_通常投稿", "Instagram_ストーリー", "note", "Youtube"]
selected_sheet = st.selectbox("📌 報告する媒体（シート）を選択してください", sheet_options)

st.write("---")

# 🌟 ステップ2：選ばれた媒体によって表示を切り替える
if selected_sheet == "Instagram_通常投稿":
    st.write(f"【{selected_sheet}】の進捗管理画面です。")

    # ==========================================
    # 🌟 GASから表のデータ(all_data)を取得する
    # ==========================================
    all_data_key = f"all_data_{selected_sheet}"
    if all_data_key not in st.session_state:
        with st.spinner(f'{selected_sheet} のデータを読み込み中...'):
            try:
                res = requests.get(GAS_URL, params={"action": "get_all", "sheet_name": selected_sheet})
                st.session_state[all_data_key] = res.json()
            except:
                st.session_state[all_data_key] = []
                
    all_data = st.session_state[all_data_key]

    # ==========================================
    # 🌟 追加：データがあれば、綺麗な表（DataFrame）にして画面に表示する！
    # ==========================================
    if len(all_data) > 0:
        st.subheader("📋 現在の投稿一覧")
        df = pd.DataFrame(all_data)
        # 列の名前を分かりやすい日本語にする
        df = df.rename(columns={"id": "通し番号", "name": "担当者", "title": "タイトル案", "purpose": "投稿目的"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("現在登録されているデータはありません。（新規追加から始められます）")
        
    st.write("---")

    # ==========================================
    # 🌟 表のデータ (all_data) から選択肢を作る
    # ==========================================
    options = ["未選択", "✨ 新規追加 (新しい通し番号を作成)"]
    for row in all_data:
        # ※もし担当者が空欄だった場合は「未記入」と表示する安全対策付き
        options.append(f"{row['id']}: {row['title']} ({row.get('name', '未記入')})")
        
    selected_option = st.selectbox("どの投稿を編集・追加しますか？", options)

    # 選ばれた文字列から「ID（通し番号）」だけを取り出す
    if selected_option == "未選択":
        selected_id_option = "未選択"
    elif selected_option.startswith("✨ 新規追加"):
        selected_id_option = "✨ 新規追加 (新しい通し番号を作成)"
    else:
        selected_id_option = selected_option.split(":")[0] # コロンより前の番号だけ取得

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

        def get_default(key, default_options, default_val):
            val = current_data.get(key, default_val)
            return default_options.index(val) if val in default_options else 0

        st.subheader("1. 基本情報")
        # 複数選べるmultiselect
        members = ["未定", "近藤衣千花", "山口悠己", "中田光優", "中西挑遥"]
        saved_names_str = current_data.get("name", "") # スプシに保存されている文字を取得
        saved_names_list = saved_names_str.split("、") if saved_names_str else [] # 「、」で切り分けてリストに戻す
        default_names = [n for n in saved_names_list if n in members] # エラー防止用チェック
        
        selected_names = st.multiselect("担当者を選択 (B列)", members, default=default_names)
        name = "、".join(selected_names)

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
                    "sheet_name": selected_sheet, 
                    "id": "新規追加" if is_new else selected_id_option,
                    "name": name, "title": title_input, "date": post_date,
                    "purpose": purpose_input, "target": selected_target,
                    "design": status_dict["デザイン案 (G列)"], "text": status_dict["文章案 (H列)"],
                    "designReq": status_dict["デザイン依頼 (I列)"], "check": status_dict["最終確認 (J列)"],
                    "reserve": status_dict["予約投稿 (K列)"], "progress": f"{progress_percent}%",
                    "comment": comment
                }
                
                requests.post(GAS_URL, data=json.dumps(payload))
                
                # 提出後にキャッシュを消して、次に画面を見た時に最新の表が出るようにする
                if all_data_key in st.session_state:
                    del st.session_state[all_data_key]
                if not is_new and data_key in st.session_state:
                    del st.session_state[data_key]
                    
                st.success("スプレッドシートを更新しました！リロードすると表とリストに新しい情報が反映されます！🎉")

# Instagram_通常投稿 以外の媒体が選ばれた場合の処理
# ==========================================
# 🌟 【追加1】Instagram_ストーリー の画面
# ==========================================
elif selected_sheet == "Instagram_ストーリー":
    st.write(f"【{selected_sheet}】の進捗管理画面です。")

    all_data_key = f"all_data_{selected_sheet}"
    if all_data_key not in st.session_state:
        with st.spinner(f'{selected_sheet} のデータを読み込み中...'):
            try:
                res = requests.get(GAS_URL, params={"action": "get_all", "sheet_name": selected_sheet})
                st.session_state[all_data_key] = res.json()
            except:
                st.session_state[all_data_key] = []
                
    all_data = st.session_state[all_data_key]

    if len(all_data) > 0:
        st.subheader("📋 現在のストーリー一覧")
        df = pd.DataFrame(all_data)
        
        # 💡 "date"（GASから送られてきたD列）を "投稿内容" にリネームします！
        df = df.rename(columns={
            "id": "通し番号", 
            "name": "担当者", 
            "title": "投稿予定日", 
            "date": "投稿内容",    
            "purpose": "投稿完了"
        })
        
        # （※GASから来たデータにこれらの列がちゃんとある場合のみ並び替えます）
        if "投稿内容" in df.columns:
            df = df[["通し番号", "担当者", "投稿予定日", "投稿内容", "投稿完了"]]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("現在登録されているデータはありません。")
        
    st.write("---")

    options = ["未選択", "✨ 新規追加 (新しい通し番号を作成)"]
    for row in all_data:
        options.append(f"{row['id']}: {row['title']} ({row.get('name', '未記入')})")
        
    selected_option = st.selectbox("どの投稿を編集・追加しますか？", options, key="story_select")

    if selected_option == "未選択":
        selected_id_option = "未選択"
    elif selected_option.startswith("✨ 新規追加"):
        selected_id_option = "✨ 新規追加 (新しい通し番号を作成)"
    else:
        selected_id_option = selected_option.split(":")[0]

    if selected_id_option != "未選択":
        is_new = selected_id_option.startswith("✨ 新規追加")
        data_key = f"data_{selected_sheet}_{selected_id_option}"
        
        if is_new:
            current_data = {}
        else:
            if data_key not in st.session_state:
                with st.spinner('データを読み込み中...'):
                    try:
                        res = requests.get(GAS_URL, params={"action": "get_data", "id": selected_id_option, "sheet_name": selected_sheet})
                        st.session_state[data_key] = res.json()
                    except:
                        st.session_state[data_key] = {}
            current_data = st.session_state[data_key]

        st.subheader("1. 投稿情報")
        # B列: 担当者
        members = ["未定", "近藤衣千花", "山口悠己", "中田光優", "中西挑遥"]
        saved_names_str = current_data.get("name", "")
        saved_names_list = saved_names_str.split("、") if saved_names_str else []
        default_names = [n for n in saved_names_list if n in members]
        
        selected_names = st.multiselect("担当者を選択 (B列)", members, default=default_names, key="story_names")
        name = "、".join(selected_names)
        # C列: 投稿予定日 (GASから 'title' という名前で来る箱に入れます)
        date_val = current_data.get("title", str(datetime.date.today()))
        try:
            parsed_date = datetime.datetime.strptime(date_val[:10], "%Y-%m-%d").date()
        except:
            parsed_date = datetime.date.today()
        post_date = st.date_input("投稿予定日 (C列)", value=parsed_date, key="story_date")
        
        # D列: 投稿内容 (GASから 'date' という名前で来る箱に入れます)
        content_input = st.text_area("投稿内容 (D列)", value=current_data.get("date", ""), key="story_content")
        
        st.write("---")
        st.subheader("2. 完了確認とコメント")
        
        # E列: 投稿完了 (GASから 'purpose' という名前で来る箱に入れます)
        status_options = ["未対応", "対応済"]
        def get_default(key, default_options, default_val):
            val = current_data.get(key, default_val)
            return default_options.index(val) if val in default_options else 0
            
        is_completed = st.selectbox("投稿完了 (E列)", status_options, index=get_default("purpose", status_options, "未対応"), key="story_comp")
        
        # F列: コメント (GASから 'target' という名前で来る箱に入れます)
        comment = st.text_area("コメント (F列)", value=current_data.get("target", ""), key="story_comment")

        if st.button("🚀 提出してスプレッドシートを更新！", key="story_submit"):
            with st.spinner('更新中...'):
                payload = {
                    "sheet_name": selected_sheet, 
                    "id": "新規追加" if is_new else selected_id_option,
                    "name": name,                  # B列へ
                    "title": str(post_date),       # C列へ
                    "date": content_input,         # D列へ
                    "purpose": is_completed,       # E列へ
                    "target": comment              # F列へ
                }
                requests.post(GAS_URL, data=json.dumps(payload))
                
                if all_data_key in st.session_state: del st.session_state[all_data_key]
                if not is_new and data_key in st.session_state: del st.session_state[data_key]
                st.success("スプレッドシートを更新しました！リロードすると表に反映されます！🎉")


# ==========================================
# 🌟 【追加2】note の画面
# ==========================================
elif selected_sheet == "note":
    st.write(f"【{selected_sheet}】の進捗管理画面です。")

    all_data_key = f"all_data_{selected_sheet}"
    if all_data_key not in st.session_state:
        with st.spinner(f'{selected_sheet} のデータを読み込み中...'):
            try:
                res = requests.get(GAS_URL, params={"action": "get_all", "sheet_name": selected_sheet})
                st.session_state[all_data_key] = res.json()
            except:
                st.session_state[all_data_key] = []
                
    all_data = st.session_state[all_data_key]

    if len(all_data) > 0:
        st.subheader("📋 現在のnote一覧")
        df = pd.DataFrame(all_data)
        # 💡 noteでは C列が"title"、E列が"purpose"なのでそのまま綺麗にリネーム！
        df = df.rename(columns={"id": "通し番号", "name": "担当者", "title": "タイトル案", "purpose": "投稿目的"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("現在登録されているデータはありません。")
        
    st.write("---")

    options = ["未選択", "✨ 新規追加 (新しい通し番号を作成)"]
    for row in all_data:
        options.append(f"{row['id']}: {row['title']} ({row.get('name', '未記入')})")
        
    selected_option = st.selectbox("どの投稿を編集・追加しますか？", options, key="note_select")

    if selected_option == "未選択":
        selected_id_option = "未選択"
    elif selected_option.startswith("✨ 新規追加"):
        selected_id_option = "✨ 新規追加 (新しい通し番号を作成)"
    else:
        selected_id_option = selected_option.split(":")[0]

    if selected_id_option != "未選択":
        is_new = selected_id_option.startswith("✨ 新規追加")
        data_key = f"data_{selected_sheet}_{selected_id_option}"
        
        if is_new:
            current_data = {}
        else:
            if data_key not in st.session_state:
                with st.spinner('データを読み込み中...'):
                    try:
                        res = requests.get(GAS_URL, params={"action": "get_data", "id": selected_id_option, "sheet_name": selected_sheet})
                        st.session_state[data_key] = res.json()
                    except:
                        st.session_state[data_key] = {}
            current_data = st.session_state[data_key]

        st.subheader("1. 基本情報")
        # B列: 担当者
        # B列: 担当者（履歴復元機能付き！）
        members = ["未定", "近藤衣千花", "山口悠己", "中田光優", "中西挑遥"]
        saved_names_str = current_data.get("name", "")
        saved_names_list = saved_names_str.split("、") if saved_names_str else []
        default_names = [n for n in saved_names_list if n in members]
        
        selected_names = st.multiselect("担当者を選択 (B列)", members, default=default_names, key="note_names")
        name = "、".join(selected_names)

        # C列: タイトル案
        title_input = st.text_input("タイトル案 (C列)", value=current_data.get("title", ""), key="note_title")
        
        # D列: 投稿予定日
        date_val = current_data.get("date", str(datetime.date.today()))
        try:
            parsed_date = datetime.datetime.strptime(date_val[:10], "%Y-%m-%d").date()
        except:
            parsed_date = datetime.date.today()
        post_date = st.date_input("投稿予定日 (D列)", value=parsed_date, key="note_date")
        
        # E列: 投稿目的
        purpose_input = st.text_area("投稿目的 (E列)", value=current_data.get("purpose", ""), key="note_purpose")

        st.write("---")
        st.subheader("2. 進捗状況とコメント")
        
        # F列: 進捗状況 (GASから 'target' という名前で来る箱に入れます)
        status_options = ["未着手", "執筆中", "確認待ち", "完了"]
        def get_default(key, default_options, default_val):
            val = current_data.get(key, default_val)
            return default_options.index(val) if val in default_options else 0
            
        progress_status = st.selectbox("進捗状況 (F列)", status_options, index=get_default("target", status_options, "未着手"), key="note_prog")
        
        # G列: コメント (GASから 'design' という名前で来る箱に入れます)
        comment = st.text_area("コメント (G列)", value=current_data.get("design", ""), key="note_comment")

        if st.button("🚀 提出してスプレッドシートを更新！", key="note_submit"):
            with st.spinner('更新中...'):
                payload = {
                    "sheet_name": selected_sheet, 
                    "id": "新規追加" if is_new else selected_id_option,
                    "name": name,                  # B列へ
                    "title": title_input,          # C列へ
                    "date": str(post_date),        # D列へ
                    "purpose": purpose_input,      # E列へ
                    "target": progress_status,     # F列へ
                    "design": comment              # G列へ
                }
                requests.post(GAS_URL, data=json.dumps(payload))
                
                if all_data_key in st.session_state: del st.session_state[all_data_key]
                if not is_new and data_key in st.session_state: del st.session_state[data_key]
                st.success("スプレッドシートを更新しました！リロードすると表に反映されます！🎉")


# ==========================================
# 🚧 その他の準備中シート
# ==========================================
else:
    st.info(f"🚧 「{selected_sheet}」の入力項目は現在準備中です！")