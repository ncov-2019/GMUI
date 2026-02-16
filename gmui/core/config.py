import os
import json
import sys
from typing import Dict, Any
from PyQt5.QtWidgets import QApplication

from .notice import show_first_run_notice

class ConfigManager:
    """配置"""
    def __init__(self, config_filename: str = "config.json"):
        if hasattr(sys, '_MEIPASS'):
            self.program_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.program_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.program_dir, config_filename)
        self.DEFAULT_CONFIG = self._get_default_config()
        self.config: Dict[str, Any] = self.load_config()

    def _get_default_config(self) -> dict:
        """默认配置"""
        app = QApplication.instance() or QApplication(sys.argv)
        screen = app.primaryScreen()
        size = screen.size()
        edge = min(size.width(), size.height())
        min_edge = max(500,edge // 2)
        input_width = max(100, min(min_edge - 100, 300))
        input_x = (size.width() - min_edge) // 2 + (min_edge - input_width) // 2
        input_y = (size.height() - min_edge) // 2 + min_edge - 40
        # 默认配置
        return {
            "spine": "4.1",
            "skel": False,
            "atlas": False,
            "alpha": 0,
            "window_size": (min_edge, min_edge),
            "window_pos": ((size.width() - min_edge) // 2, (size.height() - min_edge) // 2),
            "input_pos": (input_x, input_y),
            "window_opacity": 1.0,
            "page_width": 0,
            "page_height": 0,
            "page_scale": 1.0, 
            "anim_idle": False,
            "input_opacity": 1,
            "lyrics_pos": (0, 0),
            "lyrics_scale": 1,
            "lyrics_opacity": 1,
            "state":0
        }

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                return {**self.DEFAULT_CONFIG, **loaded_config}
            self.save_config(self.DEFAULT_CONFIG)
            show_first_run_notice()
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config_data: Dict[str, Any] = None) -> bool:
        """保存配置文件"""
        try:
            save_data = config_data or self.config
            os.makedirs(self.program_dir, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            return False

    def update_config(self, key: str, value: Any) -> bool:
        """更新/新增"""
        self.config[key] = value
        return self.save_config()

    def delete_config(self, key: str) -> bool:
        """删除指定key """
        if key in self.config:
            del self.config[key]
            return self.save_config()
        return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    