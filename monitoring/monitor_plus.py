#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 增強版監控系統
提供全面的進程監控、系統資源追蹤和智能告警功能
版本: 2.0
"""

import psutil
import time
import json
import logging
import threading
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import deque
import yaml

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maple_monitor_plus.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessInfo:
    """進程信息數據類"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    create_time: datetime
    status: str
    num_threads: int
    num_handles: int = 0  # Windows 特有
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['create_time'] = self.create_time.isoformat()
        return data

@dataclass
class SystemSnapshot:
    """系統快照數據類"""
    timestamp: datetime
    total_processes: int
    maple_processes: List[ProcessInfo]
    system_cpu: float
    system_memory: float
    disk_usage: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_processes': self.total_processes,
            'maple_processes': [p.to_dict() for p in self.maple_processes],
            'system_cpu': self.system_cpu,
            'system_memory': self.system_memory,
            'disk_usage': self.disk_usage
        }

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.alerts = []
    
    def add_snapshot(self, snapshot: SystemSnapshot):
        """添加系統快照"""
        self.history.append(snapshot)
        self._analyze_performance(snapshot)
    
    def _analyze_performance(self, snapshot: SystemSnapshot):
        """分析性能並生成告警"""
        # CPU 使用率告警
        if snapshot.system_cpu > 90:
            self._add_alert("HIGH_CPU", f"系統 CPU 使用率過高: {snapshot.system_cpu:.1f}%")
        
        # 記憶體使用率告警
        if snapshot.system_memory > 85:
            self._add_alert("HIGH_MEMORY", f"系統記憶體使用率過高: {snapshot.system_memory:.1f}%")
        
        # MapleStory 進程告警
        for process in snapshot.maple_processes:
            if process.memory_mb > 2000:  # 超過2GB
                self._add_alert("MAPLE_HIGH_MEMORY", 
                               f"MapleStory 進程 {process.pid} 記憶體使用過高: {process.memory_mb:.1f}MB")
            
            if process.cpu_percent > 50:  # CPU使用率超過50%
                self._add_alert("MAPLE_HIGH_CPU",
                               f"MapleStory 進程 {process.pid} CPU 使用率過高: {process.cpu_percent:.1f}%")
    
    def _add_alert(self, alert_type: str, message: str):
        """添加告警"""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message
        }
        self.alerts.append(alert)
        logger.warning(f"⚠️ {message}")
        
        # 只保留最近100個告警
        if len(self.alerts) > 100:
            self.alerts.pop(0)
    
    def get_performance_summary(self) -> Dict:
        """獲取性能摘要"""
        if not self.history:
            return {}
        
        recent_snapshots = list(self.history)[-60:]  # 最近60個數據點
        
        # CPU 統計
        cpu_values = [s.system_cpu for s in recent_snapshots]
        cpu_avg = sum(cpu_values) / len(cpu_values)
        cpu_max = max(cpu_values)
        
        # 記憶體統計
        memory_values = [s.system_memory for s in recent_snapshots]
        memory_avg = sum(memory_values) / len(memory_values)
        memory_max = max(memory_values)
        
        # MapleStory 統計
        maple_memory_total = []
        maple_cpu_total = []
        
        for snapshot in recent_snapshots:
            if snapshot.maple_processes:
                maple_memory_total.append(sum(p.memory_mb for p in snapshot.maple_processes))
                maple_cpu_total.append(sum(p.cpu_percent for p in snapshot.maple_processes))
        
        return {
            'system': {
                'cpu_avg': cpu_avg,
                'cpu_max': cpu_max,
                'memory_avg': memory_avg,
                'memory_max': memory_max
            },
            'maple': {
                'process_count': len(recent_snapshots[-1].maple_processes) if recent_snapshots else 0,
                'memory_total_avg': sum(maple_memory_total) / len(maple_memory_total) if maple_memory_total else 0,
                'cpu_total_avg': sum(maple_cpu_total) / len(maple_cpu_total) if maple_cpu_total else 0
            },
            'alerts_count': len([a for a in self.alerts if a['timestamp'] > datetime.now() - timedelta(hours=1)])
        }

