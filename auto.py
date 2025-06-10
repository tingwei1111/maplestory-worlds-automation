#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 優化自動化系統
使用 YOLO 模型進行智能物件偵測和自動化操作
版本: 2.0
作者: AI Assistant
"""

import os
import sys
import time
import logging # Standard library import
import yaml
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# --- Logging Configuration (early for use by other imports) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__) # logger is now defined

# --- Optional PyAutoGUI Import ---
try:
    import pyautogui
    # Configure pyautogui ONLY if display is available
    if 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ:
        # Assuming safety.enable_failsafe from config would be True by default
        # and pyautogui.PAUSE = 0.05 are desired defaults.
        # These might need to be set later if they depend on ConfigManager.
        # For now, only basic import is attempted.
        # pyautogui.FAILSAFE = True # This would be set in OptimizedMapleBot init based on config
        # pyautogui.PAUSE = 0.05    # This would be set in OptimizedMapleBot init
        logger.info("PyAutoGUI imported. Configuration will be handled by OptimizedMapleBot.")
    else:
        logger.warning("No DISPLAY or WAYLAND_DISPLAY found. PyAutoGUI imported but may not function for screen interactions.")
except ImportError:
    logger.warning("PyAutoGUI not found. GUI automation features will be disabled.")
    pyautogui = None # Define pyautogui as None if import fails
except Exception as e:
    logger.warning(f"Error importing PyAutoGUI: {e}. GUI automation features will be disabled.")
    pyautogui = None

# --- Other Core Imports ---
import cv2 # Ensure cv2 is imported
import mss
import numpy as np
from ultralytics import YOLO # Moved here as it's a major dependency

# --- Start of Script Classes ---
@dataclass
class Detection:
    """偵測結果數據類"""
    bbox: List[int]
    confidence: float
    class_id: int
    class_name: str
    center: Tuple[int, int]
    distance_from_center: float = 0.0

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """載入配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"配置文件 {self.config_path} 不存在，使用默認配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """獲取默認配置"""
        return {
            'model': {
                'default_path': 'weights/best.pt',
                'confidence_threshold': 0.6,
                'iou_threshold': 0.45
            },
            'window': {
                'default': {'left': 100, 'top': 100, 'width': 1200, 'height': 800}
            },
            'controls': {
                'pickup_key': 'z',
                'interact_key': 'space',
                'attack_method': 'click'
            },
            'automation': {
                'action_delay': 0.3,
                'scan_interval': 0.1,
                'max_detection_distance': 200,
                'priority_targets': ['item', 'mob', 'npc']
            },
            'safety': {
                'enable_failsafe': True,
                'max_runtime_hours': 2
            },
            'performance': { # Added performance section
                'capture_width': None,
                'capture_height': None,
                'model_inference_size': None # Added model_inference_size
            }
        }
    
    def get(self, key_path: str, default=None):
        """獲取配置值，支持點分割路徑如 'model.confidence_threshold'"""
        try:
            keys = key_path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self):
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        self.detection_times = []
        
    def update_fps(self):
        """更新 FPS 計數"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def record_detection_time(self, detection_time: float):
        """記錄偵測時間"""
        self.detection_times.append(detection_time)
        if len(self.detection_times) > 100:  # 只保留最近100次
            self.detection_times.pop(0)
    
    def get_avg_detection_time(self) -> float:
        """獲取平均偵測時間"""
        return sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0

