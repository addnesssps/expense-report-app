import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime, date

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from modules.database import init_db, add_expense, get_expenses, update_expense, delete_expense, get_categories
from modules.ocr import extract_text, save_uploaded_file
from modules.parser import parse_receipt
from modules.excel_report import generate_excel_report
from modules.pdf_report import generate_pdf_report

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# DB初期化
init_db()

# ページ設定
st.set_page_config(
    page_title="経費精算システム",
    page_icon="receipt",
    layout="wide",
)

st.title("経費精算システム")

# サイドバーでページ切替
page = st.sidebar.radio(
    "メニュー",
    ["領収書登録", "経費一覧", "レポート生成"],
)

# ========== 領収書登録ページ ==========
if page == "領収書登録":
    st.header("領収書登録")

    tab1, tab2 = st.tabs(["領収書アップロード", "手動入力"])

    # --- 領収書アップロードタブ ---
    with tab1:
        uploaded_files = st.file_uploader(
            "領収書をアップロード（画像またはPDF）",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.subheader(f"ファイル: {uploaded_file.name}")

                col1, col2 = st.columns([1, 1])

                with col1:
                    # 画像プレビュー
                    if uploaded_file.type.startswith("image"):
                        st.image(uploaded_file, width=300)
                    else:
                        st.info(f"PDF: {uploaded_file.name}")

                    # ファイル保存 & OCR実行
                    file_path = save_uploaded_file(uploaded_file, UPLOAD_DIR)
                    with st.spinner("OCR処理中..."):
                        ocr_text = extract_text(file_path)

                    if ocr_text:
                        with st.expander("OCR結果テキスト"):
                            st.text(ocr_text)
                        parsed = parse_receipt(ocr_text)
                    else:
                        parsed = {"date": datetime.now().strftime("%Y-%m-%d"),
                                  "amount": 0, "vendor": "", "category": "雑費"}

                with col2:
                    st.write("**解析結果（編集可能）**")
                    key_prefix = f"upload_{uploaded_file.name}"

                    exp_date = st.date_input(
                        "日付",
                        value=datetime.strptime(parsed["date"], "%Y-%m-%d").date()
                            if parsed["date"] else date.today(),
                        key=f"{key_prefix}_date",
                    )
                    vendor = st.text_input("支払先", value=parsed["vendor"],
                                           key=f"{key_prefix}_vendor")
                    amount = st.number_input("金額（円）", value=parsed["amount"],
                                             min_value=0, step=1,
                                             key=f"{key_prefix}_amount")
                    category = st.selectbox("科目", get_categories(),
                                            index=get_categories().index(parsed["category"])
                                            if parsed["category"] in get_categories() else 0,
                                            key=f"{key_prefix}_cat")
                    description = st.text_input("摘要", key=f"{key_prefix}_desc")

                    if st.button("登録", key=f"{key_prefix}_btn", type="primary"):
                        add_expense(
                            date=exp_date.strftime("%Y-%m-%d"),
                            vendor=vendor,
                            amount=int(amount),
                            category=category,
                            description=description,
                            receipt_path=file_path,
                        )
                        st.success("経費を登録しました！")

                st.divider()

    # --- 手動入力タブ ---
    with tab2:
        with st.form("manual_entry"):
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("日付", value=date.today())
                vendor = st.text_input("支払先")
                amount = st.number_input("金額（円）", min_value=0, step=1)
            with col2:
                category = st.selectbox("科目", get_categories())
                description = st.text_input("摘要")

            submitted = st.form_submit_button("登録", type="primary")
            if submitted:
                if amount > 0:
                    add_expense(
                        date=exp_date.strftime("%Y-%m-%d"),
                        vendor=vendor,
                        amount=int(amount),
                        category=category,
                        description=description,
                    )
                    st.success("経費を登録しました！")
                else:
                    st.warning("金額を入力してください。")

# ========== 経費一覧ページ ==========
elif page == "経費一覧":
    st.header("経費一覧")

    # フィルター
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_start = st.date_input("開始日", value=date(date.today().year, date.today().month, 1))
    with col2:
        filter_end = st.date_input("終了日", value=date.today())
    with col3:
        filter_cat = st.selectbox("科目フィルター", ["すべて"] + get_categories())

    expenses = get_expenses(
        start_date=filter_start.strftime("%Y-%m-%d"),
        end_date=filter_end.strftime("%Y-%m-%d"),
        category=filter_cat if filter_cat != "すべて" else None,
    )

    if expenses:
        # 集計サマリー
        total = sum(e["amount"] for e in expenses)
        st.metric("合計金額", f"¥{total:,}", delta=f"{len(expenses)}件")

        # データテーブル
        df = pd.DataFrame(expenses)
        display_df = df[["id", "date", "vendor", "category", "amount", "description"]].copy()
        display_df.columns = ["ID", "日付", "支払先", "科目", "金額", "摘要"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # 削除機能
        with st.expander("経費を削除"):
            del_id = st.number_input("削除するID", min_value=1, step=1, key="del_id")
            if st.button("削除", type="secondary"):
                delete_expense(int(del_id))
                st.success(f"ID {del_id} を削除しました。ページを更新してください。")
                st.rerun()
    else:
        st.info("該当する経費データがありません。")

# ========== レポート生成ページ ==========
elif page == "レポート生成":
    st.header("レポート生成")

    col1, col2 = st.columns(2)
    with col1:
        report_start = st.date_input("開始日", value=date(date.today().year, date.today().month, 1),
                                     key="report_start")
        report_end = st.date_input("終了日", value=date.today(), key="report_end")
    with col2:
        company = st.text_input("会社名", value="")
        applicant = st.text_input("申請者名", value="")

    expenses = get_expenses(
        start_date=report_start.strftime("%Y-%m-%d"),
        end_date=report_end.strftime("%Y-%m-%d"),
    )

    if expenses:
        total = sum(e["amount"] for e in expenses)
        st.write(f"対象件数: **{len(expenses)}件** / 合計金額: **¥{total:,}**")

        # 科目別集計
        category_summary = {}
        for exp in expenses:
            cat = exp["category"]
            category_summary[cat] = category_summary.get(cat, 0) + exp["amount"]

        summary_df = pd.DataFrame([
            {"科目": cat, "金額": amt} for cat, amt in sorted(category_summary.items())
        ])
        if not summary_df.empty:
            st.bar_chart(summary_df.set_index("科目"))

        st.divider()

        # ダウンロードボタン
        col1, col2 = st.columns(2)

        with col1:
            excel_data = generate_excel_report(
                expenses, applicant=applicant, company=company,
                period_start=report_start.strftime("%Y-%m-%d"),
                period_end=report_end.strftime("%Y-%m-%d"),
            )
            filename_excel = f"経費精算書_{report_start.strftime('%Y%m')}_{report_end.strftime('%Y%m')}.xlsx"
            st.download_button(
                label="Excel精算書ダウンロード",
                data=excel_data,
                file_name=filename_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

        with col2:
            pdf_data = generate_pdf_report(
                expenses, applicant=applicant, company=company,
                period_start=report_start.strftime("%Y-%m-%d"),
                period_end=report_end.strftime("%Y-%m-%d"),
            )
            filename_pdf = f"経費精算書_{report_start.strftime('%Y%m')}_{report_end.strftime('%Y%m')}.pdf"
            st.download_button(
                label="PDF精算書ダウンロード",
                data=pdf_data,
                file_name=filename_pdf,
                mime="application/pdf",
                type="primary",
            )
    else:
        st.info("対象期間の経費データがありません。先に「領収書登録」から経費を登録してください。")
