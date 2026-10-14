"""scraper.py のテスト。保存した HTML を使うので、実際のサイトにはアクセスしない。"""

import csv
from pathlib import Path

import scraper

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "page.html"


def test_parse_books_reads_title_price_rating_and_url():
    books = scraper.parse_books(FIXTURE.read_text(encoding="utf-8"))
    assert len(books) == 2
    first = books[0]
    assert first["title"] == "A Light in the Attic"   # 省略される前の書名(title 属性)を使う
    assert first["price"] == "£51.77"
    assert first["rating"] == 3                       # "Three" を数値に変換
    assert first["availability"] == "In stock"
    assert first["url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert books[1]["rating"] == 1


def test_save_csv_creates_folder_and_opens_in_excel_without_garbled_text(tmp_path):
    out = tmp_path / "new_folder" / "books.csv"
    scraper.save_csv([{"title": "テスト", "price": "£1.00", "rating": 5, "availability": "In stock", "url": "u"}], str(out))
    raw = out.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")             # BOM 付き UTF-8(Excel で文字化けしない)
    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["title"] == "テスト"
