#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試MapleStory Worlds監控功能
"""

from monitoring.monitor import MapleStoryMonitor
import json

def test_monitor():
    print("🧪 測試MapleStory Worlds監控功能")
    print("=" * 50)
    
    # 創建監控實例
    monitor = MapleStoryMonitor()
    
    # 測試1: 尋找進程
    print("1. 尋找MapleStory進程...")
    processes = monitor.find_maple_processes()
    print(f"   發現 {len(processes)} 個相關進程")
    
    if processes:
        print("\n2. 獲取進程詳細信息...")
        for i, proc in enumerate(processes, 1):
            info = monitor.get_process_info(proc)
            if 'error' not in info:
                print(f"   進程 {i}:")
                print(f"     PID: {info['pid']}")
                print(f"     名稱: {info['name']}")
                print(f"     狀態: {info['status']}")
                print(f"     CPU: {info['cpu_percent']:.1f}%")
                print(f"     記憶體: {info['memory_info']['rss_mb']} MB")
                print(f"     運行時間: {monitor.format_running_time(info['running_time'])}")
            else:
                print(f"   進程 {i}: 獲取信息失敗 - {info['error']}")
        
        print("\n3. 測試數據保存...")
        test_data = {
            'timestamp': '2024-test',
            'process_count': len(processes),
            'processes': [monitor.get_process_info(proc) for proc in processes]
        }
        monitor.save_monitoring_data(test_data)
        print("   ✅ 數據保存成功")
        
        print("\n4. 測試摘要報告...")
        report = monitor.get_summary_report()
        if 'error' not in report:
            print("   ✅ 摘要報告生成成功")
            print(f"   總記錄數: {report['total_records']}")
            if 'statistics' in report:
                stats = report['statistics']
                print(f"   平均CPU使用率: {stats['avg_cpu_usage']:.1f}%")
                print(f"   平均記憶體使用: {stats['avg_memory_usage']:.1f} MB")
        else:
            print(f"   ❌ 摘要報告生成失敗: {report['error']}")
    
    else:
        print("   ❌ 未發現MapleStory進程")
        print("   請確保MapleStory Worlds正在運行")
    
    print("\n✅ 測試完成")

if __name__ == "__main__":
    test_monitor() 