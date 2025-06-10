# 🍁 MapleStory Worlds (Artale) 自動化系統 v2.0

一個功能完整的 MapleStory Worlds 遊戲自動化系統，使用 YOLO 深度學習模型進行智能物件偵測和自動化操作。

## ✨ 主要功能

- 🤖 **智能物件偵測**: 使用 YOLO v8 模型識別遊戲中的怪物、物品、NPC 等
- 🔍 **主動尋找怪物**: 當沒有偵測到怪物時自動移動搜尋
- ⚡ **優先級系統**: 根據配置自動決定行動優先順序
- 🛡️ **安全機制**: 內建多重安全檢查，防止意外操作
- 📊 **性能監控**: 實時 FPS 監控和詳細統計分析
- ⚙️ **配置驅動**: 透過 YAML 配置文件輕鬆調整所有參數
- 🖥️ **多解析度支援**: 支援不同螢幕解析度的預設配置
- 📈 **增強監控**: 實時圖表和智能告警系統

## 🚀 快速開始

### 系統需求

- Python 3.13+ (推薦) 或 Python 3.9+
- macOS (已測試) / Windows / Linux
- 8GB+ RAM
- 支援 CUDA 的 GPU (可選，用於加速)

### 安裝步驟

1. **克隆項目**
   ```bash
   git clone https://github.com/your-username/maplestory-worlds-automation.git
   cd maplestory-worlds-automation
   ```

2. **設置 Python 環境** (推薦使用 Python 3.13)
   ```bash
   python3.13 -m venv venv313
   source venv313/bin/activate  # macOS/Linux
   # 或 venv313\Scripts\activate  # Windows
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

4. **啟動系統**
   ```bash
   # 使用 Python 3.13 (推薦)
   python3.13 start_py313.py
   
   # 或使用其他版本
   python start.py
   ```

## 🎮 使用方法

### 基本操作

1. 運行啟動器後選擇功能：
   - `1` - 系統檢查
   - `2` - 啟動自動化腳本 ⭐
   - `3` - 基礎監控
   - `4` - 增強監控 (推薦)
   - `5` - 快速測試

2. 首次使用建議順序：
   - 系統檢查 → 快速測試 → 啟動自動化

### 🔍 尋找怪物功能

系統支援智能尋找怪物功能：

- **自動觸發**: 當 2 秒內未偵測到怪物時自動開始搜尋
- **多種模式**: 
  - `horizontal` - 水平左右移動 (預設)
  - `vertical` - 垂直跳躍搜尋
  - `random` - 隨機方向搜尋
- **智能返回**: 搜尋後可自動返回原位
- **統計追蹤**: 記錄搜尋次數和效率

## ⚙️ 配置說明

主要配置文件：`config.yaml`

```yaml
# 尋找怪物設定
automation:
  mob_hunting:
    enable: true                    # 啟用/關閉功能
    search_pattern: "horizontal"    # 搜尋模式
    search_delay: 2.0              # 觸發間隔 (秒)
    max_search_time: 10            # 最大搜尋時間 (秒)
    return_to_center: true         # 是否返回原位

# 按鍵設定
controls:
  attack_key: "z"                 # 攻擊鍵
  movement_keys:
    left: "left"                  # 向左移動
    right: "right"                # 向右移動
    jump: "x"                     # 跳躍
```

## 📁 項目結構

```
maplestory-worlds-automation/
├── 📄 auto.py                 # 主要自動化腳本
├── 📄 start.py               # 通用啟動器
├── 📄 start_py313.py         # Python 3.13 專用啟動器
├── 📄 config.yaml            # 主要配置文件
├── 📄 requirements.txt       # 依賴清單
├── 📁 weights/               # YOLO 模型文件
│   ├── best.pt              # 最佳模型
│   └── best.onnx            # ONNX 格式模型
├── 📁 monitoring/            # 監控系統
│   ├── monitor.py           # 基礎監控
│   ├── monitor_plus.py      # 增強監控
│   └── quick_status.py      # 快速狀態檢查
├── 📁 tools/                 # 工具和測試
│   ├── check_optimization.py # 系統檢查
│   ├── test_mob_hunting.py   # 尋找怪物測試
│   └── demo_mob_hunting.py   # 功能演示
├── 📁 docs/                  # 文檔
│   ├── 快速開始指南.md       # 詳細使用指南
│   ├── 使用說明.md           # 完整使用說明
│   └── 監控系統說明.md       # 監控系統文檔
├── 📁 logs/                  # 日誌文件
└── 📁 venv313/              # Python 3.13 虛擬環境
```

## 🛠️ 開發工具

- `tools/check_optimization.py` - 系統完整性檢查
- `tools/test_mob_hunting.py` - 尋找怪物功能測試
- `tools/demo_mob_hunting.py` - 功能演示
- `monitoring/monitor_plus.py` - 增強監控和圖表生成

## 📊 監控功能

### 基礎監控
- 實時 FPS 顯示
- 偵測統計
- 動作執行記錄

### 增強監控
- 實時性能圖表
- 智能告警系統
- 歷史數據分析
- 自動報告生成

## 🔧 故障排除

### 常見問題

1. **模型載入失敗**
   - 確保 `weights/best.pt` 文件存在
   - 檢查 Python 版本和依賴

2. **偵測不準確**
   - 調整 `config.yaml` 中的 `confidence_threshold`
   - 確認遊戲視窗設定正確

3. **角色移動異常**
   - 檢查按鍵配置是否與遊戲設定一致
   - 調整搜尋間隔時間

### 診斷工具

```bash
# 系統檢查
python tools/check_optimization.py

# 功能測試
python tools/test_mob_hunting.py

# 功能演示
python tools/demo_mob_hunting.py
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本項目僅供學習和研究使用。

## ⚠️ 免責聲明

- 本工具僅供教育和研究目的
- 使用者需自行承擔使用風險
- 請遵守遊戲服務條款

---

## 🎯 更新日誌

### v2.0 (最新)
- ✨ 新增主動尋找怪物功能
- 🔧 完全重構代碼架構
- 📊 增強監控系統
- ⚙️ 配置驅動設計
- 🐍 支援 Python 3.13

### v1.0
- 🤖 基礎自動化功能
- 👁️ YOLO 物件偵測
- 📈 基礎監控系統

---

**⭐ 如果這個項目對您有幫助，請給個 Star！** 
