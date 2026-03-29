import re
from datetime import datetime


def parse_date(text: str) -> str | None:
    patterns = [
        # 2024年3月15日
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        # 2024/03/15 or 2024-03-15
        r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',
        # R6.3.15 (令和)
        r'[Rr令]\s*(\d{1,2})[.\s年](\d{1,2})[.\s月](\d{1,2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            year = int(groups[0])
            month = int(groups[1])
            day = int(groups[2])
            # 令和変換
            if year < 100:
                year += 2018
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"
    return None


def parse_amount(text: str) -> int | None:
    patterns = [
        # ¥1,234 or ￥1,234
        r'[¥￥]\s*([\d,]+)',
        # 合計 1,234円 or 合計金額 1,234円
        r'(?:合計|小計|合計金額|お支払い|支払|総額)\s*[：:\s]*[¥￥]?\s*([\d,]+)\s*円?',
        # 1,234円
        r'([\d,]+)\s*円',
    ]
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            cleaned = m.replace(",", "").replace(" ", "")
            if cleaned.isdigit():
                amounts.append(int(cleaned))
    if not amounts:
        return None
    # 最大値を合計金額として返す（小計より合計が大きいはず）
    return max(amounts)


def parse_vendor(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ""
    # 最初の非空行を店名と推定（多くの領収書は店名が先頭）
    for line in lines[:3]:
        # 日付行や金額行をスキップ
        if re.match(r'^\d{4}[/\-年]', line):
            continue
        if re.match(r'^[¥￥]', line):
            continue
        if len(line) >= 2:
            return line
    return lines[0] if lines else ""


def guess_category(text: str, vendor: str) -> str:
    text_lower = (text + " " + vendor).lower()
    category_keywords = {
        "交通費": ["タクシー", "taxi", "電車", "バス", "suica", "pasmo", "jr", "鉄道",
                   "交通", "駐車", "パーキング", "高速", "etcカード"],
        "交際費": ["居酒屋", "レストラン", "飲食", "懇親", "接待", "ディナー", "ランチ",
                   "カフェ", "バー", "宴会"],
        "会議費": ["会議室", "貸会議", "コワーキング", "スターバックス", "ドトール",
                   "タリーズ", "コーヒー"],
        "消耗品費": ["文房具", "コピー", "印刷", "用紙", "トナー", "インク", "事務",
                    "amazon", "ヨドバシ", "ビック"],
        "通信費": ["電話", "携帯", "インターネット", "wi-fi", "回線", "通信"],
        "旅費交通費": ["ホテル", "宿泊", "旅館", "航空", "新幹線", "飛行機", "出張"],
        "新聞図書費": ["書籍", "本", "新聞", "雑誌", "書店", "amazon kindle"],
    }
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "雑費"


def parse_receipt(text: str) -> dict:
    date = parse_date(text)
    amount = parse_amount(text)
    vendor = parse_vendor(text)
    category = guess_category(text, vendor)
    return {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "amount": amount or 0,
        "vendor": vendor,
        "category": category,
    }
