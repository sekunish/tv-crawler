from contextlib import closing
import datetime
import sys
import os
import yt_dlp
import sqlite3
import pathlib
from typing import List, Set
import argparse
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# デバッグフラグ
DEBUG = True

# DB接続＆新規作成
DB_FILE = pathlib.Path(os.getcwd()) / "db.sqlite3"

# テーブル作成
DDL_FILE = pathlib.Path(os.getcwd()) / "sql" / "ddl.sql"
# 出力先
OUT = pathlib.Path(os.getcwd()) / "out"

# 検索URL
SEARH_URL = "https://tver.jp/search/{keywords}"


@dataclass
class AppArgs:
    """引数モデル"""

    keyword: List[str]
    """ 検索キーワード """

    out: str
    """ 出力ディレクトリ """


def get_args():
    """
    引数解析
    """
    parser = argparse.ArgumentParser(prog="tv-Downloader")
    parser.add_argument("keyword", nargs="+", help="検索キーワード")
    #parser.add_argument("url", nargs="*", help="URL直接指定")
    parser.add_argument("--out", "-o", default=OUT, help="出力先")

    args = parser.parse_args()

    ret = AppArgs(args.keyword, args.out)

    return ret


def init(conn: sqlite3.Connection):
    """DB初期化

    Args:
        conn (sqlite3.Connection): DBコネクション
    """    
    ddl_str = ""
    with open(DDL_FILE, "r") as ddl:
        ddl_str = ddl.read()
    conn.execute(ddl_str)

    # トランザクション開始
    conn.execute("BEGIN TRANSACTION;")

def search(args: AppArgs):
    """キーワードで検索し、URL一覧を作成

    Args:
        args (AppArgs): 引数モデル

    Returns:
        _type_: URL一覧
    """    
   
    keywords = " ".join(args.keyword)
    req_url = SEARH_URL.format(keywords=keywords)

    debug_print(f"req_url[{req_url}]")

    # URLにアクセス
    driver_opt = Options()
    driver_opt.add_argument("--headless")
    driver = webdriver.Chrome(driver_opt)
    driver.get(req_url)
    time.sleep(5)

    # URLを持つ要素を抽出する
    div1 = driver.find_element(
        By.CSS_SELECTOR, 'div[class^="search-page-main_content"]'
    )
    lst_elem = div1.find_elements(By.CSS_SELECTOR, 'a[class^="episode-pattern-"]')

    lst_url: List[str] = []
    for elem in lst_elem:

        attr = elem.get_attribute("href")
        if type(attr) is str:
            # href無しは対象外とする
            lst_url.append(attr)

    debug_print(f"lst_url[{lst_url}]")

    driver.quit()

    return list(set(lst_url))


def url_filter(conn: sqlite3.Connection, lst: List[str]):
    """
    URL一覧とDBを照合する
    
    照合し、未登録の場合はDL対象とする

    Args:
        conn (sqlite3.Connection): DBコネクション
        lst (List[str]): URL一覧

    Returns:
        _type_: DL対象URL一覧
    """    

    # DBからURL一覧を取得
    cur = conn.cursor()
    lst_url_db_cur = cur.execute("select url from t_url")
    lst_url_db = lst_url_db_cur.fetchall()
    set_url_db: Set[str] = set(map(lambda item: item[0], lst_url_db))

    # 取得したURLのうち、DBに登録されているものを除外する
    url_web = [url for url in lst if url not in set_url_db]

    debug_print(f"url_web[{url_web}]")

    return url_web


def crawler(conn: sqlite3.Connection, args: AppArgs, lst: List[str]):
    """対象URL一覧をダウンロードする

    Args:
        conn (sqlite3.Connection): DBコネクション
        args (AppArgs): 引数
        lst (List[str]): DB対象URL一覧
    """

    # 出力オプション
    ytdlp_opt = {"outtmpl": f"{args.out}/%(title)s.%(ext)s"}

    with yt_dlp.YoutubeDL(ytdlp_opt) as ydl:
        cur = conn.cursor()

        for url in lst:
            ydl.download([url])
            cur.execute(
                "INSERT INTO t_url (url) VALUES (?)",
                (url,),
            )


def main():
    """
    メイン処理
    """
    args = get_args()

    # DB 接続
    with closing(sqlite3.connect(database=DB_FILE)) as conn:
        try:
            # DB初期化処理
            print("#DB初期化処理")
            init(conn)
            # WEB検索処理
            print("#WEB検索処理")
            lst_web = search(args)
            # URLフィルタ処理
            print("#URLフィルタ処理")
            lst_filterd = url_filter(conn, lst_web)
            # DL及びDB登録処理
            print("#DL及びDB登録処理")
            crawler(conn, args, lst_filterd)

            conn.commit()
            
            return 0
        except Exception as ex:
            conn.rollback()
            print("処理に失敗しました.", file := sys.stderr)
            print(ex, file := sys.stderr)
            
            return 1


def debug_print(msg: str):
    if DEBUG:
        print(f"{datetime.datetime.now()} {msg}", file := sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
