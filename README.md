# 文字起こし文の校正ツール

このツールは、動画から文字起こしされたテキストを自然な日本語に修正するためのPythonスクリプトです。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. APIキーをコピーして保存

### 3. APIキーの設定

#### 方法1: 環境変数を使用（推奨）

**Windows:**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Mac/Linux:**
```bash
export GEMINI_API_KEY=your-api-key-here
```

#### 方法2: .envファイルを使用

1. `env_example.txt`を`.env`にコピー
2. `.env`ファイルを編集して実際のAPIキーを設定：
```
GEMINI_API_KEY=your-actual-api-key-here
```

#### 方法3: バッチファイルを使用（Windows）

`setup_env.bat`を実行して、対話的にAPIキーを設定できます。

## 使用方法

### 基本的な使用方法

```bash
python proofreading.py
```

### .envファイルを使用する場合

```bash
python proofreading_with_env.py
```

## ファイル構成

- `proofreading.py` - 環境変数を使用するメインスクリプト
- `proofreading_with_env.py` - .envファイルを使用するバージョン
- `setup_env.bat` - Windows用環境変数設定ツール
- `env_example.txt` - .envファイルのテンプレート
- `requirements.txt` - 必要なPythonパッケージ

## 注意事項

- APIキーは絶対にGitにコミットしないでください
- `.env`ファイルは`.gitignore`に追加することを推奨します
- 環境変数は現在のセッションでのみ有効です。永続的に設定するには、システムの環境変数に追加してください

## トラブルシューティング

### APIキーが設定されていないエラー

```
ValueError: GEMINI_API_KEY環境変数が設定されていません
```

このエラーが発生した場合、上記の方法でAPIキーを正しく設定してください。

### ファイルが見つからないエラー

入力ファイル`input_text.txt`が存在することを確認してください。
