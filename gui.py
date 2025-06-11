import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os

import logging # Added for TextHandler
from tkinter.scrolledtext import ScrolledText # Added for log display

# Adjust sys.path to ensure auto.py can be imported
# This assumes gui.py is in the root directory and auto.py is also in the root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from auto import ConfigManager, OptimizedMapleBot
    import threading
except ImportError as e:
    messagebox.showerror("Error", f"Could not import modules from auto.py: {e}. Ensure auto.py is in the same directory or accessible via PYTHONPATH.")
    sys.exit(1)

# Custom logging handler to redirect logs to a ScrolledText widget
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state='disabled') # Start as read-only

    def emit(self, record):
        msg = self.format(record)
        # Thread-safe way to update Tkinter widget
        def append_message():
            self.text_widget.configure(state='normal') # Enable editing to insert text
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled') # Disable editing
            self.text_widget.see(tk.END) # Scroll to the end

        # Schedule the UI update in the main Tkinter thread
        self.text_widget.after(0, append_message)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MapleStory Worlds Automation Control")
        self.geometry("800x750")  # Increased height for log display

        try:
            self.config_manager = ConfigManager()
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load initial configuration: {e}")
            self.config_manager = ConfigManager(load_config=False)

        try:
            self.bot = OptimizedMapleBot(config_manager=self.config_manager)
        except Exception as e:
            messagebox.showerror("Bot Error", f"Failed to initialize OptimizedMapleBot: {e}")
            self.bot = None

        self.bot_thread = None
        self.bot_state = "idle"

        self._create_menubar()
        self._create_tabs()
        self._create_control_panel()
        self._create_log_display() # New log display area
        self._create_status_bar()
        self._setup_logging()      # Configure custom logger

        self._populate_config_to_ui()
        self._update_button_states()

    def _create_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Configuration", command=self._load_config_from_file)
        file_menu.add_command(label="Save Configuration", command=self._save_config_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self._create_general_model_tab()
        self._create_controls_tab()
        self._create_mob_hunting_tab()
        self._create_detection_behavior_tab()
        self._create_monitoring_logging_tab() # New Monitoring & Logging Tab
        # Add other tabs here in the future
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

    def _create_general_model_tab(self):
        self.tab_general_model = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general_model, text="General & Model")

        # --- UI Variables ---
        # Capture Window
        self.capture_left_var = tk.StringVar()
        self.capture_top_var = tk.StringVar()
        self.capture_width_var = tk.StringVar()
        self.capture_height_var = tk.StringVar()
        self.capture_preset_var = tk.StringVar()

        # Model Settings
        self.model_path_var = tk.StringVar()
        self.confidence_threshold_var = tk.StringVar()
        self.iou_threshold_var = tk.StringVar()
        self.device_var = tk.StringVar(value="auto") # Default value

        # Automation Core
        self.action_delay_var = tk.StringVar()
        self.scan_interval_var = tk.StringVar()
        self.max_detection_distance_var = tk.StringVar()
        self.pyautogui_pause_var = tk.StringVar()

        # Safety
        self.enable_failsafe_var = tk.BooleanVar()
        self.max_runtime_var = tk.StringVar()
        self.screenshot_log_var = tk.BooleanVar()

        # Preview
        self.show_preview_var = tk.BooleanVar()


        # --- Layout ---
        tab_content = ttk.Frame(self.tab_general_model)
        tab_content.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Capture Window Section
        capture_frame = ttk.LabelFrame(tab_content, text="Capture Window")
        capture_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(capture_frame, text="Left:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(capture_frame, textvariable=self.capture_left_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(capture_frame, text="Top:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(capture_frame, textvariable=self.capture_top_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(capture_frame, text="Width:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(capture_frame, textvariable=self.capture_width_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(capture_frame, text="Height:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(capture_frame, textvariable=self.capture_height_var).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(capture_frame, text="Preset:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Combobox(capture_frame, textvariable=self.capture_preset_var, values=["Full Screen", "1920x1080", "Custom"]).grid(row=4, column=1, padx=5, pady=2, sticky="ew")
        capture_frame.columnconfigure(1, weight=1)


        # Model Settings Section
        model_frame = ttk.LabelFrame(tab_content, text="Model Settings")
        model_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(model_frame, text="Model Path:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        model_path_entry = ttk.Entry(model_frame, textvariable=self.model_path_var)
        model_path_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(model_frame, text="Browse...", command=self._browse_model_path).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(model_frame, text="Confidence Threshold:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(model_frame, textvariable=self.confidence_threshold_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew", columnspan=2)
        ttk.Label(model_frame, text="IoU Threshold:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(model_frame, textvariable=self.iou_threshold_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew", columnspan=2)
        ttk.Label(model_frame, text="Device:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Combobox(model_frame, textvariable=self.device_var, values=["auto", "cpu", "cuda", "mps"]).grid(row=3, column=1, padx=5, pady=2, sticky="ew", columnspan=2)
        model_frame.columnconfigure(1, weight=1)

        # Automation Core Section
        core_frame = ttk.LabelFrame(tab_content, text="Automation Core")
        core_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(core_frame, text="Action Delay (s):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(core_frame, textvariable=self.action_delay_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(core_frame, text="Scan Interval (s):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(core_frame, textvariable=self.scan_interval_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(core_frame, text="Max Detection Distance (px):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(core_frame, textvariable=self.max_detection_distance_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(core_frame, text="PyAutoGUI Pause (s):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(core_frame, textvariable=self.pyautogui_pause_var).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        core_frame.columnconfigure(1, weight=1)


        # Safety Section
        safety_frame = ttk.LabelFrame(tab_content, text="Safety")
        safety_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew", rowspan=2) # Span across rows

        ttk.Checkbutton(safety_frame, text="Enable Failsafe", variable=self.enable_failsafe_var).grid(row=0, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        ttk.Label(safety_frame, text="Max Runtime (hours):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(safety_frame, textvariable=self.max_runtime_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Checkbutton(safety_frame, text="Screenshot Log", variable=self.screenshot_log_var).grid(row=2, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        safety_frame.columnconfigure(1, weight=1)


        # Preview Section
        preview_frame = ttk.LabelFrame(tab_content, text="Preview")
        preview_frame.grid(row=2, column=2, padx=5, pady=5, sticky="nsew") # Below Safety

        ttk.Checkbutton(preview_frame, text="Show Preview Window", variable=self.show_preview_var).pack(padx=5, pady=5, anchor="w")

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=1)
        tab_content.columnconfigure(2, weight=1) # Give some weight to the third column as well


    def _browse_model_path(self):
        filepath = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=(("PyTorch Models", "*.pt"), ("ONNX Models", "*.onnx"), ("All files", "*.*"))
        )
        if filepath:
            self.model_path_var.set(filepath)

    def _get_nested_config(self, keys, default=None):
        """Safely gets a value from a nested dictionary structure."""
        current = self.config_manager.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def _set_nested_config(self, keys, value):
        """Safely sets a value in a nested dictionary structure."""
        d = self.config_manager.config
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value


    def _populate_config_to_ui(self):
        if not self.config_manager or not self.config_manager.config:
            # messagebox.showwarning("Config", "No configuration loaded to populate UI.")
            return

        # Capture Window
        self.capture_left_var.set(str(self._get_nested_config(['capture_region', 'x'], '0')))
        self.capture_top_var.set(str(self._get_nested_config(['capture_region', 'y'], '0')))
        self.capture_width_var.set(str(self._get_nested_config(['capture_region', 'width'], '1920')))
        self.capture_height_var.set(str(self._get_nested_config(['capture_region', 'height'], '1080')))
        # self.capture_preset_var.set(...) # Needs logic if presets modify above values

        # Model Settings
        self.model_path_var.set(self._get_nested_config(['model', 'path'], ''))
        self.confidence_threshold_var.set(str(self._get_nested_config(['model', 'confidence_threshold'], '0.5')))
        self.iou_threshold_var.set(str(self._get_nested_config(['model', 'iou_threshold'], '0.45')))
        self.device_var.set(self._get_nested_config(['model', 'device'], 'auto'))

        # Automation Core
        self.action_delay_var.set(str(self._get_nested_config(['automation', 'action_delay_ms'], '100')))
        self.scan_interval_var.set(str(self._get_nested_config(['automation', 'scan_interval_ms'], '500')))
        self.max_detection_distance_var.set(str(self._get_nested_config(['automation', 'max_detection_distance'], '100')))
        self.pyautogui_pause_var.set(str(self._get_nested_config(['safety', 'pyautogui_pause_ms'], '100'))) # Note: Key was pyautogui_pause in example, but safety.pyautogui_pause_ms in typical config

        # Safety
        self.enable_failsafe_var.set(self._get_nested_config(['safety', 'enable_failsafe'], True))
        self.max_runtime_var.set(str(self._get_nested_config(['safety', 'max_runtime_hours'], '0'))) # 0 for indefinite
        self.screenshot_log_var.set(self._get_nested_config(['logging', 'screenshot_log'], False))

        # Preview
        self.show_preview_var.set(self._get_nested_config(['preview', 'show_window'], False))

        # --- Controls Tab ---
        # General Keys
        self.pickup_key_var.set(self._get_nested_config(['controls', 'pickup_key'], 'z'))
        self.interact_key_var.set(self._get_nested_config(['controls', 'interact_key'], 'space'))
        self.attack_key_var.set(self._get_nested_config(['controls', 'attack_key'], 'ctrl'))
        self.attack_method_var.set(self._get_nested_config(['controls', 'attack_method'], 'click'))
        # Movement Keys
        self.move_left_var.set(self._get_nested_config(['controls', 'movement_keys', 'left'], 'left'))
        self.move_right_var.set(self._get_nested_config(['controls', 'movement_keys', 'right'], 'right'))
        self.move_jump_var.set(self._get_nested_config(['controls', 'movement_keys', 'jump'], 'alt'))
        self.move_up_var.set(self._get_nested_config(['controls', 'movement_keys', 'up'], 'up')) # Added 'up'
        self.move_down_var.set(self._get_nested_config(['controls', 'movement_keys', 'down'], 'down'))
        # Skill & System Keys
        self.skill1_key_var.set(self._get_nested_config(['controls', 'skill_keys', 'skill_1'], '1'))
        self.skill2_key_var.set(self._get_nested_config(['controls', 'skill_keys', 'skill_2'], '2'))
        self.skill3_key_var.set(self._get_nested_config(['controls', 'skill_keys', 'skill_3'], '3'))
        self.skill4_key_var.set(self._get_nested_config(['controls', 'skill_keys', 'skill_4'], '4'))
        self.potion_key_var.set(self._get_nested_config(['controls', 'skill_keys', 'potion'], '5'))
        self.inventory_key_var.set(self._get_nested_config(['controls', 'system_keys', 'inventory'], 'i'))
        self.status_key_var.set(self._get_nested_config(['controls', 'system_keys', 'status'], 's'))
        self.chat_key_var.set(self._get_nested_config(['controls', 'system_keys', 'chat'], 'enter'))


        # --- Mob Hunting & Priority Tab ---
        self.mob_hunting_enable_var.set(self._get_nested_config(['automation', 'mob_hunting', 'enable'], False))
        self.mob_hunting_search_pattern_var.set(self._get_nested_config(['automation', 'mob_hunting', 'search_pattern'], 'horizontal'))
        self.mob_hunting_move_distance_var.set(str(self._get_nested_config(['automation', 'mob_hunting', 'move_distance'], '100'))) # Kept as string in UI
        self.mob_hunting_search_delay_ms_var.set(str(self._get_nested_config(['automation', 'mob_hunting', 'search_delay_ms'], '2000'))) # Default to 2000ms
        self.mob_hunting_max_search_time_ms_var.set(str(self._get_nested_config(['automation', 'mob_hunting', 'max_search_time_ms'], '10000'))) # Default to 10000ms
        self.mob_hunting_return_to_center_var.set(self._get_nested_config(['automation', 'mob_hunting', 'return_to_center'], True))

        priority_targets_list = self._get_nested_config(['automation', 'priority_targets'], ['mob', 'item', 'npc'])
        self.priority_targets_var.set(", ".join(priority_targets_list))

        # --- Detection Behavior Tab ---
        # Defined classes for behavior configuration
        defined_classes = self.config_manager.get('detection_behavior', {}).keys()
        if not defined_classes: # Fallback if detection_behavior is empty or not in config
            defined_classes = ['mob', 'item', 'npc', 'character', 'environment', 'ui_element'] # Default set

        for class_name in defined_classes:
            if class_name not in self.detection_behavior_vars: # Ensure var dict exists
                 self.detection_behavior_vars[class_name] = {} # Create if accessed first time here (e.g. new class in config)
                 # This scenario (new class in config not yet in UI vars) should ideally be handled by dynamically creating UI
                 # For now, we assume UI vars are created for a predefined set of classes.

            # Action
            action_var = self.detection_behavior_vars[class_name].get('action_var')
            if action_var: # Check if UI element and its var were created
                action_val = self._get_nested_config(['detection_behavior', class_name, 'action'], 'ignore')
                action_var.set(action_val)

            # Log Detection
            log_var = self.detection_behavior_vars[class_name].get('log_var')
            if log_var:
                log_val = self._get_nested_config(['detection_behavior', class_name, 'log'], False)
                log_var.set(log_val)

            # Max Distance
            max_dist_var = self.detection_behavior_vars[class_name].get('max_distance_var')
            if max_dist_var:
                max_dist_val = str(self._get_nested_config(['detection_behavior', class_name, 'max_distance'], '100'))
                max_dist_var.set(max_dist_val)

            # Attack Delay (specific to 'mob' or classes that can 'attack')
            if 'attack_delay_ms_var' in self.detection_behavior_vars[class_name]:
                attack_delay_var = self.detection_behavior_vars[class_name]['attack_delay_ms_var']
                attack_delay_val = str(self._get_nested_config(['detection_behavior', class_name, 'attack_delay_ms'], '500'))
                attack_delay_var.set(attack_delay_val)

            # Interaction Delay (specific to 'npc' or classes that can 'interact')
            if 'interaction_delay_ms_var' in self.detection_behavior_vars[class_name]:
                interaction_delay_var = self.detection_behavior_vars[class_name]['interaction_delay_ms_var']
                interaction_delay_val = str(self._get_nested_config(['detection_behavior', class_name, 'interaction_delay_ms'], '500'))
                interaction_delay_var.set(interaction_delay_val)

        # --- Monitoring & Logging Tab ---
        if hasattr(self, 'log_level_var'): # Check if UI vars for this tab exist
            self.log_level_var.set(self._get_nested_config(['monitoring', 'log_level'], 'INFO'))
            self.max_log_size_mb_var.set(str(self._get_nested_config(['monitoring', 'max_log_size_mb'], '10')))
            self.enable_performance_monitor_var.set(self._get_nested_config(['monitoring', 'enable_performance_monitor'], True))


    def _load_config_from_file(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Load Configuration File",
                filetypes=(("YAML files", "*.yaml *.yml"), ("All files", "*.*")),
                initialdir=os.path.dirname(self.config_manager.config_path) # Start in the current config directory
            )
            if filepath:
                self.config_manager.load_config(filepath)
                self._populate_config_to_ui()
                messagebox.showinfo("Config Loaded", f"Configuration loaded successfully from\n{filepath}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load configuration: {e}")

    def _save_config_to_file(self):
        try:
            # Update self.config_manager.config from UI variables
            # Capture Window
            self._set_nested_config(['capture_region', 'x'], int(self.capture_left_var.get()))
            self._set_nested_config(['capture_region', 'y'], int(self.capture_top_var.get()))
            self._set_nested_config(['capture_region', 'width'], int(self.capture_width_var.get()))
            self._set_nested_config(['capture_region', 'height'], int(self.capture_height_var.get()))

            # Model Settings
            self._set_nested_config(['model', 'path'], self.model_path_var.get())
            self._set_nested_config(['model', 'confidence_threshold'], float(self.confidence_threshold_var.get()))
            self._set_nested_config(['model', 'iou_threshold'], float(self.iou_threshold_var.get()))
            self._set_nested_config(['model', 'device'], self.device_var.get())

            # Automation Core
            self._set_nested_config(['automation', 'action_delay_ms'], int(self.action_delay_var.get()))
            self._set_nested_config(['automation', 'scan_interval_ms'], int(self.scan_interval_var.get()))
            self._set_nested_config(['automation', 'max_detection_distance'], int(self.max_detection_distance_var.get()))
            self._set_nested_config(['safety', 'pyautogui_pause_ms'], int(self.pyautogui_pause_var.get()))

            # Safety
            self._set_nested_config(['safety', 'enable_failsafe'], self.enable_failsafe_var.get())
            self._set_nested_config(['safety', 'max_runtime_hours'], int(self.max_runtime_var.get()))
            self._set_nested_config(['logging', 'screenshot_log'], self.screenshot_log_var.get())

            # Preview
            self._set_nested_config(['preview', 'show_window'], self.show_preview_var.get())

            # --- Controls Tab ---
            # General Keys
            self._set_nested_config(['controls', 'pickup_key'], self.pickup_key_var.get())
            self._set_nested_config(['controls', 'interact_key'], self.interact_key_var.get())
            self._set_nested_config(['controls', 'attack_key'], self.attack_key_var.get())
            self._set_nested_config(['controls', 'attack_method'], self.attack_method_var.get())
            # Movement Keys
            self._set_nested_config(['controls', 'movement_keys', 'left'], self.move_left_var.get())
            self._set_nested_config(['controls', 'movement_keys', 'right'], self.move_right_var.get())
            self._set_nested_config(['controls', 'movement_keys', 'jump'], self.move_jump_var.get())
            self._set_nested_config(['controls', 'movement_keys', 'up'], self.move_up_var.get())
            self._set_nested_config(['controls', 'movement_keys', 'down'], self.move_down_var.get())
            # Skill & System Keys
            self._set_nested_config(['controls', 'skill_keys', 'skill_1'], self.skill1_key_var.get())
            self._set_nested_config(['controls', 'skill_keys', 'skill_2'], self.skill2_key_var.get())
            self._set_nested_config(['controls', 'skill_keys', 'skill_3'], self.skill3_key_var.get())
            self._set_nested_config(['controls', 'skill_keys', 'skill_4'], self.skill4_key_var.get())
            self._set_nested_config(['controls', 'skill_keys', 'potion'], self.potion_key_var.get())
            self._set_nested_config(['controls', 'system_keys', 'inventory'], self.inventory_key_var.get())
            self._set_nested_config(['controls', 'system_keys', 'status'], self.status_key_var.get())
            self._set_nested_config(['controls', 'system_keys', 'chat'], self.chat_key_var.get())

            # --- Mob Hunting & Priority Tab ---
            self._set_nested_config(['automation', 'mob_hunting', 'enable'], self.mob_hunting_enable_var.get())
            self._set_nested_config(['automation', 'mob_hunting', 'search_pattern'], self.mob_hunting_search_pattern_var.get())
            self._set_nested_config(['automation', 'mob_hunting', 'move_distance'], int(self.mob_hunting_move_distance_var.get()))
            self._set_nested_config(['automation', 'mob_hunting', 'search_delay_ms'], int(self.mob_hunting_search_delay_ms_var.get()))
            self._set_nested_config(['automation', 'mob_hunting', 'max_search_time_ms'], int(self.mob_hunting_max_search_time_ms_var.get()))
            self._set_nested_config(['automation', 'mob_hunting', 'return_to_center'], self.mob_hunting_return_to_center_var.get())

            priority_targets_str = self.priority_targets_var.get()
            priority_targets_list = [s.strip() for s in priority_targets_str.split(',') if s.strip()]
            self._set_nested_config(['automation', 'priority_targets'], priority_targets_list)

            # --- Detection Behavior Tab ---
            if hasattr(self, 'detection_behavior_vars'): # Check if the UI elements were created
                for class_name, class_vars in self.detection_behavior_vars.items():
                    # Action
                    if 'action_var' in class_vars:
                        self._set_nested_config(['detection_behavior', class_name, 'action'], class_vars['action_var'].get())
                    # Log Detection
                    if 'log_var' in class_vars:
                        self._set_nested_config(['detection_behavior', class_name, 'log'], class_vars['log_var'].get())
                    # Max Distance
                    if 'max_distance_var' in class_vars:
                        try:
                            max_dist_val = int(class_vars['max_distance_var'].get())
                            self._set_nested_config(['detection_behavior', class_name, 'max_distance'], max_dist_val)
                        except ValueError:
                            messagebox.showwarning("Validation Error", f"Invalid Max Distance for {class_name}. Must be an integer.")
                            # Optionally, don't save this specific field or save a default

                    # Attack Delay
                    if 'attack_delay_ms_var' in class_vars:
                        try:
                            attack_delay_val = int(class_vars['attack_delay_ms_var'].get())
                            self._set_nested_config(['detection_behavior', class_name, 'attack_delay_ms'], attack_delay_val)
                        except ValueError:
                             messagebox.showwarning("Validation Error", f"Invalid Attack Delay for {class_name}. Must be an integer.")

                    # Interaction Delay
                    if 'interaction_delay_ms_var' in class_vars:
                        try:
                            interaction_delay_val = int(class_vars['interaction_delay_ms_var'].get())
                            self._set_nested_config(['detection_behavior', class_name, 'interaction_delay_ms'], interaction_delay_val)
                        except ValueError:
                             messagebox.showwarning("Validation Error", f"Invalid Interaction Delay for {class_name}. Must be an integer.")

            # --- Monitoring & Logging Tab ---
            if hasattr(self, 'log_level_var'): # Check if UI vars for this tab exist
                self._set_nested_config(['monitoring', 'log_level'], self.log_level_var.get())
                try:
                    max_log_size = int(self.max_log_size_mb_var.get())
                    self._set_nested_config(['monitoring', 'max_log_size_mb'], max_log_size)
                except ValueError:
                    messagebox.showwarning("Validation Error", "Invalid Max Log Size. Must be an integer.")
                self._set_nested_config(['monitoring', 'enable_performance_monitor'], self.enable_performance_monitor_var.get())


            # Ask where to save (or use current path)
            filepath = filedialog.asksaveasfilename(
                title="Save Configuration File",
                filetypes=(("YAML files", "*.yaml *.yml"), ("All files", "*.*")),
                initialfile="config.yaml",
                initialdir=os.path.dirname(self.config_manager.config_path),
                defaultextension=".yaml"
            )
            if filepath:
                self.config_manager.save_config(filepath) # save_config needs to be added to ConfigManager
                messagebox.showinfo("Config Saved", f"Configuration saved successfully to\n{filepath}")

        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid input for a field: {e}. Please check numeric fields.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {e}")


if __name__ == '__main__':
    app = App()
    app.mainloop()


    def _create_controls_tab(self):
        self.tab_controls = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_controls, text="Controls")

        # --- UI Variables for Controls Tab ---
        # General Keys
        self.pickup_key_var = tk.StringVar()
        self.interact_key_var = tk.StringVar()
        self.attack_key_var = tk.StringVar()
        self.attack_method_var = tk.StringVar()
        # Movement Keys
        self.move_left_var = tk.StringVar()
        self.move_right_var = tk.StringVar()
        self.move_jump_var = tk.StringVar()
        self.move_up_var = tk.StringVar()
        self.move_down_var = tk.StringVar()
        # Skill & System Keys
        self.skill1_key_var = tk.StringVar()
        self.skill2_key_var = tk.StringVar()
        self.skill3_key_var = tk.StringVar()
        self.skill4_key_var = tk.StringVar()
        self.potion_key_var = tk.StringVar()
        self.inventory_key_var = tk.StringVar()
        self.status_key_var = tk.StringVar()
        self.chat_key_var = tk.StringVar()

        # --- Layout ---
        tab_content = ttk.Frame(self.tab_controls)
        tab_content.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # General Keys Section
        general_keys_frame = ttk.LabelFrame(tab_content, text="General Keys")
        general_keys_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(general_keys_frame, text="Pickup Key:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(general_keys_frame, textvariable=self.pickup_key_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(general_keys_frame, text="Interact Key:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(general_keys_frame, textvariable=self.interact_key_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(general_keys_frame, text="Attack Key:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(general_keys_frame, textvariable=self.attack_key_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(general_keys_frame, text="Attack Method:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Combobox(general_keys_frame, textvariable=self.attack_method_var, values=["key", "click"]).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        general_keys_frame.columnconfigure(1, weight=1)

        # Movement Keys Section
        movement_keys_frame = ttk.LabelFrame(tab_content, text="Movement Keys")
        movement_keys_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(movement_keys_frame, text="Left:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(movement_keys_frame, textvariable=self.move_left_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(movement_keys_frame, text="Right:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(movement_keys_frame, textvariable=self.move_right_var).grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(movement_keys_frame, text="Jump:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(movement_keys_frame, textvariable=self.move_jump_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(movement_keys_frame, text="Up:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(movement_keys_frame, textvariable=self.move_up_var).grid(row=1, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(movement_keys_frame, text="Down:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(movement_keys_frame, textvariable=self.move_down_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        movement_keys_frame.columnconfigure(1, weight=1)
        movement_keys_frame.columnconfigure(3, weight=1)

        # Skill & System Keys Section
        skill_sys_frame = ttk.LabelFrame(tab_content, text="Skill & System Keys")
        skill_sys_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(skill_sys_frame, text="Skill 1:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.skill1_key_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Skill 2:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.skill2_key_var).grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Skill 3:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.skill3_key_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Skill 4:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.skill4_key_var).grid(row=1, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Potion:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.potion_key_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(skill_sys_frame, text="Inventory:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.inventory_key_var).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Status:").grid(row=3, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.status_key_var).grid(row=3, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(skill_sys_frame, text="Chat:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(skill_sys_frame, textvariable=self.chat_key_var).grid(row=4, column=1, padx=5, pady=2, sticky="ew")

        skill_sys_frame.columnconfigure(1, weight=1)
        skill_sys_frame.columnconfigure(3, weight=1)

        tab_content.columnconfigure(0, weight=1) # Allow content to expand

    def _create_mob_hunting_tab(self):
        self.tab_mob_hunting = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mob_hunting, text="Mob Hunting & Priority")

        # --- UI Variables for Mob Hunting Tab ---
        self.mob_hunting_enable_var = tk.BooleanVar()
        self.mob_hunting_search_pattern_var = tk.StringVar()
        self.mob_hunting_move_distance_var = tk.StringVar() # Kept as string for Entry
        self.mob_hunting_search_delay_ms_var = tk.StringVar()
        self.mob_hunting_max_search_time_ms_var = tk.StringVar()
        self.mob_hunting_return_to_center_var = tk.BooleanVar()
        self.priority_targets_var = tk.StringVar()

        # --- Layout ---
        tab_content = ttk.Frame(self.tab_mob_hunting)
        tab_content.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Mob Hunting Section
        mob_hunting_frame = ttk.LabelFrame(tab_content, text="Mob Hunting")
        mob_hunting_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Checkbutton(mob_hunting_frame, text="Enable Mob Hunting", variable=self.mob_hunting_enable_var).grid(row=0, column=0, padx=5, pady=2, sticky="w", columnspan=2)

        ttk.Label(mob_hunting_frame, text="Search Pattern:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Combobox(mob_hunting_frame, textvariable=self.mob_hunting_search_pattern_var, values=["horizontal", "vertical", "random"]).grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(mob_hunting_frame, text="Move Distance (conceptual):").grid(row=2, column=0, padx=5, pady=2, sticky="w") # In config: automation.mob_hunting.move_distance (but it's more like duration_ms now in bot)
        ttk.Entry(mob_hunting_frame, textvariable=self.mob_hunting_move_distance_var).grid(row=2, column=1, padx=5, pady=2, sticky="ew") # This might need to be re-evaluated based on bot's needs

        ttk.Label(mob_hunting_frame, text="Search Delay (ms):").grid(row=3, column=0, padx=5, pady=2, sticky="w") # In config: automation.mob_hunting.search_delay_ms
        ttk.Entry(mob_hunting_frame, textvariable=self.mob_hunting_search_delay_ms_var).grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(mob_hunting_frame, text="Max Search Time (ms):").grid(row=4, column=0, padx=5, pady=2, sticky="w") # In config: automation.mob_hunting.max_search_time_ms
        ttk.Entry(mob_hunting_frame, textvariable=self.mob_hunting_max_search_time_ms_var).grid(row=4, column=1, padx=5, pady=2, sticky="ew")

        ttk.Checkbutton(mob_hunting_frame, text="Return to Center After Search", variable=self.mob_hunting_return_to_center_var).grid(row=5, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        mob_hunting_frame.columnconfigure(1, weight=1)

        # Priority Targets Section
        priority_targets_frame = ttk.LabelFrame(tab_content, text="Priority Targets")
        priority_targets_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(priority_targets_frame, text="Targets (comma-separated, order matters):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(priority_targets_frame, textvariable=self.priority_targets_var, width=60).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        priority_targets_frame.columnconfigure(1, weight=1)

        tab_content.columnconfigure(0, weight=1) # Allow content to expand

    def _create_control_panel(self):
        control_frame = ttk.LabelFrame(self, text="Bot Controls")
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5,10)) # pady top=5, bottom=10

        self.start_button = ttk.Button(control_frame, text="Start Automation", command=self._start_bot, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(control_frame, text="Stop Automation", command=self._stop_bot, width=20)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.pause_resume_button = ttk.Button(control_frame, text="Pause/Resume", command=self._toggle_pause_resume_bot, width=20)
        self.pause_resume_button.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Idle")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

    def _update_status(self, message: str):
        self.status_var.set(f"Status: {message}")

    def _update_button_states(self):
        if self.bot_state == "idle":
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(state=tk.DISABLED, text="Pause")
        elif self.bot_state == "running":
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_resume_button.config(state=tk.NORMAL, text="Pause")
        elif self.bot_state == "paused":
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL) # Can still stop while paused
            self.pause_resume_button.config(state=tk.NORMAL, text="Resume")
        elif self.bot_state == "stopping":
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(state=tk.DISABLED)

        if not self.bot: # If bot failed to initialize
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_resume_button.config(state=tk.DISABLED)


    def _start_bot(self):
        if not self.bot:
            messagebox.showerror("Bot Error", "OptimizedMapleBot is not initialized.")
            return
        if self.bot_thread and self.bot_thread.is_alive():
            messagebox.showwarning("Bot Control", "Bot is already running.")
            return

        # Ensure current UI settings are saved to config, then bot reloads them
        self._save_config_to_file() # This saves to the file path in config_manager
        # The bot's start_automation now reloads config and applies settings

        show_preview_ui = self.show_preview_var.get()

        # The bot's start_automation method will use its internal config_manager
        # which is shared with this App instance.
        self.bot_thread = threading.Thread(target=self.bot.start_automation, args=(show_preview_ui,), daemon=True)
        self.bot_thread.start()

        self.bot_state = "running"
        self._update_button_states()
        self._update_status("Bot Running...")

    def _stop_bot(self):
        if not self.bot:
            messagebox.showerror("Bot Error", "OptimizedMapleBot is not initialized.")
            return

        if not self.bot_thread or not self.bot_thread.is_alive():
            # If thread is not alive, but state wasn't idle, reset it.
            if self.bot_state != "idle":
                 self._update_status("Bot was not running or already stopped.")
            self.bot_state = "idle"
            self._update_button_states()
            return

        self._update_status("Stopping Bot...")
        self.bot_state = "stopping" # Intermediate state
        self._update_button_states()

        self.bot.running = False # Signal the bot to stop its loop

        # Wait for the thread to finish, with a timeout
        # Important: The mainloop of Tkinter runs in the main thread.
        # Directly calling join() here would block the UI.
        # So, we can schedule a check.
        self.after(100, self._check_bot_thread_stopped)

    def _check_bot_thread_stopped(self):
        if self.bot_thread and self.bot_thread.is_alive():
            # If still alive, schedule another check
            self.after(100, self._check_bot_thread_stopped)
        else:
            # Thread has finished
            self.bot_thread = None
            self.bot_state = "idle"
            self._update_button_states()
            self._update_status("Bot Stopped.")
            messagebox.showinfo("Bot Control", "Automation stopped.")


    def _toggle_pause_resume_bot(self):
        if not self.bot:
            messagebox.showerror("Bot Error", "OptimizedMapleBot is not initialized.")
            return

        if not self.bot_thread or not self.bot_thread.is_alive() or self.bot_state == "stopping":
            messagebox.showwarning("Bot Control", "Bot is not running or is stopping.")
            return

        if self.bot_state == "running":
            self.bot.paused = True
            self.bot_state = "paused"
            self._update_status("Bot Paused.")
        elif self.bot_state == "paused":
            self.bot.paused = False
            self.bot_state = "running"
            self._update_status("Bot Resumed.")

        self._update_button_states()

    def _create_detection_behavior_tab(self):
        self.tab_detection_behavior = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_detection_behavior, text="Detection Behavior")

        # --- Canvas and Scrollbar for scrollable content ---
        canvas = tk.Canvas(self.tab_detection_behavior)
        scrollbar = ttk.Scrollbar(self.tab_detection_behavior, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # --- UI Variables for Detection Behavior Tab ---
        self.detection_behavior_vars = {} # Store vars like: self.detection_behavior_vars[class_name]['action_var']

        # Define classes. This list should ideally come from a more dynamic source or be comprehensive.
        # These are based on common object types in games.
        self.defined_detection_classes = self.config_manager.get('detection_behavior', {}).keys()
        if not self.defined_detection_classes: # Fallback if detection_behavior is empty or not in config
            self.defined_detection_classes = ['mob', 'item', 'npc', 'character', 'environment', 'ui_element']

        # Action types available for comboboxes
        self.action_types = ["ignore", "log_only", "attack", "pickup", "interact"]


        for class_name in self.defined_detection_classes:
            self._create_class_behavior_frame(scrollable_frame, class_name)

    def _create_class_behavior_frame(self, parent_frame, class_name: str):
        """Creates a Labelframe for configuring behavior for a specific detection class."""

        class_frame = ttk.LabelFrame(parent_frame, text=f"{class_name.capitalize()} Behavior")
        class_frame.pack(padx=10, pady=10, fill="x", expand=True)

        self.detection_behavior_vars.setdefault(class_name, {})

        # Action Combobox
        ttk.Label(class_frame, text="Action:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        action_var = tk.StringVar()
        self.detection_behavior_vars[class_name]['action_var'] = action_var
        ttk.Combobox(class_frame, textvariable=action_var, values=self.action_types, width=15).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Log Detection Checkbutton
        log_var = tk.BooleanVar()
        self.detection_behavior_vars[class_name]['log_var'] = log_var
        ttk.Checkbutton(class_frame, text="Log Detection", variable=log_var).grid(row=0, column=2, padx=10, pady=2, sticky="w")

        # Max Distance Entry
        ttk.Label(class_frame, text="Max Distance (px):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        max_distance_var = tk.StringVar()
        self.detection_behavior_vars[class_name]['max_distance_var'] = max_distance_var
        ttk.Entry(class_frame, textvariable=max_distance_var, width=10).grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Conditional delay fields based on class or typical actions
        if class_name in ['mob', 'boss']: # Classes that typically attack
            ttk.Label(class_frame, text="Attack Delay (ms):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            attack_delay_ms_var = tk.StringVar()
            self.detection_behavior_vars[class_name]['attack_delay_ms_var'] = attack_delay_ms_var
            ttk.Entry(class_frame, textvariable=attack_delay_ms_var, width=10).grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        if class_name in ['npc']: # Classes that typically interact
            ttk.Label(class_frame, text="Interaction Delay (ms):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            interaction_delay_ms_var = tk.StringVar()
            self.detection_behavior_vars[class_name]['interaction_delay_ms_var'] = interaction_delay_ms_var
            ttk.Entry(class_frame, textvariable=interaction_delay_ms_var, width=10).grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        class_frame.columnconfigure(1, weight=1)
        class_frame.columnconfigure(2, weight=0) # Log checkbox column

    def _create_monitoring_logging_tab(self):
        self.tab_monitoring_logging = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_monitoring_logging, text="Monitoring & Logging")

        # --- UI Variables ---
        self.log_level_var = tk.StringVar()
        self.max_log_size_mb_var = tk.StringVar()
        self.enable_performance_monitor_var = tk.BooleanVar()

        tab_content = ttk.Frame(self.tab_monitoring_logging)
        tab_content.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Logging Section
        logging_frame = ttk.LabelFrame(tab_content, text="Logging")
        logging_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(logging_frame, text="Log Level:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Combobox(logging_frame, textvariable=self.log_level_var, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(logging_frame, text="Max Log File Size (MB):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(logging_frame, textvariable=self.max_log_size_mb_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        logging_frame.columnconfigure(1, weight=1)

        # Performance Monitoring Section
        performance_frame = ttk.LabelFrame(tab_content, text="Performance Monitoring")
        performance_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Checkbutton(performance_frame, text="Enable/Display Performance Metrics in Preview", variable=self.enable_performance_monitor_var).grid(row=0, column=0, padx=5, pady=2, sticky="w", columnspan=2)

        tab_content.columnconfigure(0, weight=1)

    def _create_log_display(self):
        log_frame = ttk.LabelFrame(self, text="Logs")
        # Pack below tabs, above control panel and status bar
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,0))

        self.log_text_widget = ScrolledText(log_frame, state='disabled', height=10, wrap=tk.WORD)
        self.log_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _setup_logging(self):
        # Create and configure the custom TextHandler
        text_handler = TextHandler(self.log_text_widget)
        # You can set a specific format for the log messages in the UI
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)

        # Add this handler to the root logger to capture all logs
        # Or, if auto.py uses a specific logger like logging.getLogger('auto'), add to that.
        # Adding to root is generally fine if auto.py's logger propagates.
        root_logger = logging.getLogger()
        root_logger.addHandler(text_handler)
        # Set the level for the root logger (or the specific logger if you target one)
        # This determines the minimum severity of messages that will be passed to handlers.
        # The handler itself can also have a level if you want it to be more restrictive.
        # The effective level will be the more restrictive of the logger and handler.
        # Getting log level from config for the TextHandler
        log_level_str = self.config_manager.get('monitoring.log_level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        root_logger.setLevel(log_level) # Set root logger to a fairly permissive level initially
        text_handler.setLevel(log_level) # Set handler level based on config

        # Example: Log a message to test the UI handler
        logging.info("GUI logging initialized.")