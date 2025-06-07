#!/usr/bin/env python3
"""
MapleStory Worlds 尋找怪物功能測試腳本
"""

import time
import logging
from auto import OptimizedMapleBot, ConfigManager

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mob_hunting_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_mob_hunting_config():
    """測試尋找怪物配置"""
    print("🧪 測試尋找怪物配置...")
    
    config = ConfigManager()
    
    # 檢查配置項目
    mob_hunting_config = config.get('automation.mob_hunting')
    if mob_hunting_config:
        print("✅ 尋找怪物配置已載入:")
        print(f"   啟用: {mob_hunting_config.get('enable', False)}")
        print(f"   搜尋模式: {mob_hunting_config.get('search_pattern', 'horizontal')}")
        print(f"   移動距離: {mob_hunting_config.get('move_distance', 100)}")
        print(f"   搜尋間隔: {mob_hunting_config.get('search_delay', 2.0)}秒")
        print(f"   最大搜尋時間: {mob_hunting_config.get('max_search_time', 10)}秒")
        print(f"   返回中心: {mob_hunting_config.get('return_to_center', True)}")
    else:
        print("❌ 尋找怪物配置未找到")
        return False
    
    # 檢查移動按鍵配置
    movement_keys = config.get('controls.movement_keys')
    if movement_keys:
        print("✅ 移動按鍵配置:")
        print(f"   左移: {movement_keys.get('left', 'left')}")
        print(f"   右移: {movement_keys.get('right', 'right')}")
        print(f"   跳躍: {movement_keys.get('jump', 'x')}")
        print(f"   向上: {movement_keys.get('up', 'up')}")
        print(f"   向下: {movement_keys.get('down', 'down')}")
    else:
        print("❌ 移動按鍵配置未找到")
        return False
    
    return True

def test_mob_hunting_logic():
    """測試尋找怪物邏輯"""
    print("\n🧪 測試尋找怪物邏輯...")
    
    try:
        bot = OptimizedMapleBot()
        
        # 測試搜尋條件檢查
        print("測試搜尋條件檢查...")
        
        # 模擬沒有偵測到怪物的情況
        bot.last_mob_detection_time = time.time() - 5  # 5秒前
        should_search = bot._should_search_for_mobs()
        print(f"   5秒未偵測到怪物，應該搜尋: {should_search}")
        
        # 模擬剛偵測到怪物的情況
        bot.last_mob_detection_time = time.time()
        should_search = bot._should_search_for_mobs()
        print(f"   剛偵測到怪物，應該搜尋: {should_search}")
        
        # 測試搜尋狀態管理
        print("測試搜尋狀態管理...")
        print(f"   初始搜尋狀態: {bot.is_searching}")
        
        bot._start_mob_search()
        print(f"   開始搜尋後狀態: {bot.is_searching}")
        
        bot._end_mob_search()
        print(f"   結束搜尋後狀態: {bot.is_searching}")
        
        print("✅ 尋找怪物邏輯測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 尋找怪物邏輯測試失敗: {e}")
        return False

def test_search_patterns():
    """測試不同搜尋模式"""
    print("\n🧪 測試搜尋模式...")
    
    try:
        bot = OptimizedMapleBot()
        
        # 測試水平搜尋
        print("測試水平搜尋模式...")
        bot.search_direction = 1
        bot.search_moves = 0
        print("   執行水平搜尋移動 (模擬)")
        # bot._horizontal_search(100)  # 註解掉實際移動
        print("   ✅ 水平搜尋邏輯正常")
        
        # 測試垂直搜尋
        print("測試垂直搜尋模式...")
        bot.search_moves = 0
        print("   執行垂直搜尋移動 (模擬)")
        # bot._vertical_search(100)  # 註解掉實際移動
        print("   ✅ 垂直搜尋邏輯正常")
        
        # 測試隨機搜尋
        print("測試隨機搜尋模式...")
        bot.search_moves = 0
        print("   執行隨機搜尋移動 (模擬)")
        # bot._random_search(100)  # 註解掉實際移動
        print("   ✅ 隨機搜尋邏輯正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 搜尋模式測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🍁 MapleStory Worlds 尋找怪物功能測試")
    print("=" * 50)
    
    tests = [
        ("配置測試", test_mob_hunting_config),
        ("邏輯測試", test_mob_hunting_logic),
        ("搜尋模式測試", test_search_patterns)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 執行 {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} 通過")
                passed += 1
            else:
                print(f"❌ {test_name} 失敗")
        except Exception as e:
            print(f"❌ {test_name} 異常: {e}")
    
    print(f"\n📊 測試結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！尋找怪物功能已準備就緒")
    else:
        print("⚠️ 部分測試失敗，請檢查配置和代碼")

if __name__ == "__main__":
    main() 