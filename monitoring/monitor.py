#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 背景監控工具
實時監控遊戲進程狀態、資源使用情況和運行時間
"""

import psutil  # type: ignore
import time
import datetime
import json
import os
from typing import Dict, List, Optional

class MapleStoryMonitor:
    def __init__(self):
        self.process_name = "MapleStory Worlds"
        self.log_file = "maple_monitor.log"
        self.data_file = "maple_monitor_data.json"
        self.monitoring = False
        
    def find_maple_processes(self) -> List[psutil.Process]:
        """尋找所有MapleStory相關的進程"""
        maple_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'maple' in proc.info['name'].lower():
                    maple_processes.append(proc)
                elif proc.info['cmdline']:
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    if 'maplestory' in cmdline_str or 'maple' in cmdline_str:
                        maple_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return maple_processes
    
    def get_process_info(self, process: psutil.Process) -> Dict:
        """獲取進程詳細信息"""
        try:
            with process.oneshot():
                info = {
                    'pid': process.pid,
                    'name': process.name(),
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_info': {
                        'rss': process.memory_info().rss,  # 實際記憶體使用
                        'vms': process.memory_info().vms,  # 虛擬記憶體使用
                        'rss_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                        'vms_mb': round(process.memory_info().vms / 1024 / 1024, 2)
                    },
                    'create_time': process.create_time(),
                    'running_time': time.time() - process.create_time(),
                    'num_threads': process.num_threads(),
                    'connections': len(process.connections()) if hasattr(process, 'connections') else 0,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                return info
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return {'error': str(e), 'timestamp': datetime.datetime.now().isoformat()}
    
    def log_message(self, message: str, level: str = "INFO"):
        """記錄日誌訊息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def save_monitoring_data(self, data: Dict):
        """保存監控數據到JSON文件"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        existing_data.append(data)
        
        # 只保留最近1000筆記錄
        if len(existing_data) > 1000:
            existing_data = existing_data[-1000:]
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    def format_running_time(self, seconds: float) -> str:
        """格式化運行時間"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def display_status(self, processes: List[psutil.Process]):
        """顯示當前狀態"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=" * 80)
        print("🍁 MapleStory Worlds 監控面板")
        print("=" * 80)
        print(f"監控時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"發現進程數量: {len(processes)}")
        print("-" * 80)
        
        if not processes:
            print("❌ 未發現MapleStory Worlds進程正在運行")
            return
        
        for i, proc in enumerate(processes, 1):
            info = self.get_process_info(proc)
            if 'error' in info:
                print(f"進程 {i}: 無法獲取信息 - {info['error']}")
                continue
            
            print(f"🎮 進程 {i}:")
            print(f"   PID: {info['pid']}")
            print(f"   名稱: {info['name']}")
            print(f"   狀態: {info['status']}")
            print(f"   CPU使用率: {info['cpu_percent']:.1f}%")
            print(f"   記憶體使用: {info['memory_info']['rss_mb']} MB (實際) / {info['memory_info']['vms_mb']} MB (虛擬)")
            print(f"   執行緒數: {info['num_threads']}")
            print(f"   網路連線數: {info['connections']}")
            print(f"   運行時間: {self.format_running_time(info['running_time'])}")
            print("-" * 40)
    
    def start_monitoring(self, interval: int = 5):
        """開始監控"""
        self.monitoring = True
        self.log_message("開始監控MapleStory Worlds")
        
        try:
            while self.monitoring:
                processes = self.find_maple_processes()
                
                if processes:
                    self.display_status(processes)
                    
                    # 保存監控數據
                    monitoring_data = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'process_count': len(processes),
                        'processes': [self.get_process_info(proc) for proc in processes]
                    }
                    self.save_monitoring_data(monitoring_data)
                    
                    # 檢查異常狀況
                    for proc in processes:
                        info = self.get_process_info(proc)
                        if 'error' not in info:
                            if info['cpu_percent'] > 80:
                                self.log_message(f"警告: 進程 {info['pid']} CPU使用率過高: {info['cpu_percent']:.1f}%", "WARNING")
                            if info['memory_info']['rss_mb'] > 2000:  # 超過2GB
                                self.log_message(f"警告: 進程 {info['pid']} 記憶體使用過高: {info['memory_info']['rss_mb']} MB", "WARNING")
                else:
                    print("❌ MapleStory Worlds 未在運行")
                    self.log_message("MapleStory Worlds 進程未找到", "WARNING")
                
                print(f"\n⏱️  下次更新: {interval}秒後 (按 Ctrl+C 停止監控)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.log_message("監控已停止")
            print("\n✅ 監控已停止")
        except Exception as e:
            self.log_message(f"監控過程中發生錯誤: {str(e)}", "ERROR")
            print(f"\n❌ 發生錯誤: {str(e)}")
    
    def get_summary_report(self) -> Dict:
        """獲取監控摘要報告"""
        if not os.path.exists(self.data_file):
            return {"error": "沒有監控數據"}
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return {"error": "監控數據為空"}
        
        # 計算統計信息
        total_records = len(data)
        latest_record = data[-1]
        
        cpu_usage = []
        memory_usage = []
        
        for record in data:
            for process in record.get('processes', []):
                if 'error' not in process:
                    cpu_usage.append(process.get('cpu_percent', 0))
                    memory_usage.append(process.get('memory_info', {}).get('rss_mb', 0))
        
        summary = {
            'total_records': total_records,
            'monitoring_period': {
                'start': data[0]['timestamp'],
                'end': data[-1]['timestamp']
            },
            'latest_status': latest_record,
            'statistics': {
                'avg_cpu_usage': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                'max_cpu_usage': max(cpu_usage) if cpu_usage else 0,
                'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'max_memory_usage': max(memory_usage) if memory_usage else 0
            }
        }
        
        return summary

def main():
    monitor = MapleStoryMonitor()
    
    print("🍁 MapleStory Worlds 監控工具")
    print("1. 開始實時監控")
    print("2. 查看摘要報告")
    print("3. 檢查當前狀態")
    
    choice = input("\n請選擇功能 (1-3): ").strip()
    
    if choice == '1':
        interval = input("請輸入監控間隔秒數 (預設5秒): ").strip()
        interval = int(interval) if interval.isdigit() else 5
        monitor.start_monitoring(interval)
    
    elif choice == '2':
        report = monitor.get_summary_report()
        print("\n📊 監控摘要報告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    elif choice == '3':
        processes = monitor.find_maple_processes()
        monitor.display_status(processes)
    
    else:
        print("無效選擇")

if __name__ == "__main__":
    main() 
