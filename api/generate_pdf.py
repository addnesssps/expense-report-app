from http.server import BaseHTTPRequestHandler
import json
import io
import base64
from datetime import datetime
from fpdf import FPDF


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))
        expenses = body.get("expenses", [])
        applicant = body.get("applicant", "")
        company = body.get("company", "")
        period_start = body.get("period_start", "")
        period_end = body.get("period_end", "")

        output = _generate_pdf(expenses, applicant, company, period_start, period_end)
        b64 = base64.b64encode(output.read()).decode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"data": b64}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def _generate_pdf(expenses, applicant, company, period_start, period_end):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Use Helvetica (built-in, no Japanese font on serverless)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Expense Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(30, 8, "Company:")
    pdf.cell(60, 8, company)
    pdf.cell(30, 8, "Applicant:")
    pdf.cell(60, 8, applicant, new_x="LMARGIN", new_y="NEXT")

    period_text = f"{period_start} - {period_end}" if period_start and period_end else ""
    pdf.cell(30, 8, "Period:")
    pdf.cell(60, 8, period_text)
    pdf.cell(30, 8, "Date:")
    pdf.cell(60, 8, datetime.now().strftime("%Y-%m-%d"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    col_widths = [12, 25, 45, 28, 28, 52]
    headers = ["No.", "Date", "Vendor", "Category", "Amount", "Note"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    total_amount = 0

    for idx, exp in enumerate(expenses, 1):
        amount = exp.get("amount", 0)
        total_amount += amount
        row_data = [
            str(idx), exp.get("date", ""), exp.get("vendor", "")[:15],
            exp.get("category", ""), f"{amount:,}", exp.get("description", "")[:20],
        ]
        aligns = ["C", "C", "L", "C", "R", "L"]
        for i, (val, align) in enumerate(zip(row_data, aligns)):
            pdf.cell(col_widths[i], 7, val, border=1, align=align)
        pdf.ln()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(217, 226, 243)
    merged_width = sum(col_widths[:4])
    pdf.cell(merged_width, 8, "Total", border=1, align="R", fill=True)
    pdf.cell(col_widths[4], 8, f"{total_amount:,}", border=1, align="R", fill=True)
    pdf.cell(col_widths[5], 8, "", border=1, fill=True)
    pdf.ln(15)

    # Category summary
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "Category Summary", new_x="LMARGIN", new_y="NEXT")

    category_totals = {}
    for exp in expenses:
        cat = exp.get("category", "Other")
        category_totals[cat] = category_totals.get(cat, 0) + exp.get("amount", 0)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 8, "Category", border=1, align="C", fill=True)
    pdf.cell(25, 8, "Count", border=1, align="C", fill=True)
    pdf.cell(35, 8, "Amount", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for cat, total in sorted(category_totals.items()):
        count = sum(1 for e in expenses if e.get("category") == cat)
        pdf.cell(50, 7, cat, border=1, align="L")
        pdf.cell(25, 7, str(count), border=1, align="C")
        pdf.cell(35, 7, f"{total:,}", border=1, align="R")
        pdf.ln()

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
