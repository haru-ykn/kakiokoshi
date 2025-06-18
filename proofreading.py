# -*- coding: utf-8 -*-
"""
このコードは動画から文字起こしをするコードです。
ローカル環境用に修正版
"""

import subprocess
import sys

def install_package(package):
    """パッケージがインストールされていない場合に自動インストール"""
    try:
        __import__(package)
    except ImportError:
        print(f"{package}パッケージをインストールしています...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package}のインストールが完了しました。")

# 必要なパッケージを自動インストール
install_package("google-genai")

import os
from google import genai
from google.genai import types

# 方法1: 環境変数からAPIキーを取得（推奨）
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 方法2: 直接設定する場合（セキュリティ上推奨されません）
# GEMINI_API_KEY = "your-api-key-here"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY環境変数が設定されていません。"
                    "以下のコマンドで設定してください：\n"
                    "Windows: set GEMINI_API_KEY=your-api-key\n"
                    "Mac/Linux: export GEMINI_API_KEY=your-api-key")

# APIキーのモデルへの設定
client = genai.Client(api_key=GEMINI_API_KEY)

# 変数定義
# ファイルのPATH（ローカル環境用に修正）
file_path = "input_text.txt"  # 入力ファイルのパス
output_file_path = "processed_text.txt"  # 出力ファイルのパス
prompt = "このファイルの書きおこし文を自然な日本語に修正してください。"

# ファイルを読み込む
myfile = client.files.upload(file=file_path)

# gemini2.0で生成
response = client.models.generate_content(
    model="gemini-2.0-flash", contents=[prompt, myfile]
)

print(response.text)

# responseの内容をファイルに保存
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(response.text)