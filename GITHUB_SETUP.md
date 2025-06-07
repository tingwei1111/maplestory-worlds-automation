# 🚀 GitHub 上傳指南

## 📋 步驟 1: 在 GitHub 創建新倉庫

1. 前往 [GitHub](https://github.com)
2. 點擊右上角的 "+" 按鈕，選擇 "New repository"
3. 填寫倉庫信息：
   - **Repository name**: `maplestory-worlds-automation`
   - **Description**: `🍁 MapleStory Worlds 自動化系統 - 使用 YOLO 深度學習的智能遊戲自動化工具`
   - **Visibility**: Public (或 Private，根據您的需求)
   - **不要** 勾選 "Add a README file"（我們已經有了）
   - **不要** 勾選 "Add .gitignore"（我們已經有了）
   - **不要** 選擇 License（可以稍後添加）

4. 點擊 "Create repository"

## 📋 步驟 2: 連接本地倉庫到 GitHub

創建倉庫後，GitHub 會顯示設置指令。請在終端中運行：

```bash
# 添加遠程倉庫（替換 YOUR_USERNAME 為您的 GitHub 用戶名）
git remote add origin https://github.com/YOUR_USERNAME/maplestory-worlds-automation.git

# 推送到 GitHub
git push -u origin main
```

## 📋 步驟 3: 驗證上傳

上傳完成後，您應該能在 GitHub 上看到：

- ✅ 完整的項目結構
- ✅ 美觀的 README.md 顯示
- ✅ 所有源代碼文件
- ✅ 文檔和工具目錄
- ✅ 正確的 .gitignore 設置

## 🎯 推薦的後續步驟

1. **添加 Topics**: 在 GitHub 倉庫頁面添加相關標籤
   - `python`
   - `yolo`
   - `automation`
   - `gaming`
   - `computer-vision`
   - `maplestory`

2. **設置 Release**: 創建 v2.0 版本發布

3. **添加 License**: 選擇合適的開源許可證

4. **設置 Issues 模板**: 方便用戶報告問題

## ⚠️ 重要提醒

- 模型文件 (`weights/*.pt`) 由於太大已被排除，用戶需要自行訓練或獲取
- 虛擬環境 (`venv313/`) 已被排除，用戶需要自行設置
- 日誌文件已被排除，避免上傳敏感信息

## 🔧 如果遇到問題

如果推送失敗，可能需要：

1. 設置 Git 用戶信息：
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

2. 如果是私有倉庫，可能需要設置 Personal Access Token

3. 如果有衝突，可能需要先 pull：
```bash
git pull origin main --allow-unrelated-histories
``` 