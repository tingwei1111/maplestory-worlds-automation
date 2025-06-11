#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapleStory Worlds 優化自動化系統
使用 YOLO 模型進行智能物件偵測和自動化操作
版本: 2.0
作者: AI Assistant
"""

import cv2
import mss
import numpy as np
import pyautogui
import time
import os
import sys
import logging
import yaml
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ultralytics import YOLO

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    
    def __init__(self, config_path: str = "config.yaml", load_config: bool = True): # Parameter renamed for clarity
        self.config_path = Path(config_path)
        if load_config:
            self.config = self._load_config_internal(str(self.config_path))
        else:
            self.config = self._get_default_config()
            if not self.config_path.exists():
                self.save_config(str(self.config_path)) # Save default if not loading and file absent
    
    def _load_config_internal(self, filepath: str) -> Dict:
        """Internal loading logic."""
        load_path = Path(filepath)
        try:
            if load_path.exists():
                with open(load_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    logger.info(f"配置已從 {load_path} 載入")
                    return loaded_config if loaded_config else self._get_default_config() # Handle empty config file
            else:
                logger.warning(f"配置文件 {load_path} 不存在，使用並保存默認配置")
                default_config = self._get_default_config()
                self._save_config_internal(str(load_path), default_config)
                return default_config
        except Exception as e:
            logger.error(f"載入配置 {load_path} 失敗: {e}. 使用默認配置.")
            return self._get_default_config()

    def load_config(self, filepath: Optional[str] = None):
        """載入配置文件, updating self.config and self.config_path."""
        load_path_str = filepath if filepath else str(self.config_path)
        self.config = self._load_config_internal(load_path_str)
        self.config_path = Path(load_path_str)

    def _save_config_internal(self, filepath: str, config_data: Dict):
        """Internal saving logic."""
        save_path = Path(filepath)
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, sort_keys=False, indent=4)
            logger.info(f"配置已成功保存到 {save_path}")
        except Exception as e:
            logger.error(f"保存配置到 {save_path} 失敗: {e}")

    def save_config(self, filepath: Optional[str] = None):
        """保存當前 self.config 到 YAML 文件"""
        save_path_str = filepath if filepath else str(self.config_path)
        self._save_config_internal(save_path_str, self.config)
        if filepath:
            self.config_path = Path(filepath)

    def _get_default_config(self) -> Dict:
        """獲取默認配置 - Aligned with GUI fields"""
        return {
            'model': {
                'path': 'weights/best.pt',
                'confidence_threshold': 0.5,
                'iou_threshold': 0.45,
                'device': 'auto'
            },
            'capture_region': {
                'x': 0, 'y': 0, 'width': 1920, 'height': 1080
            },
            'controls': {
                'pickup_key': 'z',
                'interact_key': 'space',
                'attack_method': 'click',
                'attack_key': 'ctrl',
                'movement_keys': {
                    'left': 'left', 'right': 'right', 'jump': 'alt', 'down': 'down'
                 }
            },
            'automation': {
                'action_delay_ms': 100,
                'scan_interval_ms': 500,
                'max_detection_distance': 150,
                'priority_targets': ['item', 'mob', 'npc'],
                'mob_hunting': {
                    'enable': False,
                    'search_delay_seconds': 5.0,
                    'max_search_time_seconds': 20,
                    'search_pattern': 'horizontal',
                    'move_duration_ms': 300,
                    'return_to_center': True
                }
            },
            'safety': {
                'enable_failsafe': True,
                'max_runtime_hours': 0,
                'pyautogui_pause_ms': 100
            },
            'logging': {
                'screenshot_log': False
            },
            'preview': {
                'show_window': False
            },
            'detection_behavior': {
                'mob': {'action': 'attack', 'attack_delay_ms': 500, 'max_distance': 150},
                'item': {'action': 'pickup', 'max_distance': 100},
                'npc': {'action': 'interact', 'max_distance': 80},
            }
        }
    
    def get(self, key_path: str, default=None):
        """獲取配置值，支持點分割路徑如 'model.confidence_threshold'"""
        try:
            keys = key_path.split('.')
            value = self.config
            for key in keys:
                if not isinstance(value, dict):
                    return default
                value = value[key]
            return value
        except (KeyError, TypeError):
            # logger.debug(f"Key '{key_path}' not found in config, returning default '{default}'. Current config: {self.config}")
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
    def __init__(self, config_path: str = "config.yaml", config_manager: Optional[ConfigManager] = None):
        if config_manager:
            self.config_manager = config_manager
        else:
            self.config_manager = ConfigManager(config_path)
        self.model = None
        self.running = False
        self.paused = False
        self.start_time = None
        self.performance_monitor = PerformanceMonitor()
        self._apply_config_settings() # Apply initial settings
        
        self.stats = {
            'detections': 0, 'actions_performed': 0, 'items_collected': 0,
            'mobs_attacked': 0, 'npcs_interacted': 0, 'searches_performed': 0,
            'search_time_total': 0
        }
        # Mob hunting related variables
        self.last_mob_detection_time = time.time() # Initialize to current time
        self.is_searching = False
        self.search_start_time = 0
        self.original_position = None # For more complex return logic (not fully implemented)
        self.search_direction = 1  # 1 for right, -1 for left
        self.search_moves = 0
        
        logger.info("OptimizedMapleBot 初始化完成")
        self._load_model() # Load model upon initialization

    def _apply_config_settings(self):
        """Apply settings from config_manager to bot attributes. Can be called to refresh settings."""
        capture_cfg = self.config_manager.get('capture_region', self.config_manager._get_default_config()['capture_region'])
        self.monitor = {'left': capture_cfg['x'], 'top': capture_cfg['y'],
                        'width': capture_cfg['width'], 'height': capture_cfg['height']}

        self.confidence_threshold = self.config_manager.get('model.confidence_threshold', 0.5)
        # Read delay/interval in ms from config and convert to seconds for bot's internal use
        self.action_delay = self.config_manager.get('automation.action_delay_ms', 100) / 1000.0
        self.scan_interval = self.config_manager.get('automation.scan_interval_ms', 500) / 1000.0

        max_runtime_hours = self.config_manager.get('safety.max_runtime_hours', 0)
        self.max_runtime = max_runtime_hours * 3600 if max_runtime_hours > 0 else float('inf')

        if self.config_manager.get('safety.enable_failsafe', True):
            pyautogui.FAILSAFE = True
        # Update PyAutoGUI's PAUSE based on config; this is a global setting for PyAutoGUI
        pyautogui.PAUSE = self.config_manager.get('safety.pyautogui_pause_ms', 100) / 1000.0

        # Check if model needs reloading due to path/device change, or update thresholds
        if self.model:
            new_model_path = self.config_manager.get('model.path')
            new_device = self.config_manager.get('model.device', 'auto')
            # Assuming model object has attributes like ckpt_path and device after loading
            # This part is highly dependent on how YOLO model objects store this info.
            # For simplicity, if critical params might change, consider reloading or providing a dedicated update method in YOLO wrapper.
            # For now, we'll just update conf/iou if path/device appear same.
            # A more robust check would be needed if model objects don't store path/device predictably.
            self.model.conf = self.confidence_threshold
            self.model.iou = self.config_manager.get('model.iou_threshold', 0.45)


    def _load_model(self):
        """載入 YOLO 模型 based on current config_manager settings."""
        model_path = self.config_manager.get('model.path', 'weights/best.pt') # Default path if not in config
        device = self.config_manager.get('model.device', 'auto')
        # Ensure confidence_threshold is up-to-date before loading/using model
        self.confidence_threshold = self.config_manager.get('model.confidence_threshold', 0.5)
        iou_threshold = self.config_manager.get('model.iou_threshold', 0.45)

        if not model_path or not Path(model_path).exists(): # Check if path is valid
            logger.error(f"模型文件不存在或路徑無效: {model_path}")
            self.model = None # Ensure model is None if loading fails
            return False
        
        try:
            logger.info(f"載入模型: {model_path} 使用設備: {device}")
            self.model = YOLO(model_path)
            if device != 'auto': # YOLO handles 'auto' or specific devices like 'cpu', 'cuda:0'
                self.model.to(device)

            self.model.conf = self.confidence_threshold # Set confidence on model
            self.model.iou = iou_threshold    # Set IoU on model
            
            logger.info(f"✅ 模型載入成功! 實際使用設備: {self.model.device}")
            logger.info(f"📊 模型類別: {self.model.names}")
            return True
        except Exception as e:
            logger.error(f"模型載入失敗: {e}", exc_info=True)
            self.model = None # Ensure model is None if loading fails
            return False

    def capture_screen(self) -> Optional[np.ndarray]:
        """優化的螢幕擷取 using MSS, returns BGR image."""
        try:
            with mss.mss() as sct:
                sct_img = sct.grab(self.monitor)
                # Convert RGB to BGR for OpenCV compatibility
                img = np.frombuffer(sct_img.rgb, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 3))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                return img
        except Exception as e:
            logger.error(f"螢幕擷取失敗: {e}")
            return None
    
    def detect_objects(self, img: np.ndarray) -> List[Detection]:
        """優化的物件偵測, returns a list of Detection objects."""
        if self.model is None:
            # logger.warning("Model not loaded, skipping detection.")
            return []
        
        detections = []
        start_time = time.time()
        
        try:
            results = self.model(img, verbose=False) # verbose=False for cleaner logs
            
            center_x, center_y = self.monitor['width'] // 2, self.monitor['height'] // 2
            
            for result in results: # Process each result object (usually one per image)
                if result.boxes is not None: # Check if 'boxes' attribute exists
                    for box in result.boxes:
                        xyxy = box.xyxy[0].cpu().numpy() # Bounding box coordinates
                        conf = float(box.conf[0].cpu().numpy()) # Confidence score
                        cls_id = int(box.cls[0].cpu().numpy()) # Class ID
                        class_name = self.model.names[cls_id] # Get class name from model
                        
                        # Filter by the bot's current confidence_threshold
                        if conf > self.confidence_threshold:
                            detection_center = (int((xyxy[0] + xyxy[2]) / 2), int((xyxy[1] + xyxy[3]) / 2))
                            distance = np.sqrt((detection_center[0] - center_x)**2 + (detection_center[1] - center_y)**2)
                            
                            detections.append(Detection(
                                bbox=[int(c) for c in xyxy], # Ensure coords are int
                                confidence=conf,
                                class_id=cls_id,
                                class_name=class_name,
                                center=detection_center,
                                distance_from_center=distance
                            ))
            
            detections = self._prioritize_detections(detections) # Sort by priority and distance
            self.stats['detections'] += len(detections)
            self.performance_monitor.record_detection_time(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"物件偵測過程中發生錯誤: {e}", exc_info=True)
        return detections

    def _prioritize_detections(self, detections: List[Detection]) -> List[Detection]:
        """按優先級和距離排序偵測結果."""
        priority_map = {name: i for i, name in enumerate(self.config_manager.get('automation.priority_targets', []))}
        # Sort key: lower priority number is better, then by distance.
        def sort_key(detection: Detection):
            return (priority_map.get(detection.class_name, 999), detection.distance_from_center)
        return sorted(detections, key=sort_key)

    def perform_action(self, detection: Detection) -> bool:
        """執行基於偵測結果的遊戲動作."""
        class_name = detection.class_name
        # Calculate absolute coordinates on screen
        abs_x = self.monitor['left'] + detection.center[0]
        abs_y = self.monitor['top'] + detection.center[1]

        # Get behavior specific to this class from config
        class_behavior = self.config_manager.get(f'detection_behavior.{class_name}', {})
        action_type = class_behavior.get('action', 'log_only') # Default to 'log_only'
        max_dist_class = class_behavior.get('max_distance')

        # Use class-specific max_distance, or fallback to general setting, then a hardcoded default
        max_distance = max_dist_class if max_dist_class is not None \
            else self.config_manager.get('automation.max_detection_distance', 150)

        if detection.distance_from_center > max_distance:
            # logger.debug(f"Skipping {class_name}, too far ({detection.distance_from_center:.0f}px > {max_distance}px)")
            return False
        
        action_performed = False
        logger.debug(f"Attempting action '{action_type}' for {class_name} at ({abs_x},{abs_y}) dist {detection.distance_from_center:.0f}px")

        try:
            if action_type == 'attack':
                pyautogui.moveTo(abs_x, abs_y, duration=0.05) # Quicker move for attack
                attack_method = self.config_manager.get('controls.attack_method', 'click')
                if attack_method == 'key':
                    attack_key = self.config_manager.get('controls.attack_key', 'ctrl')
                    pyautogui.press(attack_key)
                else:
                    pyautogui.click()
                logger.info(f"⚔️ Attacked {class_name} (Conf: {detection.confidence:.2f})")
                if class_name == 'mob': self.stats['mobs_attacked'] += 1 # Specific stat for mobs
                action_performed = True
                # Use class-specific attack delay, fallback to general action_delay if not set
                attack_delay_ms = class_behavior.get('attack_delay_ms', self.action_delay * 1000)
                time.sleep(attack_delay_ms / 1000.0)
            
            elif action_type == 'pickup':
                pyautogui.moveTo(abs_x, abs_y, duration=0.1)
                pickup_key = self.config_manager.get('controls.pickup_key', 'z')
                pyautogui.press(pickup_key)
                logger.info(f"🖐️ Picked up {class_name} (Conf: {detection.confidence:.2f})")
                if class_name == 'item': self.stats['items_collected'] +=1
                action_performed = True
                time.sleep(self.action_delay) # Use bot's general action_delay

            elif action_type == 'interact':
                pyautogui.moveTo(abs_x, abs_y, duration=0.1)
                interact_key = self.config_manager.get('controls.interact_key', 'space')
                pyautogui.press(interact_key)
                logger.info(f"🗣️ Interacted with {class_name} (Conf: {detection.confidence:.2f})")
                if class_name == 'npc': self.stats['npcs_interacted'] +=1
                action_performed = True
                time.sleep(self.action_delay) # Use bot's general action_delay

            elif action_type == 'log_only':
                logger.info(f"👁️ {class_name} detected (Conf: {detection.confidence:.2f}) - Logged only.")
                # This is not an "action_performed" for stats purposes.

            else:
                logger.warning(f"Unknown action type '{action_type}' specified for class '{class_name}'. No action taken.")


            if action_performed:
                self.stats['actions_performed'] += 1
                self.last_mob_detection_time = time.time() # Reset search timer if any significant action is taken
                if self.is_searching: self._end_mob_search() # Stop searching if we acted on something
                return True
        except Exception as e:
            logger.error(f"執行動作 '{action_type}' for {class_name} 失敗: {e}", exc_info=True)
        return False

    def _should_search_for_mobs(self) -> bool:
        """檢查是否應該開始尋找目標 (e.g. mobs)."""
        if not self.config_manager.get('automation.mob_hunting.enable', False): return False
        if self.is_searching: return False # Already searching
        
        search_delay_sec = self.config_manager.get('automation.mob_hunting.search_delay_seconds', 5.0)
        # Only search if no mobs (or primary targets) detected for a while
        return (time.time() - self.last_mob_detection_time > search_delay_sec)

    def _start_mob_search(self):
        """開始尋找目標."""
        if self.is_searching: return
        self.is_searching = True
        self.search_start_time = time.time()
        self.search_moves = 0 # Reset moves for this search session
        # self.original_position = pyautogui.position() # Potentially save current mouse/char position
        logger.info("🔍 開始尋找目標...")
    
    def _perform_mob_search(self):
        """執行尋找目標的移動動作."""
        if not self.is_searching: return
        
        max_search_time_sec = self.config_manager.get('automation.mob_hunting.max_search_time_seconds', 20)
        if time.time() - self.search_start_time > max_search_time_sec:
            logger.info("超過最大搜尋時間，停止搜尋。")
            self._end_mob_search()
            return
        
        pattern = self.config_manager.get('automation.mob_hunting.search_pattern', 'horizontal')
        move_duration_ms = self.config_manager.get('automation.mob_hunting.move_duration_ms', 300)

        if pattern == 'horizontal': self._horizontal_search(move_duration_ms)
        elif pattern == 'vertical': self._vertical_search(move_duration_ms)
        elif pattern == 'random': self._random_search(move_duration_ms)
        
        time.sleep(0.1) # Brief pause after a search move, before next scan_interval cycle

    def _horizontal_search(self, duration_ms: int):
        """水平搜尋移動."""
        key_name = 'right' if self.search_direction > 0 else 'left'
        move_key = self.config_manager.get(f'controls.movement_keys.{key_name}', key_name) # Default to key_name if not in config
        pyautogui.keyDown(move_key); time.sleep(duration_ms / 1000.0); pyautogui.keyUp(move_key)
        self.search_moves += 1
        if self.search_moves >= 5: # Example: change direction after 5 moves
            self.search_direction *= -1; self.search_moves = 0
            logger.info(f"🔄 改變搜尋方向: {'右' if self.search_direction > 0 else '左'}")

    def _vertical_search(self, duration_ms: int): # duration_ms for falling/down-jump
        """垂直搜尋移動（跳躍和向下跳平台）."""
        jump_key = self.config_manager.get('controls.movement_keys.jump', 'alt')
        down_key = self.config_manager.get('controls.movement_keys.down', 'down')
        if self.search_moves % 2 == 0: # Simple alternation: jump up, then try to go down
            pyautogui.press(jump_key); logger.info("⬆️ 跳躍搜尋")
        else: # Attempt to jump down from a platform
            pyautogui.keyDown(down_key); time.sleep(0.05); pyautogui.press(jump_key) # Hold Down + Press Jump
            time.sleep(duration_ms / 2000.0); # Shorter delay, assuming quick fall through platform
            pyautogui.keyUp(down_key)
            logger.info("⬇️ 向下搜尋 (嘗試跳下平台)")
        self.search_moves += 1

    def _random_search(self, duration_ms: int):
        """隨機搜尋移動."""
        import random
        choice = random.choice(['left', 'right', 'jump']) # Can add 'down_jump' or other patterns
        move_key_val = self.config_manager.get(f'controls.movement_keys.{choice}', choice)

        if choice == 'jump': pyautogui.press(move_key_val)
        else: # left or right
            pyautogui.keyDown(move_key_val); time.sleep(duration_ms / 1000.0); pyautogui.keyUp(move_key_val)
        logger.info(f"🎲 隨機移動: {choice}")
        self.search_moves +=1

    def _end_mob_search(self):
        """結束尋找目標狀態."""
        if not self.is_searching: return
        
        duration = time.time() - self.search_start_time
        self.stats['searches_performed'] += 1
        self.stats['search_time_total'] += duration
        self.is_searching = False
        logger.info(f"🏁 結束目標搜尋 (耗時: {duration:.1f}秒)")
        
        if self.config_manager.get('automation.mob_hunting.return_to_center', True):
             self._return_to_center_simplified()

    def _return_to_center_simplified(self):
        """簡易返回中心邏輯."""
        logger.info("🏠 嘗試返回原始大致區域...")
        # This is very basic, move opposite to last general direction for a few steps.
        # A robust implementation would track net displacement or use map waypoints.
        key_name_to_reverse_last_phase = 'left' if self.search_direction > 0 else 'right'
        move_key = self.config_manager.get(f'controls.movement_keys.{key_name_to_reverse_last_phase}', key_name_to_reverse_last_phase)
        duration_ms = self.config_manager.get('automation.mob_hunting.move_duration_ms',300)
        # Try to reverse about half the number of moves made in the last search segment
        num_return_moves = self.search_moves // 2 + 1
        for _ in range(num_return_moves):
             pyautogui.keyDown(move_key); time.sleep(duration_ms / 1000.0); pyautogui.keyUp(move_key)
             time.sleep(0.1) # Small pause between moves

    def _check_safety_conditions(self) -> bool:
        """檢查安全條件, e.g., max runtime."""
        if self.start_time and (time.time() - self.start_time > self.max_runtime):
            logger.warning("達到最大運行時間限制，停止自動化。")
            return False
        return True

    def start_automation(self, show_preview: Optional[bool] = None):
        """開始優化的自動化流程."""
        self.config_manager.load_config() # Ensure latest config from file
        self._apply_config_settings()     # Apply any changes from config to bot attributes
        
        if not self.model and not self._load_model(): # Try to load model if not already loaded
            logger.error("模型未能成功載入或設定，無法開始自動化。請檢查 GUI 或 config.yaml 中的模型路徑。")
            return

        self.running = True
        self.start_time = time.time()
        self.last_mob_detection_time = time.time() # Initialize for search logic

        # Determine preview window based on argument or config
        preview_flag = show_preview if show_preview is not None \
            else self.config_manager.get('preview.show_window', False)
        preview_window_name = 'MapleStory Auto Bot Preview'
        self.preview_active = False # Flag to manage cv2 window state

        logger.info("🚀 開始 MapleStory Worlds 優化自動化")
        logger.info(f"預覽視窗: {'啟用' if preview_flag else '禁用'}")
        logger.info("在預覽視窗中按 'q' 暫停/恢復, 'Esc' 停止。或在終端按 Ctrl+C 停止。")
        
        last_stats_time = time.time()

        try:
            while self.running:
                if not self._check_safety_conditions():
                    logger.info("安全條件未通過，停止自動化。")
                    break
                if self.paused:
                    # While paused, still process OpenCV window events if preview is active
                    if self.preview_active and preview_flag:
                        key = cv2.waitKey(100) & 0xFF # Check for key press every 100ms
                        if key == ord('q'): self.paused = not self.paused; logger.info(f"{'⏸️ 暫停' if self.paused else '▶️ 恢復'}自動化")
                        elif key == 27: self.running = False; logger.info("ESC 按下，停止自動化。")
                    else:
                        time.sleep(0.1) # Standard sleep if no preview
                    continue

                loop_start_time = time.time()
                img = self.capture_screen()
                if img is None: time.sleep(self.scan_interval); continue # Wait before retrying capture

                detections = self.detect_objects(img)
                
                # Check if any detected object should trigger action (not 'log_only')
                # This helps decide if we should reset the mob search timer
                meaningful_detection_this_cycle = any(
                    self.config_manager.get(f'detection_behavior.{d.class_name}.action', 'log_only') != 'log_only'
                    for d in detections if d.distance_from_center <= self.config_manager.get(f'detection_behavior.{d.class_name}.max_distance', self.config_manager.get('automation.max_detection_distance',150))
                )

                if meaningful_detection_this_cycle:
                    self.last_mob_detection_time = time.time() # Reset timer as we saw something actionable
                    if self.is_searching: self._end_mob_search() # Stop searching
                
                actions_this_cycle = 0
                for detection in detections: # Iterate through prioritized detections
                    if not self.running or self.paused: break # Check status before each action
                    if self.perform_action(detection):
                        actions_this_cycle += 1
                        # Limit actions per scan cycle to prevent spamming and allow re-evaluation
                        if actions_this_cycle >= self.config_manager.get('automation.max_actions_per_cycle', 2):
                            break
                        # No need for extra sleep here, perform_action includes its own delay based on action type
                
                # Search logic: if no meaningful detections and should search
                if not meaningful_detection_this_cycle and self._should_search_for_mobs():
                    self._start_mob_search()
                
                if self.is_searching: self._perform_mob_search() # Execute one step of search pattern
                
                if preview_flag:
                    display_img = self._draw_detections(img.copy(), detections)
                    cv2.imshow(preview_window_name, display_img)
                    self.preview_active = True # Mark preview as active
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'): self.paused = not self.paused; logger.info(f"{'⏸️ 暫停' if self.paused else '▶️ 恢復'}自動化")
                    elif key == 27: self.running = False; logger.info("ESC 按下，停止自動化。")
                else: # If preview becomes disabled mid-run, ensure window is closed
                    if self.preview_active:
                        cv2.destroyWindow(preview_window_name)
                        self.preview_active = False
                
                self.performance_monitor.update_fps()
                if time.time() - last_stats_time >= 30:
                    self._log_statistics(); last_stats_time = time.time()
                
                elapsed_loop_time = time.time() - loop_start_time
                sleep_time = self.scan_interval - elapsed_loop_time
                if sleep_time > 0: time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("⏹️ 使用者中斷自動化 (Ctrl+C)")
            self.running = False # Ensure running flag is set to false
        except Exception as e:
            logger.error(f"自動化過程中發生未預期錯誤: {e}", exc_info=True)
            self.running = False # Ensure running flag is set to false
        finally:
            self.running = False # Explicitly set running to false on exit
            if self.preview_active: # Ensure window is destroyed if it was active
                cv2.destroyWindow(preview_window_name)
                self.preview_active = False
            logger.info("執行緒清理完成。")
            self._log_final_statistics()
            logger.info("✅ 自動化已停止")

    def _draw_detections(self, img: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """繪製偵測結果到圖像上."""
        for det in detections:
            # Default color, can be customized further via config if needed
            color_map = { 'mob': (0,0,255), 'item': (0,255,0), 'npc': (255,0,0) }
            color = color_map.get(det.class_name, (200,200,200)) # Default grey for others
            
            # Draw bounding box
            cv2.rectangle(img, (det.bbox[0], det.bbox[1]), (det.bbox[2], det.bbox[3]), color, 2)
            # Prepare label text
            label = f"{det.class_name}: {det.confidence:.2f} ({det.distance_from_center:.0f}px)"
            # Put label above the bounding box
            cv2.putText(img, label, (det.bbox[0], det.bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Display FPS
        fps_text = f"FPS: {self.performance_monitor.current_fps:.1f}"
        cv2.putText(img, fps_text, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0),2) # Green FPS text
        # Display Paused status
        if self.paused:
             cv2.putText(img, "PAUSED", (self.monitor['width']//2 - 50, self.monitor['height']//2),
                         cv2.FONT_HERSHEY_TRIPLEX, 1, (0,0,255), 2, cv2.LINE_AA) # Red PAUSED text
        return img

    def _log_statistics(self):
        """記錄當前運行統計信息."""
        runtime_sec = time.time() - self.start_time if self.start_time else 0
        avg_det_time_ms = self.performance_monitor.get_avg_detection_time() * 1000
        
        logger.info(f"📊 STATS | Runtime: {runtime_sec/60:.1f}m | FPS: {self.performance_monitor.current_fps:.1f} | AvgDetTime: {avg_det_time_ms:.1f}ms")
        logger.info(f"  Detections: {self.stats['detections']} | Actions: {self.stats['actions_performed']} | Mobs Attacked: {self.stats['mobs_attacked']} | Items Collected: {self.stats['items_collected']}")
        if self.stats['searches_performed'] > 0:
            avg_search_s = self.stats['search_time_total'] / self.stats['searches_performed']
            logger.info(f"  Searches: {self.stats['searches_performed']} (Avg Duration: {avg_search_s:.1f}s)")
    
    def _log_final_statistics(self):
        """記錄最終統計報告."""
        logger.info("🎯 FINAL STATISTICS:")
        self._log_statistics() # Call the regular statistics logging

    def test_detection(self):
        """測試單次物件偵測功能."""
        self.config_manager.load_config() # Load latest config
        self._apply_config_settings()     # Apply settings
        if not self.model and not self._load_model(): # Ensure model is loaded
            logger.error("模型未能成功載入，無法執行偵測測試。")
            return
        
        logger.info("🧪 測試物件偵測功能 (單次擷取)...")
        img = self.capture_screen()
        if img is None:
            logger.error("無法擷取畫面進行測試。")
            return
        
        detections = self.detect_objects(img)
        logger.info(f"📊 偵測結果: 發現 {len(detections)} 個物件")
        for i, det in enumerate(detections,1):
            logger.info(f"  {i}. {det.class_name} (信賴度: {det.confidence:.2f}, 距離中心: {det.distance_from_center:.0f}px)")
        
        if detections:
            result_img = self._draw_detections(img.copy(), detections) # Draw on a copy
            cv2.imshow('Detection Test', result_img)
            logger.info("按任意鍵關閉預覽視窗...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            logger.info("在擷取的畫面中未偵測到任何物件。")

def load_available_models(weights_dir_str: str = "weights") -> Dict[str, str]:
    """載入可用的模型文件 (.pt and .onnx)"""
    models = {}
    weights_dir = Path(weights_dir_str)
    if weights_dir.exists():
        print("可用的模型文件:")
        # Combine .pt and .onnx file searches
        model_files = list(weights_dir.glob("*.pt")) + list(weights_dir.glob("*.onnx"))
        for i, model_file in enumerate(model_files, 1):
            size_mb = model_file.stat().st_size / (1024*1024)
            print(f"  {i}. {model_file.name} ({size_mb:.1f} MB)") # Show only filename
            models[str(i)] = str(model_file.resolve()) # Store full resolved path
    else:
        logger.warning(f"模型資料夾 '{weights_dir_str}' 不存在。")
    return models

def main():
    """主程序 (CLI)"""
    print("🍁 MapleStory Worlds 優化自動化系統 v2.1 (CLI)") # Updated version
    print("=" * 60)
    
    # Instantiate ConfigManager for CLI operations. It loads or creates config.yaml.
    config_for_cli = ConfigManager()

    models = load_available_models()
    if not models:
        logger.error("在 'weights' 資料夾中未找到任何模型文件 (.pt 或 .onnx)。請確保模型存在。")
        # Proceeding without a model might be possible if user only wants to view/edit config via CLI then use GUI

    if models: # Only ask for model selection if models are available
        current_model_path_in_config = Path(config_for_cli.get('model.path', 'N/A'))
        prompt_message = (
            f"\n請選擇模型文件 (1-{len(models)}, Enter "
            f"使用設定檔中的模型 '{current_model_path_in_config.name if current_model_path_in_config.exists() else 'N/A'}'): "
        )
        choice = input(prompt_message).strip()

        if choice and choice in models:
            selected_model_path = models[choice]
            config_for_cli.config['model']['path'] = selected_model_path # Update config object
            config_for_cli.save_config() # Save this choice back to config.yaml
            logger.info(f"已選擇模型: {selected_model_path} 並保存到設定檔。")
        elif not choice:
            logger.info(f"將使用設定檔中的模型: {current_model_path_in_config if current_model_path_in_config.exists() else '未設定'}")
        else: # Invalid choice, not empty
            logger.warning(f"無效選擇 '{choice}'. 將使用設定檔中的模型。")

    # Bot will initialize its own ConfigManager instance, reading from config.yaml
    # which may have been updated by the CLI model selection above.
    bot = OptimizedMapleBot()
    
    while True:
        print("\n🎮 CLI 功能選單:")
        print("1. 測試物件偵測")
        print("2. 開始自動化 (使用設定檔預覽設定)")
        # print("3. 開始自動化 (無預覽)") # Option 2 now covers this via config
        print("3. 調整擷取區域設定 (CLI)")
        print("4. 查看當前配置 (config.yaml)")
        print("5. 查看即時統計")
        print("6. 退出 CLI") # Changed from 7 to 6
        
        user_choice = input("\n請選擇功能 (1-6): ").strip()
        
        if user_choice == '1':
            bot.test_detection()
        elif user_choice == '2':
            # Start automation; show_preview will be determined by bot's config
            bot.start_automation()
        # elif user_choice == '3': bot.start_automation(show_preview=False) # Covered by option 2
        elif user_choice == '3':
            _adjust_capture_region_cli(bot.config_manager, bot) # Pass bot's CM and bot instance
        elif user_choice == '4':
            _show_config_cli(bot.config_manager) # Pass bot's CM
        elif user_choice == '5':
            bot._log_statistics() # Log current stats if bot is running or has run
        elif user_choice == '6':
            logger.info("正在退出 CLI...")
            break
        else:
            print("❌ 無效選擇，請重試。")
    
    print("👋 再見！")

def _adjust_capture_region_cli(cm: ConfigManager, bot_instance: Optional[OptimizedMapleBot] = None):
    """通过 CLI 调整擷取區域設定并保存到 config.yaml.
    Optionally updates the bot instance if provided."""
    current_cr = cm.get('capture_region', cm._get_default_config()['capture_region'])
    print(f"\n當前擷取區域: X={current_cr.get('x')}, Y={current_cr.get('y')}, W={current_cr.get('width')}, H={current_cr.get('height')}")
    try:
        x = int(input(f"新 X (Enter 保留 {current_cr.get('x')}): ") or current_cr.get('x'))
        y = int(input(f"新 Y (Enter 保留 {current_cr.get('y')}): ") or current_cr.get('y'))
        w = int(input(f"新寬度 (Enter 保留 {current_cr.get('width')}): ") or current_cr.get('width'))
        h = int(input(f"新高度 (Enter 保留 {current_cr.get('height')}): ") or current_cr.get('height'))

        # Basic validation for width and height
        if w <= 0 or h <= 0:
            print("❌ 寬度和高度必須是正數。")
            return

        new_cr = {'x':x, 'y':y, 'width':w, 'height':h}
        cm.config['capture_region'] = new_cr # Update the config dictionary in ConfigManager
        cm.save_config() # Save the updated dictionary to file

        if bot_instance:
            bot_instance._apply_config_settings() # Re-apply settings to the running bot instance
            logger.info(f"Bot instance's capture settings updated to: {bot_instance.monitor}")
        print(f"✅ 擷取區域已更新並保存到 config.yaml: {new_cr}")
    except ValueError:
        print("❌ 輸入無效，請確保所有值都是有效的整數。")
    except Exception as e:
        logger.error(f"調整擷取區域時發生錯誤: {e}")

def _show_config_cli(cm: ConfigManager):
    """顯示當前配置 (從 ConfigManager's config)."""
    print("\n⚙️ 當前配置 (源自 config.yaml):")
    # Use yaml.dump for a nicely formatted output of the current config dictionary
    print(yaml.dump(cm.config, allow_unicode=True, sort_keys=False, indent=2))

if __name__ == "__main__":
    if "--gui" in sys.argv:
        try:
            # Local import for GUI mode to prevent issues if Tkinter is not installed for CLI use
            import tkinter as tk
            from gui import App  # Assuming gui.py contains the App class

            logger.info("啟動 GUI 模式...")
            # The App class will create its own ConfigManager instance.
            # It's okay if main() also created one; they operate on the same config.yaml.
            app = App()
            app.mainloop()
        except ImportError as e:
            logger.error(f"無法導入 GUI 模組 (gui.py 或 Tkinter): {e}. "
                         "請確保 gui.py 檔案存在於同目錄下且 Tkinter 圖形庫已正確安裝。")
            logger.info("如果只想使用 CLI 模式，請執行程式時不加上 --gui 參數。")
            # Fallback to CLI if GUI fails to import essential modules
            # print("\nFalling back to CLI mode due to GUI import error.")
            # main()
        except tk.TclError as e:
            logger.error(f"Tkinter 初始化錯誤: {e}. Tkinter 可能未正確安裝或 GUI 環境設定不完整。")
            logger.info("如果只想使用 CLI 模式，請執行程式時不加上 --gui 參數。")
            # print("\nFalling back to CLI mode due to Tkinter error.")
            # main()
        except Exception as e:
            logger.error(f"啟動 GUI 時發生未預期錯誤: {e}", exc_info=True)
            # print("\nFalling back to CLI mode due to unexpected GUI error.")
            # main()
    else:
        main()