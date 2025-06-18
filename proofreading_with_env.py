# -*- coding: utf-8 -*-
"""
このコードは動画から文字起こしをするコードです。
.envファイルを使用した安全なAPIキー設定版
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
install_package("python-dotenv")
install_package("google-genai")

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .envファイルから環境変数を読み込み
load_dotenv()

# APIキーを環境変数から取得
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEYが設定されていません。"
                    ".envファイルに以下を追加してください：\n"
                    "GEMINI_API_KEY=your-api-key-here")

# APIキーのモデルへの設定
client = genai.Client(api_key=GEMINI_API_KEY)

# 変数定義
file_path = "data/input/LLM2024_day7_s2t.txt"  # 入力ファイルのパス
output_file_path = "data/output/processed_text_llm2024_day7.txt"  # 出力ファイルのパス
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