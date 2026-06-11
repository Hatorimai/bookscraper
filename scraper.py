"""Books to Scrape (https://books.toscrape.com) から書籍情報を収集し、
CSVファイルに出力するスクレイピングツール。

使い方:
    python scraper.py            # 全ページ(50ページ)を取得
    python scraper.py --pages 3  # 最初の3ページだけ取得(動作確認用)
"""

import argparse
import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
TOTAL_PAGES = 50
REQUEST_INTERVAL = 1.0  # サーバー負荷軽減のためのアクセス間隔(秒)
MAX_RETRIES = 3         # 通信失敗時の最大再試行回数

# 星評価のクラス名(英単語)を数値に変換するための対応表
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def fetch_page(url: str) -> str | None:
    """指定URLのHTMLを取得する。失敗時はMAX_RETRIES回まで再試行する。"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # サーバーがcharsetを宣言していないため文字コードを明示する
            # (これがないと £ が Â£ に化ける)
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            print(f"  通信エラー({attempt}/{MAX_RETRIES}回目): {e}")
            time.sleep(2)
    return None


def parse_books(html: str) -> list[dict]:
    """1ページ分のHTMLから書籍情報のリストを抽出する。"""
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"]
        price = article.select_one("p.price_color").text.strip()
        # 評価は <p class="star-rating Three"> のように2つ目のクラス名で表現される
        rating_word = article.select_one("p.star-rating")["class"][1]
        rating = RATING_MAP.get(rating_word, 0)
        availability = article.select_one("p.instock.availability").text.strip()
        detail_url = "https://books.toscrape.com/catalogue/" + article.h3.a["href"]
        books.append(
            {
                "title": title,
                "price": price,
                "rating": rating,
                "availability": availability,
                "url": detail_url,
            }
        )
    return books


def save_csv(books: list[dict], filepath: str) -> None:
    """書籍情報をCSVに保存する。utf-8-sigでExcelの文字化けを防ぐ。"""
    # 出力先フォルダが存在しなければ自動で作成する
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["title", "price", "rating", "availability", "url"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books)


def main() -> None:
    parser = argparse.ArgumentParser(description="Books to Scrape 書籍情報収集ツール")
    parser.add_argument(
        "--pages",
        type=int,
        default=TOTAL_PAGES,
        help=f"取得するページ数(デフォルト: 全{TOTAL_PAGES}ページ)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/books.csv",
        help="出力先CSVファイルのパス(デフォルト: output/books.csv)",
    )
    args = parser.parse_args()

    all_books = []
    for page in range(1, args.pages + 1):
        print(f"ページ {page}/{args.pages} を処理中...")
        html = fetch_page(BASE_URL.format(page))
        if html is None:
            print(f"  ページ {page} の取得に失敗したためスキップします")
            continue
        all_books.extend(parse_books(html))
        time.sleep(REQUEST_INTERVAL)  # サーバーへの配慮

    save_csv(all_books, args.output)
    print(f"完了: {len(all_books)} 件を {args.output} に保存しました")


if __name__ == "__main__":
    main()