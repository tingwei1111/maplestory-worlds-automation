#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 自動化系統快速啟動器
提供直觀的啟動界面和系統檢查功能
版本: 2.0
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import importlib.util

def check_python_version():
    """檢查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        print(f"   當前版本: Python {sys.version}")
        return False
    print(f"✅ Python 版本: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """檢查必要依賴"""
    required_packages = [
        ('ultralytics', 'YOLO 模型支持'),
        ('cv2', 'OpenCV 電腦視覺'),
        ('numpy', '數值計算'),
        ('pyautogui', 'GUI 自動化'),
        ('psutil', '系統監控'),
        ('mss', '螢幕截圖'),
        ('yaml', 'YAML 配置')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if package == 'cv2':
                importlib.import_module('cv2')
            elif package == 'yaml':
                importlib.import_module('yaml')
            else:
                importlib.import_module(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (未安裝)")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """安裝依賴包"""
    print("\n🔧 開始安裝依賴包...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt 文件不存在")
        return False
    
    try:
        # 升級 pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # 安裝依賴
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依賴包安裝完成")
            return True
        else:
            print(f"❌ 安裝失敗: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 安裝過程中發生錯誤: {e}")
        return False

def check_model_files():
    """檢查模型文件"""
    weights_dir = Path("weights")
    
    if not weights_dir.exists():
        print("❌ weights 目錄不存在")
        return False
    
    model_files = list(weights_dir.glob("*.pt"))
    if not model_files:
        print("❌ 未找到 .pt 模型文件")
        return False
    
    print(f"✅ 發現 {len(model_files)} 個模型文件:")
    for model_file in model_files:
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"   - {model_file.name} ({size_mb:.1f} MB)")
    
    return True

def check_config_files():
    """檢查配置文件"""
    config_file = Path("config.yaml")
    
    if config_file.exists():
        print(f"✅ 配置文件: {config_file}")
    else:
        print("⚠️ 配置文件不存在，將使用默認配置")
    
    return True

def check_maple_running():
    """檢查 MapleStory 是否在運行"""
    try:
        import psutil
        
        maple_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if 'maplestory' in proc.info['name'].lower() or 'maple' in proc.info['name'].lower():
                maple_processes.append(proc.info)
        
        if maple_processes:
            print(f"✅ 發現 {len(maple_processes)} 個 MapleStory 進程:")
            for proc in maple_processes:
                print(f"   - PID {proc['pid']}: {proc['name']}")
            return True
        else:
            print("⚠️ 未發現 MapleStory 進程")
            return False
            
    except ImportError:
        print("⚠️ 無法檢查 MapleStory 進程 (psutil 未安裝)")
        return False

def system_check():
    """系統全面檢查"""
    print("🔍 系統檢查中...")
    print("=" * 50)
    
    all_good = True
    
    # Python 版本
    if not check_python_version():
        all_good = False
    
    print()
    
    # 依賴檢查
    print("📦 檢查依賴包:")
    missing = check_dependencies()
    
    if missing:
        all_good = False
        print(f"\n❌ 缺少 {len(missing)} 個依賴包")
        
        install_choice = input("\n是否現在安裝缺少的依賴包? (y/n): ").lower()
        if install_choice == 'y':
            if install_dependencies():
                print("\n✅ 重新檢查依賴...")
                missing = check_dependencies()
                if not missing:
                    all_good = True
    
    print()
    
    # 模型文件
    print("🤖 檢查模型文件:")
    if not check_model_files():
        all_good = False
    
    print()
    
    # 配置文件
    print("⚙️ 檢查配置文件:")
    check_config_files()
    
    print()
    
    # MapleStory 進程
    print("🎮 檢查 MapleStory 進程:")
    check_maple_running()
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("✅ 系統檢查完成，所有必要組件都已就緒！")
    else:
        print("⚠️ 系統檢查發現問題，請解決後再次運行")
    
    return all_good

def show_menu():
    """顯示主選單"""
    print("\n🍁 MapleStory Worlds 自動化系統 v2.0")
    print("=" * 60)
    print("🚀 快速啟動選單:")
    print()
    print("1. 🔍 系統檢查")
    print("2. 🤖 啟動自動化腳本")
    print("3. 📊 啟動監控系統")
    print("4. 📈 啟動增強監控")
    print("5. ⚡ 快速測試")
    print("6. 🔧 安裝依賴")
    print("7. 📁 打開配置文件")
    print("8. 🆘 幫助信息")
    print("9. 🚪 退出")
    print()

def run_script(script_path, description):
    """運行指定腳本"""
    if not Path(script_path).exists():
        print(f"❌ {script_path} 不存在")
        return
    
    print(f"\n🚀 啟動 {description}...")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, script_path])
    except KeyboardInterrupt:
        print(f"\n⏹️ {description} 已停止")
    except Exception as e:
        print(f"❌ 啟動 {description} 時發生錯誤: {e}")

def quick_test():
    """快速測試功能"""
    print("\n🧪 執行快速測試...")
    print("=" * 50)
    
    # 測試模型載入
    try:
        from ultralytics import YOLO
        model_path = "weights/best.pt"
        
        if Path(model_path).exists():
            print("🔄 測試模型載入...")
            model = YOLO(model_path)
            print(f"✅ 模型載入成功: {len(model.names)} 個類別")
            print(f"   類別: {list(model.names.values())}")
        else:
            print("❌ 模型文件不存在")
            
    except Exception as e:
        print(f"❌ 模型測試失敗: {e}")
    
    # 測試螢幕截圖
    try:
        import mss
        import numpy as np
        
        print("🔄 測試螢幕截圖...")
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = np.array(screenshot)
            print(f"✅ 螢幕截圖成功: {img.shape}")
            
    except Exception as e:
        print(f"❌ 螢幕截圖測試失敗: {e}")
    
    # 測試 GUI 自動化
    try:
        import pyautogui
        
        print("🔄 測試 GUI 自動化...")
        x, y = pyautogui.position()
        print(f"✅ 鼠標位置: ({x}, {y})")
        
    except Exception as e:
        print(f"❌ GUI 自動化測試失敗: {e}")
    
    print("\n✅ 快速測試完成")

def open_config():
    """打開配置文件"""
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        print("❌ 配置文件不存在")
        create_choice = input("是否創建默認配置文件? (y/n): ").lower()
        if create_choice == 'y':
            # 這裡可以創建默認配置
            print("✅ 請先運行自動化腳本以創建配置文件")
        return
    
    try:
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['open', str(config_path)])
        elif sys.platform.startswith('win'):   # Windows
            subprocess.run(['notepad', str(config_path)])
        else:  # Linux
            subprocess.run(['xdg-open', str(config_path)])
        
        print(f"✅ 已打開配置文件: {config_path}")
        
    except Exception as e:
        print(f"❌ 無法打開配置文件: {e}")
        print(f"請手動編輯: {config_path}")

def show_help():
    """顯示幫助信息"""
    help_text = """
