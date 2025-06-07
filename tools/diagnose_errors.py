#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 錯誤診斷腳本
檢查常見問題和提供修復建議
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """測試關鍵模組導入"""
    print("🔍 測試模組導入...")
    
    modules_to_test = [
        ('ultralytics', 'YOLO 模型支持'),
        ('cv2', 'OpenCV 電腦視覺'),
        ('numpy', '數值計算'),
        ('pyautogui', 'GUI 自動化'),
        ('psutil', '系統監控'),
        ('mss', '螢幕截圖'),
        ('yaml', 'YAML 配置'),
        ('matplotlib', '圖表生成'),
        ('pandas', '數據分析')
    ]
    
    failed_imports = []
    
    for module_name, description in modules_to_test:
        try:
            if module_name == 'cv2':
                import cv2
            elif module_name == 'yaml':
                import yaml
            else:
                __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            print(f"❌ {module_name} - {description}: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            print(f"⚠️ {module_name} - {description}: 載入異常 - {e}")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports

def test_auto_py_syntax():
    """測試 auto.py 語法"""
    print("\n🔍 測試 auto.py 語法...")
    
    try:
        with open('auto.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 嘗試編譯代碼
        compile(code, 'auto.py', 'exec')
        print("✅ auto.py 語法正確")
        return True
        
    except SyntaxError as e:
        print(f"❌ auto.py 語法錯誤:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   錯誤: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ auto.py 檢查失敗: {e}")
        return False

def test_start_py_syntax():
    """測試 start.py 語法"""
    print("\n🔍 測試 start.py 語法...")
    
    try:
        with open('start.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'start.py', 'exec')
        print("✅ start.py 語法正確")
        return True
        
    except SyntaxError as e:
        print(f"❌ start.py 語法錯誤:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   錯誤: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ start.py 檢查失敗: {e}")
        return False

def test_config_yaml():
    """測試配置文件"""
    print("\n🔍 測試配置文件...")
    
    try:
        import yaml
        
        if not Path('config.yaml').exists():
            print("⚠️ config.yaml 不存在，將在首次運行時創建")
            return True
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ config.yaml 格式正確")
        return True
        
    except Exception as e:
        print(f"❌ config.yaml 錯誤: {e}")
        return False

def test_model_files():
    """測試模型文件"""
    print("\n🔍 測試模型文件...")
    
    weights_dir = Path('weights')
    if not weights_dir.exists():
        print("❌ weights 目錄不存在")
        return False
    
    model_files = list(weights_dir.glob('*.pt'))
    if not model_files:
        print("❌ 未找到 .pt 模型文件")
        return False
    
    for model_file in model_files:
        try:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            if size_mb < 1:
                print(f"⚠️ {model_file.name} 文件太小 ({size_mb:.1f}MB)")
            else:
                print(f"✅ {model_file.name} ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"❌ {model_file.name} 檢查失敗: {e}")
            return False
    
    return True

def test_yolo_model_load():
    """測試 YOLO 模型載入"""
    print("\n🔍 測試 YOLO 模型載入...")
    
    try:
        from ultralytics import YOLO
        
        model_path = "weights/best.pt"
        if not Path(model_path).exists():
            model_files = list(Path('weights').glob('*.pt'))
            if model_files:
                model_path = str(model_files[0])
            else:
                print("❌ 沒有可用的模型文件")
                return False
        
        print(f"🔄 嘗試載入模型: {model_path}")
        model = YOLO(model_path)
        print(f"✅ 模型載入成功: {len(model.names)} 個類別")
        print(f"   類別: {list(model.names.values())}")
        return True
        
    except Exception as e:
        print(f"❌ 模型載入失敗: {e}")
        traceback.print_exc()
        return False

def provide_fix_suggestions(failed_imports):
    """提供修復建議"""
    print("\n🔧 修復建議:")
    
    if failed_imports:
        print("\n📦 安裝缺少的依賴:")
        print("   pip install -r requirements.txt")
        print("\n或者單獨安裝:")
        
        for module_name, error in failed_imports:
            if module_name == 'cv2':
                print("   pip install opencv-python")
            elif module_name == 'yaml':
                print("   pip install PyYAML")
            else:
                print(f"   pip install {module_name}")
    
    print("\n🚀 其他建議:")
    print("   1. 確保 Python 版本 >= 3.8")
    print("   2. 使用虛擬環境避免依賴衝突")
    print("   3. 檢查網絡連接 (YOLO 首次使用需要下載)")
    print("   4. 重新啟動終端後再試")

def main():
    """主診斷函數"""
    print("🩺 MapleStory Worlds 錯誤診斷")
    print("=" * 50)
    
    all_tests_passed = True
    
    # 測試導入
    failed_imports = test_imports()
    if failed_imports:
        all_tests_passed = False
    
    # 測試語法
    if not test_auto_py_syntax():
        all_tests_passed = False
    
    if not test_start_py_syntax():
        all_tests_passed = False
    
    # 測試配置
    if not test_config_yaml():
        all_tests_passed = False
    
    # 測試模型文件
    if not test_model_files():
        all_tests_passed = False
    
    # 測試模型載入
    if not test_yolo_model_load():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    
    if all_tests_passed:
        print("🎉 所有測試通過！系統應該能正常運行")
        print("✅ 如果仍有問題，請提供具體的錯誤信息")
    else:
        print("❌ 發現問題，請參考修復建議")
        provide_fix_suggestions(failed_imports)
    
    return all_tests_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 診斷被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 診斷過程中發生意外錯誤: {e}")
        traceback.print_exc()
        sys.exit(1) 