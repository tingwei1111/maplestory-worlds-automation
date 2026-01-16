#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 優化檢查腳本
驗證所有優化項目是否正確實施
"""

import os
import sys
from pathlib import Path
import json
import yaml

def check_file_exists(file_path, description):
    """檢查文件是否存在"""
    if Path(file_path).exists():
        size = Path(file_path).stat().st_size
        if size > 0:
            print(f"✅ {description}: {file_path} ({size} bytes)")
            return True
        else:
            print(f"⚠️ {description}: {file_path} (文件為空)")
            return False
    else:
        print(f"❌ {description}: {file_path} (不存在)")
        return False

def check_config_file():
    """檢查配置文件內容"""
    config_path = "config.yaml"
    if not Path(config_path).exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['model', 'window', 'controls', 'automation', 'safety']
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ 配置文件缺少部分: {missing_sections}")
            return False
        else:
            print("✅ 配置文件結構完整")
            return True
    
    except Exception as e:
        print(f"❌ 配置文件格式錯誤: {e}")
        return False

def check_python_imports():
    """檢查 Python 導入"""
    try:
        import ultralytics
        print("✅ ultralytics 已安裝")
    except ImportError:
        print("❌ ultralytics 未安裝")
        return False
    
    try:
        import cv2
        print("✅ opencv-python 已安裝")
    except ImportError:
        print("❌ opencv-python 未安裝")
        return False
    
    try:
        import pyautogui
        print("✅ pyautogui 已安裝")
    except ImportError:
        print("❌ pyautogui 未安裝")
        return False
    
    try:
        import yaml
        print("✅ PyYAML 已安裝")
    except ImportError:
        print("❌ PyYAML 未安裝")
        return False
    
    return True

def check_auto_py_features():
    """檢查 auto.py 的優化功能"""
    auto_path = "auto.py"
    if not Path(auto_path).exists():
        print("❌ auto.py 不存在")
        return False
    
    with open(auto_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    features = {
        "ConfigManager": "配置管理器",
        "PerformanceMonitor": "性能監控",
        "OptimizedMapleBot": "優化版機器人類",
        "Detection": "偵測數據類",
        "_prioritize_detections": "優先級系統",
        "get_performance_summary": "性能摘要",
        "load_available_models": "模型載入功能"
    }
    
    missing_features = []
    for feature, description in features.items():
        if feature in content:
            print(f"✅ {description}: {feature}")
        else:
            print(f"❌ {description}: {feature} (缺失)")
            missing_features.append(feature)
    
    return len(missing_features) == 0

def check_directory_structure():
    """檢查目錄結構"""
    expected_structure = {
        "weights/": "模型文件目錄",
        "maple/": "監控系統目錄",
        "charts/": "圖表目錄 (可能不存在)",
    }
    
    all_good = True
    
    for dir_path, description in expected_structure.items():
        if Path(dir_path).exists():
            print(f"✅ {description}: {dir_path}")
        else:
            if dir_path == "charts/":
                print(f"⚠️ {description}: {dir_path} (將自動創建)")
            else:
                print(f"❌ {description}: {dir_path} (不存在)")
                all_good = False
    
    return all_good

def main():
    """主檢查函數"""
    print("🔍 MapleStory Worlds 優化系統檢查")
    print("=" * 60)
    
    total_checks = 0
    passed_checks = 0
    
    # 檢查核心文件
    print("\n📄 核心文件檢查:")
    core_files = {
        "auto.py": "優化版自動化腳本",
        "start.py": "快速啟動器",
        "config.yaml": "配置文件",
        "requirements.txt": "依賴清單"
    }
    
    for file_path, description in core_files.items():
        total_checks += 1
        if check_file_exists(file_path, description):
            passed_checks += 1
    
    # 檢查監控系統文件
    print("\n📊 監控系統文件:")
    monitoring_files = {
        "monitoring/monitor.py": "基礎監控",
        "monitoring/monitor_plus.py": "增強監控",
        "monitoring/quick_status.py": "快速狀態",
        "docs/使用說明.md": "更新的使用說明"
    }
    
    for file_path, description in monitoring_files.items():
        total_checks += 1
        if check_file_exists(file_path, description):
            passed_checks += 1
    
    # 檢查模型文件
    print("\n🤖 模型文件:")
    weights_dir = Path("weights")
    if weights_dir.exists():
        model_files = list(weights_dir.glob("*.pt"))
        if model_files:
            for model_file in model_files:
                total_checks += 1
                if check_file_exists(str(model_file), f"模型文件"):
                    passed_checks += 1
        else:
            print("❌ 未找到 .pt 模型文件")
            total_checks += 1
    else:
        print("❌ weights 目錄不存在")
        total_checks += 1
    
    # 檢查目錄結構
    print("\n📁 目錄結構:")
    total_checks += 1
    if check_directory_structure():
        passed_checks += 1
    
    # 檢查配置文件
    print("\n⚙️ 配置文件檢查:")
    total_checks += 1
    if check_config_file():
        passed_checks += 1
    
    # 檢查 Python 導入
    print("\n📦 Python 包檢查:")
    total_checks += 1
    if check_python_imports():
        passed_checks += 1
    
    # 檢查 auto.py 功能
    print("\n🚀 auto.py 功能檢查:")
    total_checks += 1
    if check_auto_py_features():
        passed_checks += 1
    
    # 最終統計
    print("\n" + "=" * 60)
    print("📊 檢查結果統計:")
    print(f"   總檢查項目: {total_checks}")
    print(f"   通過檢查: {passed_checks}")
    print(f"   失敗檢查: {total_checks - passed_checks}")
    print(f"   成功率: {passed_checks/total_checks*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 恭喜！所有優化項目都已正確實施！")
        print("✅ 系統已完全優化，可以開始使用")
        print("\n🚀 下一步:")
        print("   1. 運行 'python start.py' 開始使用")
        print("   2. 選擇系統檢查確認一切正常")
        print("   3. 啟動自動化開始優化體驗")
    
    elif passed_checks / total_checks >= 0.8:
        print("\n✅ 優化基本完成，有少量問題需要解決")
        print("⚠️ 建議檢查失敗的項目並修復")
    
    else:
        print("\n❌ 優化不完整，需要解決多個問題")
        print("🔧 請檢查失敗的項目並重新運行檢查")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
