#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 快速狀態檢查
"""

from monitoring.monitor import MapleStoryMonitor
import datetime

def quick_status():
    monitor = MapleStoryMonitor()
    processes = monitor.find_maple_processes()
    
    print("🍁 MapleStory Worlds 快速狀態檢查")
    print("=" * 60)
    print(f"檢查時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"發現進程: {len(processes)} 個")
    print("-" * 60)
    
    if not processes:
        print("❌ MapleStory Worlds 未在運行")
        return
    
    total_memory = 0
    total_cpu = 0
    main_process = None
    
    for proc in processes:
        info = monitor.get_process_info(proc)
        if 'error' not in info:
            total_memory += info['memory_info']['rss_mb']
            total_cpu += info['cpu_percent']
            
            # 找到主進程 (通常是記憶體使用最大的)
            if info['name'] == 'MapleStory Worlds':
                main_process = info
            
            print(f"🎮 {info['name']} (PID: {info['pid']})")
            print(f"   狀態: {info['status']} | CPU: {info['cpu_percent']:.1f}% | 記憶體: {info['memory_info']['rss_mb']} MB")
            print(f"   運行時間: {monitor.format_running_time(info['running_time'])}")
            print()
    
    print("-" * 60)
    print(f"📊 總計: CPU {total_cpu:.1f}% | 記憶體 {total_memory:.1f} MB")
    
    if main_process:
        print(f"🎯 主進程運行時間: {monitor.format_running_time(main_process['running_time'])}")
        
        # 狀態評估
        if main_process['memory_info']['rss_mb'] > 2000:
            print("⚠️  記憶體使用較高，建議關注")
        if total_cpu > 50:
            print("⚠️  CPU使用率較高，建議關注")
        if main_process['running_time'] > 3600:  # 超過1小時
            hours = int(main_process['running_time'] // 3600)
            print(f"ℹ️  遊戲已運行 {hours} 小時")
    
    print("✅ 狀態檢查完成")

if __name__ == "__main__":
    quick_status() 
