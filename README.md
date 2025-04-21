# Productivity Tracker (Windows)

🕒 アクティブなウィンドウごとの使用時間を自動で記録し、アプリ別に可視化する Windows 用トラッカーアプリです。

<!-- 任意：スクリーンショットを追加したい場合は以下の行のコメントを外して画像を配置してください -->
<!-- ![screenshot](docs/screenshot.png) -->

---

## 📦 主な機能

- アクティブなアプリをリアルタイムで検出・記録
- 表形式でアプリ名・累積時間・目標時間に対する進捗率を表示
- 棒グラフによるアクティブ時間の可視化（アプリ別）
- 「今日」または「過去7日間」の切り替え
- プルダウンで表示スケール（1h / 3h / 6h / 12h）を選択可能
- グラフはボタンで非表示にでき、ウィンドウをコンパクト化
- アプリ名の表示名や目標時間の編集が可能（GUI対応）
- `.exe` ビルド後はアイコンをダブルクリックするだけで起動可能

---

## 🔧 開発環境での実行方法

```bash
git clone https://github.com/your-username/productivity-tracker.git
cd productivity-tracker
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```
---


## 🛠 PyInstaller による EXE ビルド（手動）
以下のコマンドで .exe をビルドできます：
```bash
pyinstaller --noconsole --windowed --icon=icon.ico --name=productivity_tracker main.py
```

出力ファイルは次の場所に生成されます：
```bash
dist/productivity_tracker/productivity_tracker.exe
```
---

## ☁ GitHub Actions での自動ビルド
このリポジトリには GitHub Actions による Windows 自動ビルドCIが含まれており、 main ブランチに push されると .exe が自動でビルドされ、アーティファクトとしてダウンロード可能になります。  

ワークフローは .github/workflows/build.yml に定義されています。
---

## 📁 ディレクトリ構成
```bash
productivity-tracker/
├── main.py
├── graph.py
├── tracker.py
├── logger.py
├── dialogs.py
├── requirements.txt
├── icon.ico
├── logs/               # 自動生成されるログフォルダ
├── icons/              # アプリ毎のアイコン画像（任意）
├── settings.json       # 記録対象アプリや目標時間などの設定
└── .github/
    └── workflows/
        └── build.yml   # GitHub Actions 用 CI 定義

```