class OptimizedMapleBot:
    """優化版 MapleStory 自動化機器人"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = ConfigManager(config_path)
        self.model = None
        self.running = False
        self.paused = False
        self.start_time = None
        self.performance_monitor = PerformanceMonitor()
        
        # 從配置載入設定
        self.monitor = self.config.get('window.default')
        self.confidence_threshold = self.config.get('model.confidence_threshold', 0.6)
        self.action_delay = self.config.get('automation.action_delay', 0.3)
        self.scan_interval = self.config.get('automation.scan_interval', 0.1)
        self.max_runtime = self.config.get('safety.max_runtime_hours', 2) * 3600

        # Load performance settings
        self.capture_width = self.config.get('performance.capture_width')
        self.capture_height = self.config.get('performance.capture_height')
        self.model_inference_size = self.config.get('performance.model_inference_size')
        
        # 統計數據
        self.stats = {
            'detections': 0,
            'actions_performed': 0,
            'items_collected': 0,
            'mobs_attacked': 0,
            'npcs_interacted': 0,
            'searches_performed': 0,
            'search_time_total': 0
        }
        
        # 尋找怪物相關變數
        self.last_mob_detection_time = time.time()
        self.is_searching = False
        self.search_start_time = 0
        self.original_position = None
        self.search_direction = 1  # 1 for right, -1 for left
        self.search_moves = 0
        
        # PyAutoGUI setup is moved to the global import block
        
        logger.info("OptimizedMapleBot 初始化完成")
        self._load_model()
    
    def _load_model(self):
        """載入 YOLO 模型"""
        model_path = self.config.get('model.default_path')
        if not model_path or not os.path.exists(model_path):
            logger.error(f"模型文件不存在: {model_path}")
            return False
        
        try:
            logger.info(f"載入模型: {model_path}")
            self.model = YOLO(model_path)
            self.model.conf = self.confidence_threshold
            self.model.iou = self.config.get('model.iou_threshold', 0.45)
            
            logger.info("✅ 模型載入成功!")
            logger.info(f"📊 模型類別: {self.model.names}")
            return True
            
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            return False
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """優化的螢幕擷取"""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(self.monitor)
                img = np.array(screenshot)

                # Resize if capture dimensions are specified
                if self.capture_width and self.capture_height:
                    try:
                        img = cv2.resize(img, (self.capture_width, self.capture_height), interpolation=cv2.INTER_AREA)
                    except Exception as resize_e:
                        logger.error(f"螢幕截圖縮放失敗: {resize_e}")
                        # Proceed with original image if resize fails

                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        except Exception as e:
            logger.error(f"螢幕擷取失敗: {e}")
            return None
    
    def detect_objects(self, img: np.ndarray) -> List[Detection]:
        """優化的物件偵測"""
        if self.model is None:
            return []
        
        start_time = time.time()
        
        try:
            if self.model_inference_size:
                results = self.model(img, imgsz=self.model_inference_size, verbose=False)
            else:
                results = self.model(img, verbose=False)
            detections = []
            
            # 計算畫面中心點
            center_x, center_y = self.monitor['width'] // 2, self.monitor['height'] // 2
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = box.cls[0].cpu().numpy()
                        
                        if conf > self.confidence_threshold:
                            detection_center = (int((xyxy[0] + xyxy[2]) / 2), int((xyxy[1] + xyxy[3]) / 2))
                            
                            # 計算距離中心點的距離
                            distance = np.sqrt((detection_center[0] - center_x)**2 + (detection_center[1] - center_y)**2)
                            
                            detection = Detection(
                                bbox=[int(x) for x in xyxy],
                                confidence=float(conf),
                                class_id=int(cls),
                                class_name=self.model.names[int(cls)],
                                center=detection_center,
                                distance_from_center=distance
                            )
                            detections.append(detection)
            
            # 按優先級和距離排序
            detections = self._prioritize_detections(detections)
            
            # 記錄統計
            self.stats['detections'] += len(detections)
            detection_time = time.time() - start_time
            self.performance_monitor.record_detection_time(detection_time)
            
            return detections
            
        except Exception as e:
            logger.error(f"物件偵測失敗: {e}")
            return []
    
    def _prioritize_detections(self, detections: List[Detection]) -> List[Detection]:
        """按優先級和距離排序偵測結果"""
        priority_map = {name: i for i, name in enumerate(self.config.get('automation.priority_targets', []))}
        
        def sort_key(detection):
            priority = priority_map.get(detection.class_name, 999)
            return (priority, detection.distance_from_center)
        
        return sorted(detections, key=sort_key)
    
    def perform_action(self, detection: Detection) -> bool:
        """執行優化的遊戲動作"""
        class_name = detection.class_name
        abs_x = self.monitor['left'] + detection.center[0]
        abs_y = self.monitor['top'] + detection.center[1]
        
        # 檢查距離限制
        max_distance = self.config.get(f'detection_behavior.{class_name}.max_distance', 200)
        if detection.distance_from_center > max_distance:
            return False
        
        try:
            action_performed = False
            
            if class_name == 'mob':
                # 檢查是否啟用攻擊動作
                mob_action = self.config.get('detection_behavior.mob.action', 'attack')
                if mob_action == 'attack':
                    if pyautogui: # Check if pyautogui was imported successfully
                        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
                        attack_method = self.config.get('controls.attack_method', 'click')
                        if attack_method == 'key':
                            attack_key = self.config.get('controls.attack_key', 'z')
                            pyautogui.press(attack_key)
                        else:
                            pyautogui.click()
                        logger.info(f"⚔️ 攻擊怪物 (信賴度: {detection.confidence:.2f})")
                        self.stats['mobs_attacked'] += 1
                        action_performed = True
                        time.sleep(self.config.get('detection_behavior.mob.attack_delay', 0.5))
                    else:
                        logger.warning("PyAutoGUI not available, cannot perform attack.")
                else:
                    logger.info(f"👁️ 偵測到怪物 (信賴度: {detection.confidence:.2f}) - 僅記錄")
                
            elif class_name == 'item':
                # 只偵測物品，不執行動作
                logger.info(f"👁️ 偵測到物品 (信賴度: {detection.confidence:.2f}) - 僅記錄")
                
            elif class_name == 'npc':
                # 只偵測 NPC，不執行動作
                logger.info(f"👁️ 偵測到 NPC (信賴度: {detection.confidence:.2f}) - 僅記錄")
            
            if action_performed:
                self.stats['actions_performed'] += 1
                return True
                
        except Exception as e:
            logger.error(f"執行動作失敗: {e}")
        
        return False
    
    def _should_search_for_mobs(self) -> bool:
        """檢查是否應該開始尋找怪物"""
        if not self.config.get('automation.mob_hunting.enable', True):
            return False
        
        # 如果正在搜尋中，不重複開始
        if self.is_searching:
            return False
        
        # 檢查距離上次偵測到怪物的時間
        search_delay = self.config.get('automation.mob_hunting.search_delay', 2.0)
        time_since_last_mob = time.time() - self.last_mob_detection_time
        
        return time_since_last_mob > search_delay
    
    def _start_mob_search(self):
        """開始尋找怪物"""
        if self.is_searching:
            return
        
        self.is_searching = True
        self.search_start_time = time.time()
        self.search_moves = 0
        
        # 記錄當前位置（假設角色在畫面中心）
        self.original_position = (self.monitor['width'] // 2, self.monitor['height'] // 2)
        
        logger.info("🔍 開始尋找怪物...")
    
    def _perform_mob_search(self):
        """執行尋找怪物的移動"""
        if not self.is_searching:
            return
        
        max_search_time = self.config.get('automation.mob_hunting.max_search_time', 10)
        if time.time() - self.search_start_time > max_search_time:
            self._end_mob_search()
            return
        
        search_pattern = self.config.get('automation.mob_hunting.search_pattern', 'horizontal')
        move_distance = self.config.get('automation.mob_hunting.move_distance', 100)
        
        try:
            if search_pattern == 'horizontal':
                self._horizontal_search(move_distance)
            elif search_pattern == 'vertical':
                self._vertical_search(move_distance)
            elif search_pattern == 'random':
                self._random_search(move_distance)
            
            time.sleep(0.5)  # 移動後稍作停頓
            
        except Exception as e:
            logger.error(f"搜尋移動失敗: {e}")
            self._end_mob_search()
    
    def _horizontal_search(self, move_distance: int):
        """水平搜尋移動"""
        move_key = self.config.get('controls.movement_keys.right' if self.search_direction > 0 else 'controls.movement_keys.left', 'right' if self.search_direction > 0 else 'left')
        
        if pyautogui: # Check if pyautogui was imported successfully
            # 按住移動鍵一段時間
            pyautogui.keyDown(move_key)
            time.sleep(0.3)
            pyautogui.keyUp(move_key)
        else:
            logger.warning("PyAutoGUI not available, cannot perform horizontal search movement.")
        
        self.search_moves += 1
        
        # 每移動3次改變方向
        if self.search_moves >= 3:
            self.search_direction *= -1
            self.search_moves = 0
            logger.info(f"🔄 改變搜尋方向: {'右' if self.search_direction > 0 else '左'}")
    
    def _vertical_search(self, move_distance: int):
        """垂直搜尋移動（跳躍和下降）"""
        if pyautogui: # Check if pyautogui was imported successfully
            if self.search_moves % 2 == 0:
                # 跳躍
                jump_key = self.config.get('controls.movement_keys.jump', 'x')
                pyautogui.press(jump_key)
                logger.info("⬆️ 跳躍搜尋")
            else:
                # 向下移動
                down_key = self.config.get('controls.movement_keys.down', 'down')
                pyautogui.keyDown(down_key)
                time.sleep(0.2)
                pyautogui.keyUp(down_key)
                logger.info("⬇️ 向下搜尋")
        else:
            logger.warning("PyAutoGUI not available, cannot perform vertical search movement.")
        
        self.search_moves += 1
    
    def _random_search(self, move_distance: int):
        """隨機搜尋移動"""
        import random
        
        movements = ['left', 'right', 'jump']
        chosen_movement = random.choice(movements)
        
        if pyautogui: # Check if pyautogui was imported successfully
            if chosen_movement == 'jump':
                jump_key = self.config.get('controls.movement_keys.jump', 'x')
                pyautogui.press(jump_key)
                logger.info("🎲 隨機跳躍")
            else:
                move_key = self.config.get(f'controls.movement_keys.{chosen_movement}', chosen_movement)
                pyautogui.keyDown(move_key)
                time.sleep(0.3)
                pyautogui.keyUp(move_key)
                logger.info(f"🎲 隨機移動: {chosen_movement}")
        else:
            logger.warning("PyAutoGUI not available, cannot perform random search movement.")
        
        self.search_moves += 1
    
    def _end_mob_search(self):
        """結束尋找怪物"""
        if not self.is_searching:
            return
        
        # 記錄搜尋統計
        search_duration = time.time() - self.search_start_time
        self.stats['searches_performed'] += 1
        self.stats['search_time_total'] += search_duration
        
        self.is_searching = False
        logger.info(f"🏁 結束怪物搜尋 (耗時: {search_duration:.1f}秒)")
        
        # 如果設定要返回中心，執行返回動作
        if self.config.get('automation.mob_hunting.return_to_center', True):
            self._return_to_center()
    
    def _return_to_center(self):
        """返回到搜尋開始的位置"""
        try:
            logger.info("🏠 返回原始位置...")
            # 簡單的返回邏輯：向相反方向移動
            if pyautogui: # Check if pyautogui was imported successfully
                if self.search_direction > 0:
                    # 如果最後是向右移動，現在向左移動
                    move_key = self.config.get('controls.movement_keys.left', 'left')
                else:
                    # 如果最後是向左移動，現在向右移動
                    move_key = self.config.get('controls.movement_keys.right', 'right')

                pyautogui.keyDown(move_key)
                time.sleep(0.5)  # 移動時間稍長一些
                pyautogui.keyUp(move_key)
            else:
                logger.warning("PyAutoGUI not available, cannot perform return to center movement.")
            
        except Exception as e:
            logger.error(f"返回中心失敗: {e}")
    
    def _check_safety_conditions(self) -> bool:
        """檢查安全條件"""
        if self.start_time and time.time() - self.start_time > self.max_runtime:
            logger.warning("達到最大運行時間限制")
            return False
        return True
    
    def start_automation(self, show_preview: bool = False):
        """開始優化的自動化流程"""
        if self.model is None:
            logger.error("模型未載入，無法開始自動化")
            return
        
        self.running = True
        self.start_time = time.time()
        logger.info("🚀 開始 MapleStory Worlds 優化自動化")
        logger.info("按 'q' 鍵暫停/恢復，'Esc' 鍵停止")
        
        last_stats_time = time.time()
        
        try:
            while self.running:
                if not self._check_safety_conditions():
                    break
                
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # 擷取和偵測
                img = self.capture_screen()
                if img is None:
                    continue
                
                detections = self.detect_objects(img)
                
                # 檢查是否偵測到怪物，更新最後偵測時間
                mob_detected = any(d.class_name == 'mob' for d in detections)
                if mob_detected:
                    self.last_mob_detection_time = time.time()
                    # 如果正在搜尋中且偵測到怪物，停止搜尋
                    if self.is_searching:
                        self._end_mob_search()
                
                # 執行動作
                actions_this_cycle = 0
                for detection in detections:
                    if not self.running or self.paused:
                        break
                    
                    if self.perform_action(detection):
                        actions_this_cycle += 1
                        if actions_this_cycle >= 3:  # 限制每週期最多執行3個動作
                            break
                        time.sleep(self.action_delay)
                
                # 如果沒有偵測到怪物且不在搜尋中，檢查是否需要開始搜尋
                if not mob_detected and self._should_search_for_mobs():
                    self._start_mob_search()
                
                # 如果正在搜尋中，執行搜尋移動
                if self.is_searching:
                    self._perform_mob_search()
                
                # 顯示預覽
                if show_preview and detections:
                    preview_img = self._draw_detections(img.copy(), detections)
                    cv2.imshow('MapleStory Auto Bot - 按 q 暫停/恢復', preview_img)
                
                # 更新性能監控
                self.performance_monitor.update_fps()
                
                # 定期顯示統計
                if time.time() - last_stats_time >= 30:  # 每30秒顯示一次
                    self._log_statistics()
                    last_stats_time = time.time()
                
                # 檢查按鍵
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.paused = not self.paused
                    logger.info(f"{'⏸️ 暫停' if self.paused else '▶️ 恢復'}自動化")
                elif key == 27:  # Esc
                    break
                
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ 使用者中斷自動化")
        except Exception as e:
            logger.error(f"自動化過程中發生錯誤: {e}")
        finally:
            self.running = False
            cv2.destroyAllWindows()
            self._log_final_statistics()
            logger.info("✅ 自動化已停止")
    
    def _draw_detections(self, img: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """繪製偵測結果"""
        for detection in detections:
            bbox = detection.bbox
            class_name = detection.class_name
            confidence = detection.confidence
            
            # 根據類型設定顏色
            color_map = {
                'mob': (0, 0, 255),      # 紅色
                'item': (0, 255, 0),     # 綠色
                'npc': (255, 0, 0),      # 藍色
                'character': (255, 255, 0), # 青色
                'environment': (128, 128, 128), # 灰色
                'ui': (255, 0, 255)      # 洋紅色
            }
            color = color_map.get(class_name, (255, 255, 255))
            
            # 繪製邊界框
            cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # 繪製標籤
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(img, label, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 繪製性能信息
        fps_text = f"FPS: {self.performance_monitor.current_fps}"
        cv2.putText(img, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return img
    
    def _log_statistics(self):
        """記錄統計信息"""
        runtime = time.time() - self.start_time if self.start_time else 0
        avg_detection_time = self.performance_monitor.get_avg_detection_time()
        
        logger.info("📊 運行統計:")
        logger.info(f"   運行時間: {runtime/60:.1f} 分鐘")
        logger.info(f"   FPS: {self.performance_monitor.current_fps}")
        logger.info(f"   平均偵測時間: {avg_detection_time*1000:.1f}ms")
        logger.info(f"   總偵測次數: {self.stats['detections']}")
        logger.info(f"   執行動作: {self.stats['actions_performed']}")
        logger.info(f"   撿取物品: {self.stats['items_collected']}")
        logger.info(f"   攻擊怪物: {self.stats['mobs_attacked']}")
        logger.info(f"   NPC互動: {self.stats['npcs_interacted']}")
        logger.info(f"   搜尋次數: {self.stats['searches_performed']}")
        if self.stats['searches_performed'] > 0:
            avg_search_time = self.stats['search_time_total'] / self.stats['searches_performed']
            logger.info(f"   平均搜尋時間: {avg_search_time:.1f}秒")
    
    def _log_final_statistics(self):
        """記錄最終統計"""
        logger.info("🎯 最終統計報告:")
        self._log_statistics()
    
    def get_performance_summary(self) -> Dict:
        """獲取性能摘要"""
        runtime = time.time() - self.start_time if self.start_time else 0
        avg_detection_time = self.performance_monitor.get_avg_detection_time()
        
        return {
            'runtime_minutes': runtime / 60,
            'current_fps': self.performance_monitor.current_fps,
            'avg_detection_time_ms': avg_detection_time * 1000,
            'total_detections': self.stats['detections'],
            'actions_performed': self.stats['actions_performed'],
            'items_collected': self.stats['items_collected'],
            'mobs_attacked': self.stats['mobs_attacked'],
            'npcs_interacted': self.stats['npcs_interacted'],
            'searches_performed': self.stats['searches_performed'],
            'avg_search_time': self.stats['search_time_total'] / max(1, self.stats['searches_performed'])
        }
    
    def test_detection(self):
        """測試偵測功能"""
        if self.model is None:
            logger.error("模型未載入")
            return
        
        logger.info("🧪 測試物件偵測功能")
        img = self.capture_screen()
        if img is None:
            logger.error("無法擷取畫面")
            return
        
        detections = self.detect_objects(img)
        logger.info(f"📊 偵測結果: 發現 {len(detections)} 個物件")
        
        for i, detection in enumerate(detections, 1):
            logger.info(f"  {i}. {detection.class_name} (信賴度: {detection.confidence:.2f}, 距離: {detection.distance_from_center:.0f}px)")
        
        if detections:
            result_img = self._draw_detections(img, detections)
            cv2.imshow('Detection Test', result_img)
            logger.info("按任意鍵關閉預覽視窗")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            logger.info("未偵測到任何物件")

def load_available_models() -> Dict[str, str]:
    """載入可用的模型文件"""
    models = {}
    weights_dir = Path("weights")
    
    if weights_dir.exists():
        for i, model_file in enumerate(weights_dir.glob("*.pt"), 1):
            size_mb = model_file.stat().st_size / (1024 * 1024)
            models[str(i)] = str(model_file)
            print(f"  {i}. {model_file} ({size_mb:.1f} MB)")
    
    return models

def main():
    """主程序"""
    print("🍁 MapleStory Worlds 優化自動化系統 v2.0")
    print("=" * 60)
    
    # 檢查配置文件
    if not os.path.exists("config.yaml"):
        logger.warning("配置文件不存在，將使用默認設定")
    
    # 顯示可用模型
    print("可用的模型文件:")
    models = load_available_models()
    
    if not models:
        logger.error("未找到任何模型文件")
        return
    
    # 選擇模型
    choice = input(f"\n請選擇模型文件 (1-{len(models)}, 預設1): ").strip()
    if choice not in models:
        choice = '1'
    
    model_path = models[choice]
    if not os.path.exists(model_path):
        logger.error(f"選擇的模型文件不存在: {model_path}")
        return
    
    # 創建配置並設定模型路徑
    config = ConfigManager()
    config.config['model']['default_path'] = model_path
    
    # 創建機器人
    bot = OptimizedMapleBot()
    
    # 主選單
    while True:
        print("\n🎮 功能選單:")
        print("1. 測試物件偵測")
        print("2. 開始自動化 (有預覽)")
        print("3. 開始自動化 (無預覽)")
        print("4. 調整視窗設定")
        print("5. 查看配置")
        print("6. 查看統計")
        print("7. 退出")
        
        choice = input("\n請選擇功能 (1-7): ").strip()
        
        if choice == '1':
            bot.test_detection()
        elif choice == '2':
            bot.start_automation(show_preview=True)
        elif choice == '3':
            bot.start_automation(show_preview=False)
        elif choice == '4':
            _adjust_window_settings(bot)
        elif choice == '5':
            _show_config(bot.config)
        elif choice == '6':
            bot._log_statistics()
        elif choice == '7':
            break
        else:
            print("❌ 無效選擇")
    
    print("👋 再見！")

def _adjust_window_settings(bot):
    """調整視窗設定"""
    print(f"\n當前視窗設定:")
    print(f"  左上角: ({bot.monitor['left']}, {bot.monitor['top']})")
    print(f"  大小: {bot.monitor['width']} x {bot.monitor['height']}")
    
    # 提供預設選項
    print("\n預設選項:")
    print("1. Full HD (1920x1080)")
    print("2. QHD (2560x1440)")
    print("3. 自訂設定")
    
    preset_choice = input("選擇預設或自訂 (1-3): ").strip()
    
    if preset_choice == '1':
        bot.monitor = {'left': 0, 'top': 100, 'width': 1920, 'height': 980}
    elif preset_choice == '2':
        bot.monitor = {'left': 320, 'top': 180, 'width': 1280, 'height': 720}
    elif preset_choice == '3':
        try:
            bot.monitor['left'] = int(input("請輸入左側位置: ") or bot.monitor['left'])
            bot.monitor['top'] = int(input("請輸入頂部位置: ") or bot.monitor['top'])
            bot.monitor['width'] = int(input("請輸入寬度: ") or bot.monitor['width'])
            bot.monitor['height'] = int(input("請輸入高度: ") or bot.monitor['height'])
        except ValueError:
            print("❌ 輸入格式錯誤")
            return
    
    print("✅ 視窗設定已更新")

def _show_config(config: ConfigManager):
    """顯示當前配置"""
    print("\n⚙️ 當前配置:")
    print(f"  模型路徑: {config.get('model.default_path')}")
    print(f"  信賴度閾值: {config.get('model.confidence_threshold')}")
    print(f"  動作延遲: {config.get('automation.action_delay')}秒")
    print(f"  掃描間隔: {config.get('automation.scan_interval')}秒")
    print(f"  最大運行時間: {config.get('safety.max_runtime_hours')}小時")
    print(f"  撿取鍵: {config.get('controls.pickup_key')}")
    print(f"  互動鍵: {config.get('controls.interact_key')}")

if __name__ == "__main__":
    # --- Start of modification for direct profiling ---
    logger.info("Attempting direct call to test_detection for profiling.")

    # Find model
    model_path_to_use = None
    weights_dir = Path("weights")
    preferred_model_path = weights_dir / "best.pt"

    if preferred_model_path.exists():
        model_path_to_use = str(preferred_model_path)
        logger.info(f"Using preferred model: {model_path_to_use}")
    else:
        logger.warning(f"Preferred model {preferred_model_path} not found. Searching for other .pt files...")
        pt_files = list(weights_dir.glob("*.pt"))
        if pt_files:
            model_path_to_use = str(pt_files[0])
            logger.info(f"Found alternative model: {model_path_to_use}")
        else:
            logger.error("No .pt model files found in the 'weights' directory.")
            sys.stderr.write("Error: No model file found in weights/. Exiting.\n")
            sys.exit(1) # Exit if no model is found

    # Ensure config reflects the chosen model
    # We need to write this to config.yaml so OptimizedMapleBot picks it up
    # as it creates its own ConfigManager instance.
    temp_config_manager = ConfigManager() # Loads existing or default
    temp_config_manager.config['model']['default_path'] = model_path_to_use

    try:
        with open(temp_config_manager.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(temp_config_manager.config, f)
        logger.info(f"Temporarily updated {temp_config_manager.config_path} with model path: {model_path_to_use}")
    except Exception as e:
        logger.error(f"Failed to write temporary config: {e}")
        sys.stderr.write(f"Error: Failed to write temporary config for model path. Exiting.\n")
        sys.exit(1)

    # Instantiate the bot - it will load the updated config.yaml
    bot = OptimizedMapleBot() # Uses its own ConfigManager, which loads from config.yaml

    if bot.model is None:
        # This check is important because _load_model might fail even if path is set
        logger.error("Bot model failed to load even after config update. Check model integrity and paths.")
        sys.stderr.write("Error: Bot model failed to load. Exiting.\n")
        sys.exit(1)

    logger.info("Calling test_detection()...")
    try:
        bot.test_detection()
    except Exception as e:
        logger.error(f"Error during test_detection: {e}", exc_info=True)
        sys.stderr.write(f"Error during test_detection: {e}\n")
        sys.exit(1)
    logger.info("test_detection() call finished.")
    # --- End of modification ---
    # main() # Original main call is commented out for profiling