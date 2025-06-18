# -*- coding: utf-8 -*-
"""
このコードは動画から文字起こしをするコードです。
高度なストリーミング処理版 - プログレス表示・エラーハンドリング・再試行機能付き
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime

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

class StreamingProcessor:
    """ストリーミング処理を管理するクラス"""
    
    def __init__(self, output_file_path):
        self.output_file_path = output_file_path
        self.total_tokens_processed = 0
        self.total_chunks_processed = 0
        self.errors = []
        
    def create_output_header(self, input_file_path, total_chunks):
        """出力ファイルのヘッダーを作成"""
        with open(self.output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 文字起こし文の校正結果\n")
            f.write(f"# 元ファイル: {os.path.basename(input_file_path)}\n")
            f.write(f"# 処理開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# チャンク数: {total_chunks}\n")
            f.write(f"# モデル: gemini-2.0-flash\n")
            f.write(f"# 処理方式: ストリーミング\n\n")
    
    def split_file_into_chunks(self, input_file_path, chunk_size=50000):
        """ファイルをチャンクに分割"""
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # より賢い分割方法：文単位で分割
        sentences = []
        current_sentence = ""
        
        for char in content:
            current_sentence += char
            if char in ['。', '！', '？', '\n']:
                sentences.append(current_sentence)
                current_sentence = ""
        
        if current_sentence:
            sentences.append(current_sentence)
        
        # チャンクにまとめる
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            if current_size + len(sentence) > chunk_size and current_chunk:
                chunks.append(''.join(current_chunk))
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        return chunks
    
    def process_chunk_with_retry(self, chunk_text, chunk_num, total_chunks, max_retries=3):
        """チャンクを再試行機能付きで処理"""
        for attempt in range(max_retries):
            try:
                return self._process_chunk_streaming(chunk_text, chunk_num, total_chunks)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  エラーが発生しました。{attempt + 1}回目の再試行... ({e})")
                    time.sleep(2 ** attempt)  # 指数バックオフ
                else:
                    print(f"  最大再試行回数に達しました。エラーを記録します。")
                    self.errors.append({
                        'chunk': chunk_num,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    return False
        return False
    
    def _process_chunk_streaming(self, chunk_text, chunk_num, total_chunks):
        """ストリーミング処理でチャンクを処理"""
        prompt = f"""以下の文字起こし文を自然な日本語に修正してください。
チャンク {chunk_num}/{total_chunks} の内容です。

文字起こし文:
{chunk_text}

修正された自然な日本語:
"""
        
        # 出力ファイルにチャンクヘッダーを追加
        with open(self.output_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## チャンク {chunk_num}/{total_chunks}\n")
            f.write(f"処理開始: {datetime.now().strftime('%H:%M:%S')}\n\n")
        
        # ストリーミングレスポンスを処理（正しいAPI使用方法）
        response_stream = client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=[prompt],
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 0.1,
            }
        )
        
        accumulated_text = ""
        token_count = 0
        write_count = 0
        
        for response in response_stream:
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        accumulated_text += part.text
                        token_count += len(part.text.split())
                        
                        # 一定量のテキストが蓄積されたらファイルに書き込み
                        if len(accumulated_text) >= 500:  # 500文字ごとに書き込み
                            with open(self.output_file_path, 'a', encoding='utf-8') as f:
                                f.write(accumulated_text)
                            write_count += 1
                            print(f"    {write_count}回目の書き込み: {len(accumulated_text)} 文字")
                            accumulated_text = ""
        
        # 残りのテキストを書き込み
        if accumulated_text:
            with open(self.output_file_path, 'a', encoding='utf-8') as f:
                f.write(accumulated_text)
            write_count += 1
            print(f"   最終書き込み: {len(accumulated_text)} 文字")
        
        # チャンク終了マーカーを追加
        with open(self.output_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n--- チャンク {chunk_num} 完了 ({token_count} トークン) ---\n")
        
        self.total_tokens_processed += token_count
        self.total_chunks_processed += 1
        
        return True
    
    def save_processing_log(self):
        """処理ログを保存"""
        log_data = {
            'processing_summary': {
                'total_chunks_processed': self.total_chunks_processed,
                'total_tokens_processed': self.total_tokens_processed,
                'errors': self.errors,
                'completion_time': datetime.now().isoformat()
            }
        }
        
        log_file = self.output_file_path.replace('.txt', '_log.json')
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"処理ログを保存しました: {log_file}")

def main():
    """メイン処理"""
    # 設定
    input_file_path = "data/input/LLM2024_day2_s2t.txt"
    output_file_path = "data/output/processed_text_advanced_streaming.txt"
    chunk_size = 50000  # チャンクサイズ（文字数）
    
    # 入力ファイルの存在確認
    if not os.path.exists(input_file_path):
        print(f"入力ファイルが見つかりません: {input_file_path}")
        return
    
    # 出力ディレクトリの作成
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    # ファイル情報を表示
    file_size = os.path.getsize(input_file_path)
    print(f"=== ファイル情報 ===")
    print(f"入力ファイル: {input_file_path}")
    print(f"ファイルサイズ: {file_size / 1024:.2f} KB")
    print(f"推定トークン数: {file_size / 4:.0f}")
    
    # ストリーミングプロセッサーを初期化
    processor = StreamingProcessor(output_file_path)
    
    # ファイルをチャンクに分割
    print(f"\n=== ファイル分割 ===")
    chunks = processor.split_file_into_chunks(input_file_path, chunk_size)
    print(f"チャンク数: {len(chunks)}")
    
    # 出力ファイルのヘッダーを作成
    processor.create_output_header(input_file_path, len(chunks))
    
    # 処理開始
    print(f"\n=== ストリーミング処理開始 ===")
    start_time = time.time()
    
    try:
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- チャンク {i}/{len(chunks)} 処理中 ---")
            print(f"チャンクサイズ: {len(chunk)} 文字")
            
            success = processor.process_chunk_with_retry(chunk, i, len(chunks))
            
            if success:
                print(f"✓ チャンク {i} 完了")
            else:
                print(f"✗ チャンク {i} 失敗")
            
            # API制限を避けるための待機
            if i < len(chunks):
                print("次のチャンク処理まで3秒待機...")
                time.sleep(3)
        
        # 処理完了
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n=== 処理完了 ===")
        print(f"処理時間: {processing_time:.2f} 秒")
        print(f"処理済みチャンク: {processor.total_chunks_processed}/{len(chunks)}")
        print(f"総処理トークン数: {processor.total_tokens_processed}")
        print(f"エラー数: {len(processor.errors)}")
        print(f"出力ファイル: {output_file_path}")
        
        # 処理ログを保存
        processor.save_processing_log()
        
        # エラーがある場合は表示
        if processor.errors:
            print(f"\n=== エラー一覧 ===")
            for error in processor.errors:
                print(f"チャンク {error['chunk']}: {error['error']}")
        
    except KeyboardInterrupt:
        print(f"\n処理が中断されました。")
        processor.save_processing_log()
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        processor.save_processing_log()

if __name__ == "__main__":
    main() 