🆘 MapleStory Worlds 自動化系統幫助

📋 系統要求:
  - Python 3.8+ 
  - MapleStory Worlds 遊戲
  - 訓練好的 YOLO 模型文件 (.pt)

🚀 快速開始:
  1. 確保 MapleStory Worlds 正在運行
  2. 執行系統檢查 (選項 1)
  3. 根據需要安裝依賴 (選項 6)
  4. 啟動自動化腳本 (選項 2)

📁 文件結構:
  - auto.py: 主要自動化腳本
  - config.yaml: 配置文件
  - weights/: YOLO 模型文件
  - maple/: 監控相關腳本
  - requirements.txt: 依賴清單

⚙️ 配置說明:
  - 可通過 config.yaml 調整所有參數
  - 包括按鍵綁定、信賴度閾值、安全設定等
  - 修改後需重新啟動程序生效

🔧 常見問題:
  - 模型載入失敗: 檢查 weights/ 目錄中的 .pt 文件
  - 依賴包錯誤: 運行選項 6 安裝依賴
  - 偵測不準確: 調整 config.yaml 中的信賴度閾值
  - 動作執行錯誤: 檢查遊戲視窗位置和按鍵設定

📞 支援:
  - 檢查日誌文件了解詳細錯誤信息
  - 使用快速測試功能 (選項 5) 診斷問題
    """
    
    print(help_text)

# Conditional import for the GUI part
try:
    from gui import App
    tkinter_available = True
except ImportError:
    tkinter_available = False
except Exception as e: # Catch other potential errors during gui import (like TclError if display not found)
    tkinter_available = False
    print(f"⚠️ 無法導入 GUI 模組 (可能是 gui.py 遺失或 Tkinter 環境問題): {e}")


def main_cli():
    """CLI 主程序"""
    os.system('clear' if os.name == 'posix' else 'cls')
    while True:
        show_menu()
        try:
            choice = input("請選擇功能 (1-9): ").strip()
            if choice == '1':
                system_check()
            elif choice == '2':
                print("提示: 如果您想使用 GUI，請直接運行 'python start.py' 而不加 --cli 參數。")
                run_script("auto.py", "自動化腳本 (CLI 模式)")
            elif choice == '3':
                run_script("maple/monitor.py", "監控系統")
            elif choice == '4':
                run_script("maple/monitor_plus.py", "增強監控系統")
            elif choice == '5':
                quick_test()
            elif choice == '6':
                install_dependencies()
            elif choice == '7':
                open_config()
            elif choice == '8':
                show_help()
            elif choice == '9':
                print("\n👋 再見！")
                break
            else:
                print("❌ 無效選擇，請重新輸入")
                time.sleep(1)

            if choice not in ['9']: # Don't pause on exit
                 input("\n按 Enter 鍵繼續...")
                 os.system('clear' if os.name == 'posix' else 'cls')


        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            input("\n按 Enter 鍵繼續...")


def main_gui():
    """GUI 主程序"""
    print("🚀 正在啟動圖形使用者介面 (GUI)...")
    if not tkinter_available:
        print("❌ Tkinter (GUI 庫) 不可用或 gui.py 遺失。")
        print("   請確保 Tkinter 已安裝 (例如: sudo apt-get install python3-tk) 且 gui.py 在正確的路徑。")
        print("   將嘗試切換到命令列介面 (CLI) 模式。")
        time.sleep(2) # Give user time to read
        return False # Indicate GUI launch failed

    print("🔍 執行 GUI 啟動前的系統檢查...")
    # For GUI, system_check failure might be less critical than for CLI bot run,
    # as user can fix things via UI or see logs.
    # We'll proceed even if system_check() returns False, but print a warning.
    if not system_check():
        print("⚠️ 系統檢查發現一些問題。GUI 仍會嘗試啟動，但某些功能可能無法正常運作。")
        print("   建議檢查上述日誌，並考慮從 CLI 模式運行 '系統檢查' (選項 1) 以獲取詳細信息。")
        if input("   是否繼續啟動 GUI? (y/n, 預設 y): ").lower() == 'n':
            return False # User chose not to proceed with GUI

    try:
        app = App()
        app.mainloop()
        return True # GUI launched and exited normally
    except Exception as e:
        print(f"❌ 啟動 GUI 時發生嚴重錯誤: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        print("   請檢查錯誤訊息。如果問題持續，請嘗試使用命令列介面 (CLI) 模式。")
        return False # Indicate GUI launch failed


def main():
    """程序主入口點"""
    import argparse # Import here to keep it out of global scope if not needed for simple script runs
    parser = argparse.ArgumentParser(description="MapleStory Worlds 自動化系統啟動器。")
    parser.add_argument('--cli', action='store_true', help="以命令列介面 (CLI) 模式運行。")
    args = parser.parse_args()

    if args.cli:
        print("ℹ️ 以命令列介面 (CLI) 模式運行...")
        main_cli()
    else:
        if not main_gui(): # If GUI fails or user opts out
            print("\n🔄 切換到命令列介面 (CLI) 模式...")
            time.sleep(1) # Brief pause
            main_cli()


if __name__ == "__main__":
    main()