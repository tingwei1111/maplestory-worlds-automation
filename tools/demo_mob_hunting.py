#!/usr/bin/env python3
"""
MapleStory Worlds 尋找怪物功能演示
"""

import time
import logging
from auto import OptimizedMapleBot, ConfigManager

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def demo_mob_hunting():
    """演示尋找怪物功能"""
    print("🍁 MapleStory Worlds 尋找怪物功能演示")
    print("=" * 60)
    
    # 載入配置
    config = ConfigManager()
    
    # 顯示當前配置
    print("📋 當前尋找怪物配置:")
    mob_config = config.get('automation.mob_hunting')
    if mob_config:
        print(f"   啟用: {mob_config.get('enable', False)}")
        print(f"   搜尋模式: {mob_config.get('search_pattern', 'horizontal')}")
        print(f"   移動距離: {mob_config.get('move_distance', 100)}")
        print(f"   搜尋間隔: {mob_config.get('search_delay', 2.0)}秒")
        print(f"   最大搜尋時間: {mob_config.get('max_search_time', 10)}秒")
        print(f"   返回中心: {mob_config.get('return_to_center', True)}")
    
    print("\n🎮 移動按鍵配置:")
    movement_keys = config.get('controls.movement_keys')
    if movement_keys:
        print(f"   左移: {movement_keys.get('left', 'left')}")
        print(f"   右移: {movement_keys.get('right', 'right')}")
        print(f"   跳躍: {movement_keys.get('jump', 'x')}")
        print(f"   向上: {movement_keys.get('up', 'up')}")
        print(f"   向下: {movement_keys.get('down', 'down')}")
    
    print("\n" + "=" * 60)
    print("🔍 尋找怪物功能說明:")
    print("1. 當系統偵測不到怪物超過設定時間時，會自動開始搜尋")
    print("2. 根據設定的搜尋模式進行移動:")
    print("   - horizontal: 左右水平移動")
    print("   - vertical: 跳躍和下降移動")
    print("   - random: 隨機方向移動")
    print("3. 一旦偵測到怪物，立即停止搜尋並攻擊")
    print("4. 搜尋結束後可選擇返回原始位置")
    
    print("\n📊 搜尋統計會包含:")
    print("   - 搜尋次數")
    print("   - 總搜尋時間")
    print("   - 平均搜尋時間")
    
    print("\n⚙️ 自訂配置:")
    print("您可以在 config.yaml 中調整以下設定:")
    print("   - search_delay: 調整搜尋觸發間隔")
    print("   - search_pattern: 選擇搜尋模式")
    print("   - max_search_time: 設定最大搜尋時間")
    print("   - return_to_center: 是否返回原位")
    
    print("\n" + "=" * 60)
    print("🚀 要體驗完整功能，請運行:")
    print("   python start.py")
    print("   然後選擇 '2. 啟動自動化腳本'")
    
    print("\n✨ 尋找怪物功能已成功整合到系統中！")

def show_search_patterns():
    """展示不同搜尋模式的說明"""
    print("\n🎯 搜尋模式詳細說明:")
    print("=" * 40)
    
    print("1. 🔄 水平搜尋 (horizontal):")
    print("   - 角色會左右移動尋找怪物")
    print("   - 每移動3次改變方向")
    print("   - 適合平面地圖")
    
    print("\n2. ⬆️ 垂直搜尋 (vertical):")
    print("   - 角色會跳躍和下降尋找怪物")
    print("   - 交替執行跳躍和下降動作")
    print("   - 適合多層地圖")
    
    print("\n3. 🎲 隨機搜尋 (random):")
    print("   - 隨機選擇移動方向")
    print("   - 包含左移、右移、跳躍")
    print("   - 適合複雜地形")

def main():
    """主函數"""
    demo_mob_hunting()
    
    print("\n" + "=" * 60)
    choice = input("是否要查看搜尋模式詳細說明？(y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        show_search_patterns()
    
    print("\n👋 演示結束，感謝使用！")

if __name__ == "__main__":
    main() 