class EnhancedMapleMonitor:
    """增強版 MapleStory 監控器"""
    
    def __init__(self, config_path: str = "monitor_config.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        self.analyzer = PerformanceAnalyzer()
        self.data_file = Path("maple_monitor_plus_data.json")
        self.chart_dir = Path("charts")
        self.chart_dir.mkdir(exist_ok=True)
        
        # 監控設定
        self.scan_interval = self.config.get('scan_interval', 5)
        self.save_interval = self.config.get('save_interval', 30)
        self.auto_chart = self.config.get('auto_chart', False)
        
        # 信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 背景線程
        self.save_thread = None
        self.chart_thread = None
        
        logger.info("Enhanced MapleStory Monitor 初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """載入配置文件"""
        default_config = {
            'scan_interval': 5,
            'save_interval': 30,
            'auto_chart': False,
            'process_names': ['MapleStory Worlds'],
            'alerts': {
                'cpu_threshold': 90,
                'memory_threshold': 85,
                'maple_memory_threshold': 2000,
                'maple_cpu_threshold': 50
            }
        }
        
        if Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    default_config.update(config)
            except Exception as e:
                logger.error(f"載入配置失敗: {e}")
        
        return default_config
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，正在停止監控...")
        self.stop_monitoring()
        sys.exit(0)
    
    def find_maple_processes(self) -> List[ProcessInfo]:
        """尋找 MapleStory 相關進程"""
        maple_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 
                                           'memory_percent', 'create_time', 'status', 'num_threads']):
                proc_info = proc.info
                
                # 檢查進程名稱
                for target_name in self.config['process_names']:
                    if target_name.lower() in proc_info['name'].lower():
                        try:
                            # 獲取額外信息
                            num_handles = 0
                            if hasattr(proc, 'num_handles'):  # Windows
                                try:
                                    num_handles = proc.num_handles()
                                except:
                                    pass
                            
                            process_info = ProcessInfo(
                                pid=proc_info['pid'],
                                name=proc_info['name'],
                                cpu_percent=proc_info['cpu_percent'] or 0,
                                memory_mb=proc_info['memory_info'].rss / 1024 / 1024,
                                memory_percent=proc_info['memory_percent'] or 0,
                                create_time=datetime.fromtimestamp(proc_info['create_time']),
                                status=proc_info['status'],
                                num_threads=proc_info['num_threads'],
                                num_handles=num_handles
                            )
                            maple_processes.append(process_info)
                            
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                        break
                        
        except Exception as e:
            logger.error(f"掃描進程時發生錯誤: {e}")
        
        return maple_processes
    
    def get_system_info(self) -> Tuple[float, float, float]:
        """獲取系統信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return (cpu_percent, memory.percent, disk.percent)
        except Exception as e:
            logger.error(f"獲取系統信息失敗: {e}")
            return (0, 0, 0)
    
    def create_snapshot(self) -> SystemSnapshot:
        """創建系統快照"""
        maple_processes = self.find_maple_processes()
        system_cpu, system_memory, disk_usage = self.get_system_info()
        total_processes = len(psutil.pids())
        
        return SystemSnapshot(
            timestamp=datetime.now(),
            total_processes=total_processes,
            maple_processes=maple_processes,
            system_cpu=system_cpu,
            system_memory=system_memory,
            disk_usage=disk_usage
        )
    
    def start_monitoring(self):
        """開始監控"""
        if self.running:
            logger.warning("監控已在運行中")
            return
        
        self.running = True
        logger.info("🚀 開始 MapleStory Worlds 增強監控")
        logger.info(f"掃描間隔: {self.scan_interval}秒")
        
        # 啟動背景線程
        self.save_thread = threading.Thread(target=self._auto_save_data, daemon=True)
        self.save_thread.start()
        
        if self.auto_chart:
            self.chart_thread = threading.Thread(target=self._auto_generate_charts, daemon=True)
            self.chart_thread.start()
        
        try:
            while self.running:
                snapshot = self.create_snapshot()
                self.analyzer.add_snapshot(snapshot)
                
                # 顯示實時信息
                if snapshot.maple_processes:
                    total_memory = sum(p.memory_mb for p in snapshot.maple_processes)
                    total_cpu = sum(p.cpu_percent for p in snapshot.maple_processes)
                    
                    logger.info(f"📊 MapleStory: {len(snapshot.maple_processes)} 進程, "
                               f"記憶體: {total_memory:.1f}MB, CPU: {total_cpu:.1f}%")
                else:
                    logger.info("🔍 未發現 MapleStory 進程")
                
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ 使用者中斷監控")
        except Exception as e:
            logger.error(f"監控過程中發生錯誤: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止監控"""
        if not self.running:
            return
        
        self.running = False
        logger.info("正在停止監控...")
        
        # 保存最終數據
        self.save_data()
        
        # 等待背景線程結束
        if self.save_thread and self.save_thread.is_alive():
            self.save_thread.join(timeout=5)
        
        if self.chart_thread and self.chart_thread.is_alive():
            self.chart_thread.join(timeout=5)
        
        logger.info("✅ 監控已停止")
    
    def _auto_save_data(self):
        """自動保存數據"""
        while self.running:
            time.sleep(self.save_interval)
            if self.running:
                self.save_data()
    
    def _auto_generate_charts(self):
        """自動生成圖表"""
        while self.running:
            time.sleep(300)  # 每5分鐘生成一次
            if self.running and len(self.analyzer.history) > 10:
                try:
                    self.generate_performance_chart()
                except Exception as e:
                    logger.error(f"生成圖表失敗: {e}")
    
    def save_data(self):
        """保存監控數據"""
        try:
            data = {
                'last_update': datetime.now().isoformat(),
                'snapshots': [s.to_dict() for s in list(self.analyzer.history)[-100:]],  # 只保存最近100個
                'performance_summary': self.analyzer.get_performance_summary(),
                'alerts': [
                    {
                        'timestamp': a['timestamp'].isoformat(),
                        'type': a['type'],
                        'message': a['message']
                    } for a in self.analyzer.alerts[-50:]  # 最近50個告警
                ]
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"數據已保存到 {self.data_file}")
            
        except Exception as e:
            logger.error(f"保存數據失敗: {e}")
    
    def load_data(self) -> Dict:
        """載入監控數據"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"從 {self.data_file} 載入歷史數據")
                return data
        except Exception as e:
            logger.error(f"載入數據失敗: {e}")
        
        return {}
    
    def generate_performance_chart(self, hours: int = 2) -> str:
        """生成性能圖表"""
        if not self.analyzer.history:
            logger.warning("沒有足夠的數據生成圖表")
            return ""
        
        # 準備數據
        snapshots = list(self.analyzer.history)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [s for s in snapshots if s.timestamp > cutoff_time]
        
        if len(recent_snapshots) < 2:
            logger.warning("沒有足夠的近期數據生成圖表")
            return ""
        
        timestamps = [s.timestamp for s in recent_snapshots]
        system_cpu = [s.system_cpu for s in recent_snapshots]
        system_memory = [s.system_memory for s in recent_snapshots]
        
        # MapleStory 數據
        maple_memory = []
        maple_cpu = []
        
        for snapshot in recent_snapshots:
            if snapshot.maple_processes:
                maple_memory.append(sum(p.memory_mb for p in snapshot.maple_processes))
                maple_cpu.append(sum(p.cpu_percent for p in snapshot.maple_processes))
            else:
                maple_memory.append(0)
                maple_cpu.append(0)
        
        # 創建圖表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('MapleStory Worlds 性能監控', fontsize=16)
        
        # 系統 CPU
        ax1.plot(timestamps, system_cpu, 'b-', linewidth=2, label='系統 CPU')
        ax1.set_title('系統 CPU 使用率 (%)')
        ax1.set_ylabel('CPU %')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # 系統記憶體
        ax2.plot(timestamps, system_memory, 'g-', linewidth=2, label='系統記憶體')
        ax2.set_title('系統記憶體使用率 (%)')
        ax2.set_ylabel('記憶體 %')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # MapleStory 記憶體
        ax3.plot(timestamps, maple_memory, 'r-', linewidth=2, label='MapleStory 記憶體')
        ax3.set_title('MapleStory 記憶體使用量 (MB)')
        ax3.set_ylabel('記憶體 MB')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # MapleStory CPU
        ax4.plot(timestamps, maple_cpu, 'm-', linewidth=2, label='MapleStory CPU')
        ax4.set_title('MapleStory CPU 使用率 (%)')
        ax4.set_ylabel('CPU %')
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # 調整佈局
        plt.tight_layout()
        
        # 保存圖表
        chart_filename = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = self.chart_dir / chart_filename
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 性能圖表已保存: {chart_path}")
        return str(chart_path)
    
    def get_status_report(self) -> str:
        """獲取狀態報告"""
        snapshot = self.create_snapshot()
        summary = self.analyzer.get_performance_summary()
        
        report = []
        report.append("📊 MapleStory Worlds 監控報告")
        report.append("=" * 50)
        report.append(f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # MapleStory 進程信息
        if snapshot.maple_processes:
            report.append(f"🎮 MapleStory 進程: {len(snapshot.maple_processes)} 個")
            total_memory = sum(p.memory_mb for p in snapshot.maple_processes)
            total_cpu = sum(p.cpu_percent for p in snapshot.maple_processes)
            report.append(f"   總記憶體使用: {total_memory:.1f} MB")
            report.append(f"   總 CPU 使用: {total_cpu:.1f}%")
            report.append("")
            
            for i, proc in enumerate(snapshot.maple_processes, 1):
                runtime = datetime.now() - proc.create_time
                report.append(f"   進程 {i}: PID {proc.pid}")
                report.append(f"     記憶體: {proc.memory_mb:.1f} MB ({proc.memory_percent:.1f}%)")
                report.append(f"     CPU: {proc.cpu_percent:.1f}%")
                report.append(f"     運行時間: {str(runtime).split('.')[0]}")
                report.append(f"     狀態: {proc.status}")
                report.append(f"     線程數: {proc.num_threads}")
                if proc.num_handles > 0:
                    report.append(f"     句柄數: {proc.num_handles}")
                report.append("")
        else:
            report.append("❌ 未發現 MapleStory 進程")
            report.append("")
        
        # 系統資源
        report.append("💻 系統資源:")
        report.append(f"   CPU 使用率: {snapshot.system_cpu:.1f}%")
        report.append(f"   記憶體使用率: {snapshot.system_memory:.1f}%")
        report.append(f"   磁盤使用率: {snapshot.disk_usage:.1f}%")
        report.append(f"   總進程數: {snapshot.total_processes}")
        report.append("")
        
        # 性能摘要
        if summary:
            report.append("📈 性能摘要 (最近1小時):")
            if 'system' in summary:
                report.append(f"   系統 CPU 平均: {summary['system']['cpu_avg']:.1f}%")
                report.append(f"   系統 CPU 峰值: {summary['system']['cpu_max']:.1f}%")
                report.append(f"   系統記憶體平均: {summary['system']['memory_avg']:.1f}%")
            
            if 'maple' in summary:
                report.append(f"   MapleStory 記憶體平均: {summary['maple']['memory_total_avg']:.1f}MB")
                report.append(f"   MapleStory CPU 平均: {summary['maple']['cpu_total_avg']:.1f}%")
            
            report.append(f"   告警數量: {summary.get('alerts_count', 0)}")
            report.append("")
        
        # 最近告警
        recent_alerts = [a for a in self.analyzer.alerts if a['timestamp'] > datetime.now() - timedelta(hours=1)]
        if recent_alerts:
            report.append("⚠️ 最近告警:")
            for alert in recent_alerts[-5:]:  # 只顯示最近5個
                report.append(f"   {alert['timestamp'].strftime('%H:%M:%S')} - {alert['message']}")
        else:
            report.append("✅ 暫無告警")
        
        return "\n".join(report)

def main():
    """主程序"""
    print("🍁 MapleStory Worlds 增強監控系統 v2.0")
    print("=" * 60)
    
    monitor = EnhancedMapleMonitor()
    
    # 載入歷史數據
    historical_data = monitor.load_data()
    if historical_data:
        print(f"✅ 載入歷史數據: {len(historical_data.get('snapshots', []))} 個快照")
    
    while True:
        print("\n🎮 功能選單:")
        print("1. 開始實時監控")
        print("2. 查看當前狀態")
        print("3. 生成性能圖表")
        print("4. 查看歷史數據")
        print("5. 導出報告")
        print("6. 退出")
        
        choice = input("\n請選擇功能 (1-6): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            print("\n" + monitor.get_status_report())
            input("\n按 Enter 鍵繼續...")
        elif choice == '3':
            hours = int(input("請輸入要分析的小時數 (預設2): ") or "2")
            chart_path = monitor.generate_performance_chart(hours)
            if chart_path:
                print(f"✅ 圖表已生成: {chart_path}")
        elif choice == '4':
            if historical_data:
                print(f"\n📊 歷史數據摘要:")
                print(f"最後更新: {historical_data.get('last_update', 'N/A')}")
                print(f"數據點數量: {len(historical_data.get('snapshots', []))}")
                print(f"告警數量: {len(historical_data.get('alerts', []))}")
                
                if 'performance_summary' in historical_data:
                    summary = historical_data['performance_summary']
                    print(f"系統 CPU 平均: {summary.get('system', {}).get('cpu_avg', 0):.1f}%")
                    print(f"MapleStory 進程數: {summary.get('maple', {}).get('process_count', 0)}")
            else:
                print("❌ 沒有歷史數據")
            input("\n按 Enter 鍵繼續...")
        elif choice == '5':
            report = monitor.get_status_report()
            report_file = f"maple_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 報告已導出: {report_file}")
        elif choice == '6':
            break
        else:
            print("❌ 無效選擇")
    
    print("👋 再見！")

if __name__ == "__main__":
    main() 