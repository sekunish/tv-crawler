# tv-crawler

## 概要

- selenium と yt-dlp を利用したダウンローダー
- yt-dlp が重複した URL はダウンロードしない仕組みを持っているが、ファイル名が変わった場合は再ダウンロードされる
- 一度実行した URL は対象外とする

## 前提条件

1. selenium のインストール

   1. apt(debian 系)の場合

      - ドライバのインストール

        > sudo apt install chromium-chromedriver

      - ドライバのパスを確認
        > which chromedriver

## 利用方法

1. 仮想環境(pipenv)を利用する場合

   1. pipenv のインストール

      > pip install pipenv

   1. ライブラリのインストール

      > pipenv install

   1. 実行
      > pipenv run python main.py キーワード --out 出力先

1. 仮想環境を利用しない場合

   1. ライブラリのインストール

      > pip install -r requirements.txt

   1. 実行
      > python main.py キーワード --out 出力先
