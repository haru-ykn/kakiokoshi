# -*- coding: utf-8 -*-
"""
このコードは動画から文字起こしをするコードです。
ストリーミング処理版 - 出力トークン制限を回避
"""

import subprocess
import sys
import os
import time

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

def process_text_in_chunks(input_file_path, output_file_path, chunk_size=5000):#入力＋出力トークンが8192までなので、25000文字くらいまで
    """
    大きなテキストファイルをチャンクに分割して処理
    """
    # 入力ファイルを読み込み
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ファイルをチャンクに分割（行単位で分割）
    lines = content.split('\n')
    #print(lines)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        if current_size + len(line) > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = len(line)
        else:
            current_chunk.append(line)
            current_size += len(line)
    
    # 最後のチャンクを追加
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    print(f"ファイルを{len(chunks)}個のチャンクに分割しました。")
 
    
    # 出力ファイルを初期化
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# 文字起こし文の校正結果\n")
        f.write(f"# 元ファイル: {os.path.basename(input_file_path)}\n")
        f.write(f"# 処理日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# チャンク数: {len(chunks)}\n\n")
    
    # 各チャンクを処理
    for i, chunk in enumerate(chunks, 1):
        print(f"\n=== チャンク {i}/{len(chunks)} を処理中 ===")
        print(f"チャンクサイズ: {len(chunk)} 文字")
        
        process_chunk_with_streaming(chunk, output_file_path, i, len(chunks))
        
        # API制限を避けるための待機
        if i < len(chunks):
            print("次のチャンク処理まで5秒待機...")
            time.sleep(5)

def process_chunk_with_streaming(chunk_text, output_file_path, chunk_num, total_chunks):
    """
    ストリーミング処理でチャンクを処理し、随時ファイルに書き込み
    """
    prompt = f"""あなたはプロの校正者です。
以下の文章は音声認識で書き起こされたものです。誤字脱字、句読点の誤り、不自然な表現、専門用語の認識誤りを修正し、自然で正確な日本語に校正してください。
チャンク {chunk_num}/{total_chunks} の内容です。

文字起こし文:
{chunk_text}

修正された自然な日本語:
"""
    
    try:
        # ストリーミング処理を開始
        print("ストリーミング処理を開始...")
        
        # 出力ファイルにチャンクヘッダーを追加
        with open(output_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## チャンク {chunk_num}/{total_chunks}\n")
            f.write(f"処理開始: {time.strftime('%H:%M:%S')}\n\n")
        
        # ストリーミングレスポンスを処理（正しいAPI使用方法）
        response_stream = client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=[prompt],
            
        )
        
        accumulated_text = ""
        token_count = 0
        
        for response in response_stream:
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        accumulated_text += part.text
                        token_count += len(part.text.split())  # 簡易的なトークン数計算
                        
                        # 一定量のテキストが蓄積されたらファイルに書き込み
                        if len(accumulated_text) >= 1000:  # 1000文字ごとに書き込み
                            with open(output_file_path, 'a', encoding='utf-8') as f:
                                f.write(accumulated_text)
                            print(f"  {len(accumulated_text)} 文字を書き込みました (累計トークン: {token_count})")
                            accumulated_text = ""
        
        # 残りのテキストを書き込み
        if accumulated_text:
            with open(output_file_path, 'a', encoding='utf-8') as f:
                f.write(accumulated_text)
            print(f"  最終 {len(accumulated_text)} 文字を書き込みました")
        
        # チャンク終了マーカーを追加
        with open(output_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n--- チャンク {chunk_num} 完了 ---\n")
        
        print(f"チャンク {chunk_num} の処理が完了しました。")
        
    except Exception as e:
        print(f"チャンク {chunk_num} の処理中にエラーが発生しました: {e}")
        # エラー情報をファイルに記録
        with open(output_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## エラー (チャンク {chunk_num})\n")
            f.write(f"エラー内容: {str(e)}\n")
            f.write(f"発生時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

def main():
    """メイン処理"""
    # 変数定義
    input_file_path = "data/input/LLM2024_day2_s2t.txt"  # 入力ファイルのパス
    output_file_path = "data/output/processed_text_streaming.txt"  # 出力ファイルのパス
    
    # 入力ファイルの存在確認
    if not os.path.exists(input_file_path):
        print(f"入力ファイルが見つかりません: {input_file_path}")
        print("data/input/フォルダにファイルを配置してください。")
        return
    
    # 出力ディレクトリの作成
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    # ファイルサイズを確認
    file_size = os.path.getsize(input_file_path)
    print(f"入力ファイル: {input_file_path}")
    print(f"ファイルサイズ: {file_size / 1024:.2f} KB")
    print(f"推定トークン数: {file_size / 4:.0f}")
    
    # 処理開始
    print(f"\n=== ストリーミング処理を開始 ===")
    start_time = time.time()
    
    try:
        process_text_in_chunks(input_file_path, output_file_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n=== 処理完了 ===")
        print(f"処理時間: {processing_time:.2f} 秒")
        print(f"出力ファイル: {output_file_path}")
        
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main() 