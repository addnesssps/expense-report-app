import io
import os
from datetime import datetime
from fpdf import FPDF


class ExpensePDF(FPDF):
    def __init__(self):
        super().__init__()
        # 日本語フォント設定
        # システムにある日本語フォントを探す
        font_paths = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        ]
        self.jp_font_name = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.add_font("JPFont", style="", fname=path, uni=True)
                    self.add_font("JPFont", style="B", fname=path, uni=True)
                    self.jp_font_name = "JPFont"
                    break
                except Exception:
                    continue

        if not self.jp_font_name:
            self.jp_font_name = "Helvetica"

    def _set_font(self, size=10, style=""):
        if self.jp_font_name == "Helvetica" and style == "B":
            self.set_font(self.jp_font_name, "B", size)
        elif self.jp_font_name != "Helvetica":
            self.set_font(self.jp_font_name, style, size)
        else:
            self.set_font(self.jp_font_name, "", size)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self._set_font(8)
        self.cell(0, 10, f"- {self.page_no()} -", align="C")


def generate_pdf_report(expenses: list[dict], applicant: str = "",
                        company: str = "", period_start: str = "",
                        period_end: str = "") -> io.BytesIO:
    pdf = ExpensePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # タイトル
    pdf._set_font(18, "B")
    pdf.cell(0, 15, "経費精算書", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 情報欄
    pdf._set_font(11)
    pdf.cell(30, 8, "会社名：")
    pdf.cell(60, 8, company)
    pdf.cell(30, 8, "申請者：")
    pdf.cell(60, 8, applicant, new_x="LMARGIN", new_y="NEXT")

    period_text = ""
    if period_start and period_end:
        period_text = f"{period_start} 〜 {period_end}"
    pdf.cell(30, 8, "対象期間：")
    pdf.cell(60, 8, period_text)
    pdf.cell(30, 8, "作成日：")
    pdf.cell(60, 8, datetime.now().strftime("%Y-%m-%d"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # テーブルヘッダー
    col_widths = [12, 25, 45, 28, 28, 52]
    headers = ["No.", "日付", "支払先", "科目", "金額", "摘要"]

    pdf._set_font(9, "B")
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C", fill=True)
    pdf.ln()

    # データ行
    pdf.set_text_color(0, 0, 0)
    pdf._set_font(9)
    total_amount = 0

    for idx, exp in enumerate(expenses, 1):
        amount = exp.get("amount", 0)
        total_amount += amount
        row_data = [
            str(idx),
            exp.get("date", ""),
            exp.get("vendor", "")[:15],
            exp.get("category", ""),
            f"{amount:,}円",
            exp.get("description", "")[:20],
        ]
        aligns = ["C", "C", "L", "C", "R", "L"]
        for i, (val, align) in enumerate(zip(row_data, aligns)):
            pdf.cell(col_widths[i], 7, val, border=1, align=align)
        pdf.ln()

    # 合計行
    pdf._set_font(10, "B")
    pdf.set_fill_color(217, 226, 243)
    merged_width = sum(col_widths[:4])
    pdf.cell(merged_width, 8, "合計", border=1, align="R", fill=True)
    pdf.cell(col_widths[4], 8, f"{total_amount:,}円", border=1, align="R", fill=True)
    pdf.cell(col_widths[5], 8, "", border=1, fill=True)
    pdf.ln(15)

    # 科目別集計
    pdf._set_font(11, "B")
    pdf.cell(0, 10, "【科目別集計】", new_x="LMARGIN", new_y="NEXT")

    category_totals = {}
    for exp in expenses:
        cat = exp.get("category", "その他")
        category_totals[cat] = category_totals.get(cat, 0) + exp.get("amount", 0)

    pdf._set_font(9, "B")
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 8, "科目", border=1, align="C", fill=True)
    pdf.cell(25, 8, "件数", border=1, align="C", fill=True)
    pdf.cell(35, 8, "金額", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf._set_font(9)
    for cat, total in sorted(category_totals.items()):
        count = sum(1 for e in expenses if e.get("category") == cat)
        pdf.cell(50, 7, cat, border=1, align="L")
        pdf.cell(25, 7, str(count), border=1, align="C")
        pdf.cell(35, 7, f"{total:,}円", border=1, align="R")
        pdf.ln()

    # BytesIOに出力
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
