#!/usr/bin/env python3
"""
MapleStory Worlds 自動化系統 - Python 3.13 啟動器
"""

import os
import sys
import subprocess

def check_venv():
    """檢查虛擬環境是否存在"""
    venv_path = "venv313"
    if not os.path.exists(venv_path):
        print("❌ Python 3.13 虛擬環境不存在")
        print("請先運行以下命令創建環境:")
        print("python3.13 -m venv venv313")
        print("source venv313/bin/activate")
        print("pip install -r requirements.txt")
        return False
    return True

def activate_and_run():
    """激活虛擬環境並運行主程序"""
    if not check_venv():
        return
    
    print("🍁 MapleStory Worlds 自動化系統 - Python 3.13")
    print("=" * 60)
    
    # 激活虛擬環境並運行 start.py
    activate_script = "venv313/bin/activate"
    cmd = f"source {activate_script} && python start.py"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 運行失敗: {e}")
    except KeyboardInterrupt:
        print("\n👋 程序已停止")

if __name__ == "__main__":
    activate_and_run() 