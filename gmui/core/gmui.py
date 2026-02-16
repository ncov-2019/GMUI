import os
import shutil
import random
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox, QVBoxLayout, QApplication,
    QSlider, QHBoxLayout, QComboBox, QCheckBox, QWidget,
    QScrollArea,QGridLayout,QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase,QIcon,QCloseEvent,QPixmap
from .url import get_exe_dir,get_exe_url
from .alert import error,three_choice

class GMUIConfigDialog(QDialog):
    """优化后的GMUI配置面板"""
    # 定义信号用于通知主窗口更新配置
    window_opacity_changed = pyqtSignal(float)
    window_size_changed = pyqtSignal(int, int)
    page_position_changed = pyqtSignal(int, int)
    page_scale_changed = pyqtSignal(float)
    animation_config_changed = pyqtSignal(dict)
    SPINE_TYPES = ["3.8", "4.1", "4.2"]
    ANIMATION_TYPES = {
        "move": "开始拖拽",
        "moveend": "结束拖拽",
        "inwindow": "窗口悬停",
        "outwindow": "离开窗口",
        "pet": "想被摸",
        "petend": "摸摸",
        "sleep": "该睡觉了",
        "rest": "休息一下",
        "click": "点击",

        "keyboard1": "快捷键动作1",
        "keyboard2": "快捷键动作2",
        "keyboard3": "快捷键动作3",
    }
    TIR_TYPES = {# 状态1：只显示条件文本框 状态2：只显示台词相关功能 
        "blink": ("眨眼", "每次动画间隔 [ 秒 ]", 1),
        "speak": ("说话", "每 [ 整数 ] 字播放一遍动画", 1),
        "0000": None,
        "move": ("开始拖拽", "", 2),
        "moveend": ("结束拖拽", "", 2),
        "click": ("点击", "", 2),
        "0001": None,
        "inwindow": ("窗口悬停", "悬停 [ 整数秒 ] 后触发", 3),
        "outwindow": ("离开窗口", "", 2),
        "0002": None,
        "pet": ("想被摸", "无动作 [ 整数秒 ] 后触发", 3),
        "petend": ("摸摸", "", 2),
        "0003": None,
        "sleep": ("该睡觉了", "到达24小时制 [ 时:分 ] 后触发", 3),
        "rest": ("休息一下", "运行 [ 整数分钟 ] 后触发", 3),
        "0004": None,
        "keyboard": ("切换维度", "快捷键 [ 键+键 ] 默认 alt+`", 1),
        "keyboard1": ("快捷键动作1", "快捷键 [ 键+键 ] ", 3),
        "keyboard2": ("快捷键动作2", "快捷键 [ 键+键 ] ", 3),
        "keyboard3": ("快捷键动作3", "快捷键 [ 键+键 ] ", 3),
        #
    }


    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.parent_window = parent
        self.animation_names = []
        self.slot_widgets = {} 
        self.slot_grid_layout = None  
        self.custom_scroll_area = None

        self.action_widgets = {}
        self.dialogue_groupboxes = {}

        self.init_ui()
        self.load_animation_names_from_config()
        self.load_config_to_ui() 


    # ========== 基本文件 ==========
    def on_copy_file(self, src_path):
        """复制assets目录，返回文件名"""
        try:
            if not os.path.exists(src_path):
                return ""
            file_name = os.path.basename(src_path)
            dest_path = os.path.join(get_exe_url(),"assets",file_name)
            shutil.copy2(src_path, dest_path)
            return file_name
        except Exception:
            error(self,"获取文件失败，目标文件可能正被使用")
            pass

    def on_select_skel_file(self):
        """选择动画"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择skel或json", "", "高维信息 (*.skel *.json);;任何 (*.*)"
        )
        if file_path:
            file_name = self.on_copy_file(file_path)
            if file_name:
                self.anim_file_edit.setText(file_name)
                self.on_select_atlas(file_path)

    def on_select_atlas(self, anim_file_path):
        """自动选择图描述"""
        try:
            anim_dir = os.path.dirname(anim_file_path)
            anim_base_name = os.path.splitext(os.path.basename(anim_file_path))[0]
            atlas_file_path = os.path.join(anim_dir, f"{anim_base_name}.atlas")
            if os.path.exists(atlas_file_path):
                atlas_file_name = self.on_copy_file(atlas_file_path)
                if atlas_file_name and hasattr(self, 'cut_file_edit'):
                    self.cut_file_edit.setText(atlas_file_name)
                self.on_png_from_atlas(atlas_file_path, anim_dir)
        except Exception:
            error(self,"尝试关联.atlas时发生问题")
            pass

    def on_png_from_atlas(self, atlas_file_path, source_dir):
        """自动选择图"""
        try:
            with open(atlas_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            png_files = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.endswith('.png'):
                    png_name = os.path.basename(line)
                    png_files.append(png_name)
            for png_name in png_files:
                png_src_path = os.path.join(source_dir, png_name)
                if os.path.exists(png_src_path):
                    self.on_copy_file(png_src_path)
        except Exception as e:
            error(self,"尝试关联.png时发生问题")
            pass

    def on_select_atlas_file(self):
        """选择图描述"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择atlas", "", "高维碎片映射信息 (*.atlas);;任何 (*.*)"
        )
        if file_path:
            file_name = self.on_copy_file(file_path)
            if file_name:
                self.cut_file_edit.setText(file_name)

    def on_select_png_file(self):
        """选择图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择png", "", "高维碎片 (*.png);;任何 (*.*)"
        )
        if file_path:
            self.on_copy_file(file_path)

    def on_open_assets(self):
        """打开目录"""
        os.startfile(os.path.join(get_exe_url(), "assets"))

    # ========== 基本动画 ==========
    def load_animation_names_from_config(self):
        """加载动画名称"""
        anim_config_val = self.config.get("anim", None) if self.config else None
        if anim_config_val is not None:
            anim_names = anim_config_val
            if isinstance(anim_names, str):
                self.animation_names = [name.strip() for name in anim_names.split(',') if name.strip()]
            elif isinstance(anim_names, list):
                self.animation_names = [str(n) for n in anim_names if n]
            else:
                self.animation_names = []
            self.update_all_anim_combos()

    def update_all_anim_combos(self):
        """更新下拉框"""
        combos_to_update = [self.default_anim_combo]
        combos_to_update.append(self.speak_anim_combo)
        combos_to_update.append(self.blink_anim_combo)
        
        # 更新动态动画部分的所有下拉框
        for widget_info in self.anim_widgets.values():
            combos_to_update.append(widget_info["main_combo"])
            for row in widget_info["extra_rows"]:
                combos_to_update.append(row["combo"])

        for combo in combos_to_update:
            combo.clear()
            combo.addItems(self.animation_names)

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowFlags(
            (self.windowFlags() | Qt.WindowStaysOnTopHint)
            & ~Qt.WindowContextHelpButtonHint
        )
        self.setWindowTitle("GMUI")
        self.setModal(True)
    
        self.resize(700,720)
        self.setWindowIcon(QIcon(os.path.join(get_exe_dir(), "assets/gm00.ico")))
        screen_geo = QApplication.desktop().screenGeometry()
        self.move(
            (screen_geo.width() - self.width()) // 2,
            (screen_geo.height() - self.height()) // 2
        )
        self.setStyleSheet("""
            QMainWindow, QDialog, QWidget {
                background-color: #d0d1d8;
            }
            QGroupBox {
                border: 1px solid #999fa7;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 4px 5px 0 5px;
            }
            QLabel {
                color: #080c15;
            }
            QPushButton {
                background-color: #080c15;
                padding-top: 4px;
                color: #d0d1d8;
                border: none;
                padding: 6px 10px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #2d3038;
            }
            QPushButton:pressed {
                background-color: #1c1c1e;
            }
            QSlider::groove:horizontal {
                background: #d0d1d8;
                height: 6px;
                border: 1px solid #999fa7;
                border-radius: 0px;
            }
            QSlider::handle:horizontal {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.5,
                    fx: 0.5, fy: 0.5,
                    stop: 0.4 #d0d1d8,
                    stop: 0.5 #999fa7,
                    stop: 0.6 #d0d1d8
                );
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border: 1px solid #080c15;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.5,
                    fx: 0.5, fy: 0.5,
                    stop: 0.4 #d0d1d8,
                    stop: 0.5 #999fa7,
                    stop: 0.6 #33ccda
                );
            }
            QComboBox {
                border: 1px solid #999fa7;
                border-radius: 2px;
                padding: 3px 5px;
                background: #e8e8f1;
            }
            QComboBox:focus {
                border: 1px solid #33ccda;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 10px;
                margin: 1px 15px;
                border: 1px solid #999fa7;
            }
            QComboBox QAbstractItemView {
                background-color: #e8e8f1;
                border: 1px solid #c83039;
                selection-background-color: #bcc1c8;
                selection-color: #080c15;
                show-decoration-selected: 0;
                outline: 0px;
                min-width: 200px;
            }
            QComboBox QAbstractItemView::item {
                padding: 15px;
                border-bottom: 1px solid #999fa7;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:last-child {
                border-bottom: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 1px solid #080c15;
            }
            QCheckBox::indicator:checked {
                background-color: #3694a7;
            }
            QLineEdit {
                border: 1px solid #999fa7;
                border-radius: 2px;
                padding: 3px 5px;
                background: #e8e8f1;
            }
            QLineEdit:focus {
                border: 1px solid #33ccda;
            }
            QLineEdit[echoMode="PasswordEchoOnEdit"] {
                lineedit-password-character: "♡";
            }
            QLineEdit[echoMode="Password"] {
                lineedit-password-character: "♡";
            }
            QScrollArea {
                border: 1px solid #999fa7;
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(240, 240, 240, 0.3);
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(150, 150, 150, 0.6);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(120, 120, 120, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background-color: rgba(240, 240, 240, 0.3);
                height: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(150, 150, 150, 0.6);
                border-radius: 3px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(120, 120, 120, 0.8);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        font_path = os.path.join(get_exe_dir(), "assets/SourceHanSansSC.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font = QFont(font_families[0], 10)
                    self.setFont(font)
                    QApplication.setFont(font)

        button_font_path = os.path.join(get_exe_dir(), "assets/FZYaSong.ttf")
        if os.path.exists(button_font_path):
            font_id = QFontDatabase.addApplicationFont(button_font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_name = font_families[0]
                    button_font_style = """
                    QPushButton {{
                        font-family: "{font_name}";
                        font-size: 14px;
                    }}           
                    QGroupBox {{
                        font-family: "{font_name}";
                    }}
                    """.format(font_name=font_name)
                    current_style = self.styleSheet()
                    self.setStyleSheet(current_style + button_font_style)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll_area)

        # ========== 1.基本配置 ==========
        basic_group = QGroupBox("基本配置")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(15)

        # 1.1 选择版本
        self.spine_version_combo = QComboBox()
        self.spine_version_combo.addItems(self.SPINE_TYPES)
        basic_layout.addRow(QLabel("spine版本："), self.spine_version_combo)

        # 1.2 动画文件
        anim_file_widget = QWidget()
        anim_file_h_layout = QHBoxLayout(anim_file_widget)
        anim_file_h_layout.setContentsMargins(0, 0, 0, 0)
        anim_file_h_layout.setSpacing(10)

        self.anim_file_edit = QLineEdit()
        anim_select_btn = QPushButton("选择文件")
        anim_select_btn.clicked.connect(self.on_select_skel_file)
        anim_select_btn.setMinimumWidth(90)

        self.premult_checkbox = QCheckBox("预乘")
        anim_file_h_layout.addWidget(self.anim_file_edit)
        anim_file_h_layout.addWidget(self.premult_checkbox)
        anim_file_h_layout.addWidget(anim_select_btn)
        self.anim_file_edit.setSizePolicy(
            self.anim_file_edit.sizePolicy().Expanding,
            self.anim_file_edit.sizePolicy().Fixed
        )
        basic_layout.addRow(QLabel(".skel："), anim_file_widget)

        # 1.3 切图文件
        cut_file_widget = QWidget()
        cut_file_h_layout = QHBoxLayout(cut_file_widget)
        cut_file_h_layout.setContentsMargins(0, 0, 0, 0)
        cut_file_h_layout.setSpacing(10)
        
        self.cut_file_edit = QLineEdit()
        cut_select_btn = QPushButton("选择文件")
        cut_select_btn.setMinimumWidth(90)
        cut_select_btn.clicked.connect(self.on_select_atlas_file)
        
        cut_file_h_layout.addWidget(self.cut_file_edit)
        cut_file_h_layout.addWidget(cut_select_btn)
        self.cut_file_edit.setSizePolicy(
            self.cut_file_edit.sizePolicy().Expanding,
            self.cut_file_edit.sizePolicy().Fixed
        )
        basic_layout.addRow(QLabel(".atlas："), cut_file_widget)

        # 1.4 图集
        atlas_widget = QWidget()
        atlas_h_layout = QHBoxLayout(atlas_widget)
        atlas_h_layout.setContentsMargins(0, 0, 0, 0)
        atlas_h_layout.setSpacing(10)
        
        atlas_select_btn = QPushButton("选择文件")
        atlas_select_btn.clicked.connect(self.on_select_png_file)
        atlas_open_btn = QPushButton("打开存放位置")
        atlas_open_btn.setMinimumWidth(90)
        atlas_open_btn.clicked.connect(self.on_open_assets)
        
        atlas_h_layout.addWidget(atlas_select_btn)
        atlas_h_layout.addWidget(atlas_open_btn)
        atlas_select_btn.setSizePolicy(
            atlas_select_btn.sizePolicy().Expanding,
            atlas_select_btn.sizePolicy().Fixed
        )
        basic_layout.addRow(QLabel(".png："), atlas_widget)

        restart_btn = QPushButton("二维展开")
        restart_btn.clicked.connect(self.reload_spine_html)
        basic_layout.addRow(restart_btn)
        main_layout.addWidget(basic_group)

        # ========== 2. 窗口配置 ==========
        window_group = QGroupBox("窗口")
        window_layout = QFormLayout(window_group)
        window_layout.setSpacing(15)

        # 2.1 窗口大小
        self.window_size_slider = QSlider(Qt.Horizontal)
        self.window_size_slider.setRange(100, 2560) 
        self.window_size_slider.setSingleStep(10)
        self.window_size_slider.setValue(1000) 
        self.window_size_slider.valueChanged.connect(self.on_window_size_change)
        self.window_size_label = QLabel("1000 × 1000")
        window_size_widget = QWidget()
        window_size_h_layout = QHBoxLayout(window_size_widget)
        window_size_h_layout.addWidget(self.window_size_slider)
        window_size_h_layout.addWidget(self.window_size_label)
        window_layout.addRow(QLabel("大小："), window_size_widget)

        # 2.2 窗口透明度
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setSingleStep(1)
        self.opacity_slider.setValue(100) 
        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        self.opacity_label = QLabel("1.0")
        opacity_widget = QWidget()
        opacity_h_layout = QHBoxLayout(opacity_widget)
        opacity_h_layout.addWidget(self.opacity_slider)
        opacity_h_layout.addWidget(self.opacity_label)
        window_layout.addRow(QLabel("透明度："), opacity_widget)

        # 2.3 重置按钮
        window_reset_btn = QPushButton("重置")
        window_reset_btn.clicked.connect(self.reset_window_config)
        window_layout.addRow(window_reset_btn)

        main_layout.addWidget(window_group)

        # ========== 3. 页面配置 ==========
        page_group = QGroupBox("二维展开")
        page_layout = QFormLayout(page_group)
        page_layout.setSpacing(15)

        # 3.1 页面高度
        self.page_height_slider = QSlider(Qt.Horizontal)
        self.page_height_slider.setRange(-10000, 10000)
        self.page_height_slider.setSingleStep(10)
        self.page_height_slider.setValue(0)
        self.page_height_slider.valueChanged.connect(self.on_page_position_change)
        self.page_height_label = QLabel("0")
        page_height_widget = QWidget()
        page_height_h_layout = QHBoxLayout(page_height_widget)
        page_height_h_layout.addWidget(self.page_height_slider)
        page_height_h_layout.addWidget(self.page_height_label)
        page_layout.addRow(QLabel("竖向位置："), page_height_widget)

        # 3.2 页面宽度
        self.page_width_slider = QSlider(Qt.Horizontal)
        self.page_width_slider.setRange(-10000, 10000)
        self.page_width_slider.setSingleStep(10)
        self.page_width_slider.setValue(0)
        self.page_width_slider.valueChanged.connect(self.on_page_position_change)
        self.page_width_label = QLabel("0")
        page_width_widget = QWidget()
        page_width_h_layout = QHBoxLayout(page_width_widget)
        page_width_h_layout.addWidget(self.page_width_slider)
        page_width_h_layout.addWidget(self.page_width_label)
        page_layout.addRow(QLabel("横向位置："), page_width_widget)

        # 3.3 页面大小
        self.page_scale_slider = QSlider(Qt.Horizontal)
        self.page_scale_slider.setRange(1, 1000)  # 0.01-10
        self.page_scale_slider.setSingleStep(1)
        self.page_scale_slider.setValue(100)  # 默认1.0倍
        self.page_scale_slider.valueChanged.connect(self.on_page_scale_change)
        self.page_scale_label = QLabel("1.0")
        page_scale_widget = QWidget()
        page_scale_h_layout = QHBoxLayout(page_scale_widget)
        page_scale_h_layout.addWidget(self.page_scale_slider)
        page_scale_h_layout.addWidget(self.page_scale_label)
        page_layout.addRow(QLabel("大小："), page_scale_widget)

        # 3.4 重置按钮
        page_reset_btn = QPushButton("重置")
        page_reset_btn.clicked.connect(self.reset_page_config)
        page_layout.addRow(page_reset_btn)

        main_layout.addWidget(page_group)

        # ========== 4. 字幕 ==========
        api_group = QGroupBox("外置字幕")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(15)

        self.api_opacity_slider = QSlider(Qt.Horizontal)
        self.api_opacity_slider.setRange(1, 100)
        self.api_opacity_slider.setSingleStep(1)
        self.api_opacity_slider.setValue(100)
        self.api_opacity_slider.valueChanged.connect(self.on_api_opacity_change)
        self.api_opacity_label = QLabel("1.00")
        api_opacity_widget = QWidget()
        api_opacity_h_layout = QHBoxLayout(api_opacity_widget)
        api_opacity_h_layout.addWidget(self.api_opacity_slider)
        api_opacity_h_layout.addWidget(self.api_opacity_label)
        api_layout.addRow(QLabel("透明度："), api_opacity_widget)

        main_layout.addWidget(api_group)

        # ========== 字幕配置 ==========
        lyrics_group = QGroupBox("内嵌字幕")
        lyrics_layout = QFormLayout(lyrics_group)
        lyrics_layout.setSpacing(15)

        # 5.1 字幕竖向位置
        self.lyrics_height_slider = QSlider(Qt.Horizontal)
        self.lyrics_height_slider.setRange(-100, 100)
        self.lyrics_height_slider.setSingleStep(1)
        self.lyrics_height_slider.setValue(0)
        self.lyrics_height_slider.valueChanged.connect(self.on_lyrics_position_change)
        self.lyrics_height_label = QLabel("0")
        lyrics_height_widget = QWidget()
        lyrics_height_h_layout = QHBoxLayout(lyrics_height_widget)
        lyrics_height_h_layout.addWidget(self.lyrics_height_slider)
        lyrics_height_h_layout.addWidget(self.lyrics_height_label)
        lyrics_layout.addRow(QLabel("竖向位置："), lyrics_height_widget)

        # 5.2 字幕横向位置
        self.lyrics_width_slider = QSlider(Qt.Horizontal)
        self.lyrics_width_slider.setRange(-100, 100)
        self.lyrics_width_slider.setSingleStep(1)
        self.lyrics_width_slider.setValue(0)
        self.lyrics_width_slider.valueChanged.connect(self.on_lyrics_position_change)
        self.lyrics_width_label = QLabel("0")
        lyrics_width_widget = QWidget()
        lyrics_width_h_layout = QHBoxLayout(lyrics_width_widget)
        lyrics_width_h_layout.addWidget(self.lyrics_width_slider)
        lyrics_width_h_layout.addWidget(self.lyrics_width_label)
        lyrics_layout.addRow(QLabel("横向位置："), lyrics_width_widget)

        # 5.3 字幕大小
        self.lyrics_scale_slider = QSlider(Qt.Horizontal)
        self.lyrics_scale_slider.setRange(1, 500)  # 0.01-5.00
        self.lyrics_scale_slider.setSingleStep(1)
        self.lyrics_scale_slider.setValue(100)  # 默认1.0倍
        self.lyrics_scale_slider.valueChanged.connect(self.on_lyrics_scale_change)
        self.lyrics_scale_label = QLabel("1.00")
        lyrics_scale_widget = QWidget()
        lyrics_scale_h_layout = QHBoxLayout(lyrics_scale_widget)
        lyrics_scale_h_layout.addWidget(self.lyrics_scale_slider)
        lyrics_scale_h_layout.addWidget(self.lyrics_scale_label)
        lyrics_layout.addRow(QLabel("大小："), lyrics_scale_widget)

        # 5.4 字幕透明度
        self.lyrics_opacity_slider = QSlider(Qt.Horizontal)
        self.lyrics_opacity_slider.setRange(0, 100)  # 0.00-1.00
        self.lyrics_opacity_slider.setSingleStep(1)
        self.lyrics_opacity_slider.setValue(100)  # 默认1.0
        self.lyrics_opacity_slider.valueChanged.connect(self.on_lyrics_opacity_change)
        self.lyrics_opacity_label = QLabel("1.00")
        lyrics_opacity_widget = QWidget()
        lyrics_opacity_h_layout = QHBoxLayout(lyrics_opacity_widget)
        lyrics_opacity_h_layout.addWidget(self.lyrics_opacity_slider)
        lyrics_opacity_h_layout.addWidget(self.lyrics_opacity_label)
        lyrics_layout.addRow(QLabel("透明度："), lyrics_opacity_widget)

        # 5.5 重置按钮
        lyrics_reset_btn = QPushButton("重置")
        lyrics_reset_btn.clicked.connect(self.reset_lyrics_config)
        lyrics_layout.addRow(lyrics_reset_btn)

        main_layout.addWidget(lyrics_group)

        # ========== 5. 动画配置 ==========
        animation_group = QGroupBox("动作")
        animation_layout = QFormLayout(animation_group)
        animation_layout.setSpacing(15)

        # 5.1 默认动画
        self.default_anim_combo = QComboBox()
        self.default_anim_combo.setMinimumWidth(200)
        self.default_anim_combo.addItems(self.animation_names)
        animation_layout.addRow(QLabel("默认动作："), self.default_anim_combo)

        # 5.2 说话动画
        speak_anim_widget = QWidget()
        speak_anim_layout = QHBoxLayout(speak_anim_widget)
        self.speak_anim_combo = QComboBox()
        self.speak_anim_combo.setMinimumWidth(400)
        self.speak_anim_combo.addItems(self.animation_names)
        self.speak_anim_combo.setEnabled(False)
        self.speak_anim_check = QCheckBox("启用")
        self.speak_anim_check.stateChanged.connect(
            lambda state: self.speak_anim_combo.setEnabled(state == Qt.Checked)
        )
        speak_anim_layout.addWidget(self.speak_anim_combo)
        speak_anim_layout.addWidget(self.speak_anim_check)
        speak_anim_layout.addStretch()
        animation_layout.addRow(QLabel("说话动作："), speak_anim_widget)

        # 5.3 眨眼动画
        blink_anim_widget = QWidget()
        blink_anim_layout = QHBoxLayout(blink_anim_widget)
        self.blink_anim_combo = QComboBox()
        self.blink_anim_combo.setMinimumWidth(400)
        self.blink_anim_combo.addItems(self.animation_names)
        self.blink_anim_combo.setEnabled(False)
        self.blink_anim_check = QCheckBox("启用")
        self.blink_anim_check.stateChanged.connect(
            lambda state: self.blink_anim_combo.setEnabled(state == Qt.Checked)
        )
        blink_anim_layout.addWidget(self.blink_anim_combo)
        blink_anim_layout.addWidget(self.blink_anim_check)
        blink_anim_layout.addStretch()
        animation_layout.addRow(QLabel("眨眼动作："), blink_anim_widget)

        # 5.4 动态动画配置
        self.anim_widgets = {}
        for key, label_text in self.ANIMATION_TYPES.items():
            widget_info = self.create_animation_row(label_text, key)
            self.anim_widgets[key] = widget_info
            animation_layout.addRow(QLabel(f"{label_text}："), widget_info["widget"])
        
        main_layout.addWidget(animation_group)

        # ==========6 触发机制 ==========
        action_group = QGroupBox("台词与触发")
        action_layout = QFormLayout(action_group)
        action_layout.setSpacing(15)

        for tir_key, tir_info in self.TIR_TYPES.items():
            if tir_info is None:
                separator = QLabel("")
                separator.setMinimumHeight(1)
                separator.setMaximumHeight(1)
                separator.setStyleSheet("background-color: #c0c0c0; margin: 5px 0px;")
                action_layout.addRow(separator)
            elif tir_info is not None: 
                tir_label, tir_hint, tir_state = tir_info
                action_row_widget = self.create_action_row(tir_key, tir_label, tir_hint, tir_state)
                self.action_widgets[tir_key] = action_row_widget
                action_layout.addRow(QLabel(f"{tir_label}："), action_row_widget["root_widget"])
        
        main_layout.addWidget(action_group)

        # ========== 7.插槽 ==========
        slot_group = QGroupBox("插槽")
        slot_layout = QVBoxLayout(slot_group)
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 10)

        select_all_btn = QPushButton("全部选是")
        select_all_btn.clicked.connect(self.on_select_all)
        deselect_all_btn = QPushButton("全部选否")
        deselect_all_btn.clicked.connect(self.on_deselect_all)
        invert_select_btn = QPushButton("反选")
        invert_select_btn.clicked.connect(self.on_invert_select)

        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addWidget(invert_select_btn)
        btn_layout.addStretch()

        self.custom_scroll_area = QScrollArea()
        self.custom_scroll_area.setWidgetResizable(True)
        self.custom_scroll_area.setMinimumHeight(500)
        self.custom_scroll_area.setMaximumHeight(500)

        slot_content_widget = QWidget()
        self.slot_grid_layout = QGridLayout(slot_content_widget)
        self.slot_grid_layout.setSpacing(10)
        self.slot_grid_layout.setContentsMargins(10, 10, 10, 10)
        self.custom_scroll_area.setWidget(slot_content_widget)
        
        slot_layout.addWidget(btn_widget)
        slot_layout.addWidget(self.custom_scroll_area)
        main_layout.addWidget(slot_group)

        image_label = QLabel()
        image_label.setPixmap(QPixmap(os.path.join(get_exe_dir(), f"assets/gmui{random.randint(1, 7):02d}.png")).scaled(375, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(image_label, alignment=Qt.AlignCenter)

    def create_animation_row(self, title: str, anim_type: str) -> dict:
        """创建动画配置行（新结构）"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        first_row_widget = QWidget()
        first_row_layout = QHBoxLayout(first_row_widget)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        state_check = QCheckBox("启用")
        main_combo = QComboBox()
        main_combo.addItems(self.animation_names)
        main_combo.setEnabled(False)
        multi_track_check = QCheckBox("多轨")
        multi_track_check.setEnabled(False)
        add_btn = QPushButton("+ 添加动画")
        add_btn.clicked.connect(lambda: self.add_extra_anim_row(anim_type))
        add_btn.setEnabled(False)

        def update_widgets_enabled(state):
            enabled = (state == Qt.Checked)
            main_combo.setEnabled(enabled)
            multi_track_check.setEnabled(enabled)
            add_btn.setEnabled(enabled)
            # 禁用所有额外行的下拉框
            for row_info in widget_info["extra_rows"]:
                row_info["combo"].setEnabled(enabled)
                row_info["delete_btn"].setEnabled(enabled)
        state_check.stateChanged.connect(update_widgets_enabled)

        first_row_layout.addWidget(main_combo, 1) 
        first_row_layout.addWidget(state_check)
        first_row_layout.addWidget(multi_track_check)
        first_row_layout.addWidget(add_btn)
        first_row_layout.addStretch()

        extra_rows_container = QWidget()
        extra_rows_layout = QVBoxLayout(extra_rows_container)
        extra_rows_layout.setSpacing(5)
        extra_rows_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(first_row_widget)
        main_layout.addWidget(extra_rows_container)
        
        widget_info = {
            "widget": main_widget,
            "state_check": state_check,
            "multi_track": multi_track_check,
            "main_combo": main_combo,
            "add_btn": add_btn,
            "extra_rows_container": extra_rows_container,
            "extra_rows": []
        }

        return widget_info
    def add_extra_anim_row(self, anim_type: str):
        """为指定的动画类型添加额外的动画行"""
        widget_info = self.anim_widgets[anim_type]
        container = widget_info["extra_rows_container"]
        if not widget_info["state_check"].isChecked():
            return
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        # 下拉框（占用剩余空间）
        combo = QComboBox()
        combo.addItems(self.animation_names)
        combo.setEnabled(widget_info["state_check"].isChecked())
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFocusPolicy(Qt.NoFocus)
        delete_btn.clicked.connect(lambda checked=False, at=anim_type, rw=row_widget: self.remove_extra_anim_row(at, rw))
        delete_btn.setEnabled(widget_info["state_check"].isChecked())

        row_layout.addWidget(combo, 1) 
        row_layout.addWidget(delete_btn)
        row_layout.addStretch()
        container.layout().addWidget(row_widget)
        row_info = {
            "widget": row_widget,
            "combo": combo,
            "delete_btn": delete_btn
        }
        widget_info["extra_rows"].append(row_info)
        container.layout().update()

    def remove_extra_anim_row(self, anim_type: str, row_widget):
        """删除指定的额外动画行"""
        widget_info = self.anim_widgets[anim_type]
        for i, row_info in enumerate(widget_info["extra_rows"]):
            if row_info["widget"] == row_widget:
                widget_info["extra_rows"].pop(i)
                break
        row_widget.setParent(None)
        row_widget.deleteLater()

    def load_config_to_ui(self):
        """加载配置到UI控件"""
        # ========== 加载基本配置 ==========
        spine_version = self.config.get("spine", "spine3.8")
        if spine_version in self.SPINE_TYPES:
            self.spine_version_combo.setCurrentText(spine_version)

        premult_config = self.config.get("alpha", 0)
        self.premult_checkbox.setChecked(premult_config == 1)

        skel_config = self.config.get("skel", False)
        if skel_config and isinstance(skel_config, str):
            skel_filename = os.path.basename(skel_config) if skel_config else ""
            self.anim_file_edit.setText(skel_filename)
        else:
            self.anim_file_edit.setText("")

        atlas_config = self.config.get("atlas", False)
        if atlas_config and isinstance(atlas_config, str):
            atlas_filename = os.path.basename(atlas_config) if atlas_config else ""
            self.cut_file_edit.setText(atlas_filename)
        else:
            self.cut_file_edit.setText("")
        api_opacity = self.config.get("input_opacity", 1.0)
        self.api_opacity_slider.setValue(int(api_opacity * 100))
        self.api_opacity_label.setText(f"{api_opacity:.2f}")

        # 加载字幕配置
        lyrics_pos = self.config.get("lyrics_pos", [0, 0])
        self.lyrics_width_slider.setValue(lyrics_pos[0])
        self.lyrics_width_label.setText(str(lyrics_pos[0]))
        self.lyrics_height_slider.setValue(lyrics_pos[1])
        self.lyrics_height_label.setText(str(lyrics_pos[1]))

        lyrics_scale = self.config.get("lyrics_scale", 1.0)
        self.lyrics_scale_slider.setValue(int(lyrics_scale * 100))
        self.lyrics_scale_label.setText(f"{lyrics_scale:.2f}")

        lyrics_opacity = self.config.get("lyrics_opacity", 1.0)
        self.lyrics_opacity_slider.setValue(int(lyrics_opacity * 100))
        self.lyrics_opacity_label.setText(f"{lyrics_opacity:.2f}")

        # 加载窗口配置
        default_width, default_height = self.config.get("window_size", (1000, 1000))
        self.window_size_slider.setValue(default_width)
        self.window_size_label.setText(f"{default_width} × {default_height}")
        self.opacity_slider.setValue(int(self.config.get("window_opacity", 1.0) * 100))
        self.opacity_label.setText(f"{self.config.get('window_opacity', 1.0):.2f}")

        # 加载页面配置
        self.page_width_slider.setValue(self.config.get("page_width", 0))
        self.page_width_label.setText(str(self.config.get("page_width", 0)))
        self.page_height_slider.setValue(self.config.get("page_height", 0))
        self.page_height_label.setText(str(self.config.get("page_height", 0)))
        self.page_scale_slider.setValue(int(self.config.get("page_scale", 1.0) * 100))
        self.page_scale_label.setText(f"{self.config.get('page_scale', 1.0):.2f}")

        # 加载默认待机动画
        default_anim = self.config.get("anim_idle", "")
        if default_anim in self.animation_names:
            self.default_anim_combo.setCurrentText(default_anim)

        # 说话动画
        speak_config = self.config.get("anim_speak", False)
        if speak_config and speak_config != False:
            if speak_config in self.animation_names:
                self.speak_anim_combo.setCurrentText(speak_config)
                self.speak_anim_check.setChecked(True)
                self.speak_anim_combo.setEnabled(True)
        else:
            self.speak_anim_check.setChecked(False)
            self.speak_anim_combo.setEnabled(False)

        # 眨眼动画
        blink_config = self.config.get("anim_blink", False)
        if blink_config and blink_config != False:
            if blink_config in self.animation_names:
                self.blink_anim_combo.setCurrentText(blink_config)
                self.blink_anim_check.setChecked(True)
                self.blink_anim_combo.setEnabled(True)
        else: 
            self.blink_anim_check.setChecked(False)
            self.blink_anim_combo.setEnabled(False)

        # ========== 加载动态动画配置 ==========
        saved_anim_config = self.config.get("anim_config", {})
        for anim_type, widget_info in self.anim_widgets.items():
            config = saved_anim_config.get(anim_type, {})
            if not config:
                continue
            state = config.get("state", False)
            widget_info["state_check"].setChecked(state)
            widget_info["multi_track"].setChecked(config.get("multi_track", False))
            widget_info["main_combo"].setEnabled(state)
            widget_info["multi_track"].setEnabled(state)
            widget_info["add_btn"].setEnabled(state)
            anim_list = config.get("anim", [])
            if not anim_list:
                continue
            if len(anim_list) > 0 and anim_list[0] in self.animation_names:
                widget_info["main_combo"].setCurrentText(anim_list[0])
            for row_info in widget_info["extra_rows"][:]:
                self.remove_extra_anim_row(anim_type, row_info["widget"])
            for anim_name in anim_list[1:]:
                self.add_extra_anim_row(anim_type)
                if widget_info["extra_rows"]: 
                    new_row = widget_info["extra_rows"][-1]
                    if anim_name in self.animation_names:
                        new_row["combo"].setCurrentText(anim_name)
                    new_row["combo"].setEnabled(state)
                    new_row["delete_btn"].setEnabled(state)

        slot_config = self.config.get("slot", {})
        if slot_config:
            self.render_slot_widgets(slot_config)
            
        # ==========加载触发机制配置 ==========
        action_config = self.config.get("action_config", {})
        for tir_key, tir_config in action_config.items():
            if tir_key not in self.action_widgets:
                continue
            
            action_info = self.action_widgets[tir_key]
            tir_state = action_info["tir_state"]
            
            if tir_state in [1, 3]:
                action_info["cod_input"].setText(tir_config.get("cod", ""))
            if tir_state in [2, 3]:
                action_info["state_check"].setChecked(tir_config.get("state", False))
                action_info["sequence_check"].setChecked(tir_config.get("sequence", False))
            
            self.clear_all_line_rows(tir_key)
            
            valid_lines = []
            if tir_config: 
                for line_key in sorted(tir_config.keys()):
                    if not line_key.startswith("lines"):
                        continue
                    
                    line_data = tir_config.get(line_key, {})
                    text = line_data.get("text", "").strip()
                    if not text:
                        continue
                    
                    audio_url = line_data.get("url", False)
                    valid_lines.append({
                        "text": text,
                        "url": audio_url if (audio_url and audio_url != False) else ""
                    })
            
            if valid_lines:
                self.add_dialogue_group(tir_key)
                groupbox = self.dialogue_groupboxes.get(tir_key)
                
                for i, line_data in enumerate(valid_lines):
                    if i > 0:
                        self.add_line_to_group(tir_key, groupbox)
                    
                    line_widgets = action_info["lines_widgets"][-1]
                    line_widgets["text_edit"].setText(line_data["text"])
                    line_widgets["audio_edit"].setText(line_data["url"])

    # === 触发 ===
    def clear_all_line_rows(self, tir_key):
        """清空指定触发类型的所有台词行"""
        action_info = self.action_widgets.get(tir_key)
        if not action_info:
            return
        if tir_key in self.dialogue_groupboxes:
            groupbox = self.dialogue_groupboxes[tir_key]
            action_info["lines_layout"].removeWidget(groupbox)
            groupbox.deleteLater()
            del self.dialogue_groupboxes[tir_key]
        action_info["lines_widgets"] = []

    def create_action_row(self, tir_key, tir_label, tir_hint, tir_state):
        """创建单个触发机制行的控件"""
        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(0, 0, 0, 0)
        top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        
        cod_input = QLineEdit()
        cod_input.setPlaceholderText(tir_hint)
        state_check = QCheckBox("台词")
        add_btn = QPushButton("+添加台词")
        add_btn.clicked.connect(lambda _, k=tir_key: self.add_dialogue_group(k))
        sequence_check = QCheckBox("顺序")
        sequence_check.setToolTip("按顺序播放台词，否则随机播放")
        if tir_state == 1:  # 状态1：只显示条件文本框
            top_row_layout.addWidget(cod_input, 1)
        elif tir_state == 2:  # 状态2：只显示台词相关功能
            top_row_layout.addStretch(1)
            top_row_layout.addWidget(state_check)
            top_row_layout.addWidget(sequence_check)
            top_row_layout.addWidget(add_btn)
        elif tir_state == 3:  # 状态3：都显示
            top_row_layout.addWidget(cod_input, 1)
            top_row_layout.addWidget(state_check)
            top_row_layout.addWidget(sequence_check)
            top_row_layout.addWidget(add_btn)
        top_row_layout.addStretch()
        lines_widget = QWidget()
        lines_layout = QVBoxLayout(lines_widget)
        lines_layout.setSpacing(5)
        lines_layout.setContentsMargins(10, 0, 0, 0)
        root_layout.addWidget(top_row_widget)
        root_layout.addWidget(lines_widget)
        
        return {
            "root_widget": root_widget,
            "cod_input": cod_input,
            "state_check": state_check,
            "add_btn": add_btn,
            "sequence_check": sequence_check,
            "lines_layout": lines_layout,
            "lines_widgets": [],
            "tir_state": tir_state
        }

    def add_dialogue_group(self, tir_key):
        """为指定触发类型添加台词组"""
        action_info = self.action_widgets.get(tir_key)
        if not action_info:
            return
        if tir_key in self.dialogue_groupboxes:
            groupbox = self.dialogue_groupboxes[tir_key]
            self.add_line_to_group(tir_key, groupbox)
        else:
            groupbox = QGroupBox(f"{self.TIR_TYPES[tir_key][0]}台词配置")
            groupbox_layout = QVBoxLayout(groupbox)
            groupbox_layout.setSpacing(5)
            groupbox_layout.setContentsMargins(10, 15, 10, 10)
            self.add_line_to_group(tir_key, groupbox)
            action_info["lines_layout"].addWidget(groupbox)
            self.dialogue_groupboxes[tir_key] = groupbox

    def add_line_to_group(self, tir_key, groupbox):
        """在台词组内添加一行台词配置"""
        action_info = self.action_widgets.get(tir_key)
        if not action_info:
            return
        line_row_widget = QWidget()
        line_row_layout = QHBoxLayout(line_row_widget)
        line_row_layout.setSpacing(10)
        line_row_layout.setContentsMargins(0, 0, 0, 0)
        text_edit = QLineEdit()
        text_edit.setPlaceholderText("台词(必要)")
        audio_edit = QLineEdit()
        audio_edit.setPlaceholderText("文件名称")
        audio_btn = QPushButton("选择配音")
        audio_btn.clicked.connect(
            lambda _, edit=audio_edit: self.select_audio_file(edit)
        )
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(
            lambda _, widget=line_row_widget, key=tir_key: self.delete_line_row(widget, key)
        )
        line_row_layout.addWidget(text_edit, 2) 
        line_row_layout.addWidget(audio_edit, 2)
        line_row_layout.addWidget(audio_btn)
        line_row_layout.addWidget(delete_btn)
        line_row_layout.addStretch()
        groupbox.layout().addWidget(line_row_widget)

        action_info["lines_widgets"].append({
            "widget": line_row_widget,
            "text_edit": text_edit,
            "audio_edit": audio_edit,
            "groupbox": groupbox
        })

    def delete_line_row(self, widget, tir_key):
        """删除指定行"""
        action_info = self.action_widgets.get(tir_key)
        if not action_info:
            return
        for i, line_data in enumerate(action_info["lines_widgets"]):
            if line_data["widget"] == widget:
                if tir_key in self.dialogue_groupboxes:
                    groupbox = self.dialogue_groupboxes[tir_key]
                    groupbox.layout().removeWidget(widget)
                widget.deleteLater()
                action_info["lines_widgets"].pop(i)
                if tir_key in self.dialogue_groupboxes:
                    groupbox = self.dialogue_groupboxes[tir_key]
                    if groupbox.layout().count() == 0:
                        action_info["lines_layout"].removeWidget(groupbox)
                        groupbox.deleteLater()
                        del self.dialogue_groupboxes[tir_key]
                break

    def select_audio_file(self, audio_edit: QLineEdit):
        """选择音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.flac *.wav)"
        )
        if file_path:
            file_name = self.on_copy_file(file_path)
            if file_name:
                audio_edit.setText(file_name)

    # === slot ===
    def render_slot_widgets(self, slot_config: dict):
        """统一渲染slot控件"""
        for i in reversed(range(self.slot_grid_layout.count())):
            widget = self.slot_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.slot_widgets.clear()
        row = 0
        col = 0
        max_cols = 2
        slot_names = list(slot_config.keys())
    
        for slot_name in slot_names:
            label = QLabel(slot_name)
            checkbox = QCheckBox()
            checkbox.setChecked(slot_config.get(slot_name, True))
            checkbox.stateChanged.connect(
                lambda state, name=slot_name: self.on_slot_checkbox_changed(name, state)
            )
            self.slot_widgets[slot_name] = checkbox
            self.slot_grid_layout.addWidget(label, row, col*2)
            self.slot_grid_layout.addWidget(checkbox, row, col*2 + 1)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def on_select_all(self):
        """全部选是"""
        for slot_name, checkbox in self.slot_widgets.items():
            checkbox.setChecked(True)

    def on_deselect_all(self):
        """全部选否"""
        for slot_name, checkbox in self.slot_widgets.items():
            checkbox.setChecked(False)

    def on_invert_select(self):
        """反选"""
        for slot_name, checkbox in self.slot_widgets.items():
            checkbox.setChecked(not checkbox.isChecked())

    # 复选框状态变更回调 ==========
    def on_slot_checkbox_changed(self, slot_name: str, state: int):
        """Slot复选框状态变更时调用runjs"""
        state_val = 1 if state == Qt.Checked else 0
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"setslot('{slot_name}', {state_val})")

    def on_slot_check_changed(self, state: int, slot_name: str):
        """用户手动点击复选框触发"""
        is_checked = state == Qt.Checked
        state_num = 1 if is_checked else 0
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"setslot('{slot_name}', {state_num})")

    # ========== 事件处理 ==========
    def on_window_size_change(self, value: int):
        """窗口大小滑块变化"""
        width = value
        height = int(width * 1)
        self.window_size_label.setText(f"{width} × {height}")
        self.window_size_changed.emit(width, height)
        # 同步更新主窗口大小实时预览
        if self.parent_window:
            self.parent_window.setposition(width, height)

    def on_opacity_change(self, value: int):
        """透明度滑块变化"""
        opacity = value / 100.0
        self.opacity_label.setText(f"{opacity:.2f}")
        self.window_opacity_changed.emit(opacity)
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"setopacity({opacity})")

    def on_page_position_change(self):
        """页面位置/尺寸变化"""
        width = self.page_width_slider.value()
        height = self.page_height_slider.value()
        self.page_width_label.setText(str(width))
        self.page_height_label.setText(str(height))
        self.page_position_changed.emit(width, height)
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"setposition({width}, {height})")

    def on_page_scale_change(self, value: int):
        """页面缩放变化"""
        scale = value / 100.0
        self.page_scale_label.setText(f"{scale:.2f}")
        self.page_scale_changed.emit(scale)
        width = self.page_width_slider.value()
        height = self.page_height_slider.value()
        self.page_width_label.setText(str(width))
        self.page_height_label.setText(str(height))
        self.page_position_changed.emit(width, height)
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"setscale({scale},{width},{height})")

    def on_api_opacity_change(self, value: int):
        """API透明度滑块变化"""
        opacity = value / 100.0
        self.api_opacity_label.setText(f"{opacity:.2f}")
        # 调用主窗口的init_set_opacity方法
        if hasattr(self.parent_window, 'init_set_opacity'):
            self.parent_window.init_set_opacity(opacity)

    def on_lyrics_position_change(self):
        """字幕位置变化"""
        x = self.lyrics_width_slider.value()
        y = self.lyrics_height_slider.value()
        self.lyrics_width_label.setText(str(x))
        self.lyrics_height_label.setText(str(y))
        # 调用JS设置字幕位置
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"lyricsmove({x}, {y})")

    def on_lyrics_scale_change(self, value: int):
        """字幕大小变化"""
        scale = value / 100.0
        self.lyrics_scale_label.setText(f"{scale:.2f}")
        # 调用JS设置字幕大小
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"lyricsscale({scale})")

    def on_lyrics_opacity_change(self, value: int):
        """字幕透明度变化"""
        opacity = value / 100.0
        self.lyrics_opacity_label.setText(f"{opacity:.2f}")
        # 调用JS设置字幕透明度
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js(f"lyricsopacity({opacity})")

    def reset_window_config(self):
        """重置窗口配置"""
        self.opacity_slider.setValue(100)
        size = QApplication.desktop().screenGeometry()
        edge = min(size.width(), size.height())
        min_edge = max(500,edge // 2)
        self.window_size_slider.setValue(min_edge)
        self.parent_window.resize(min_edge, min_edge)
        self.parent_window.move((size.width() - min_edge) // 2, (size.height() - min_edge) // 2)
        self.parent_window.run_js(f"setopacity(1)")

    def reset_page_config(self):
        """重置页面配置"""
        self.page_width_slider.setValue(0)
        self.page_height_slider.setValue(0)
        self.page_scale_slider.setValue(100)
        if self.parent_window:
            self.parent_window.run_js(f"setposition(0,0)")
            self.parent_window.run_js(f"setscale(1)")

    def reset_lyrics_config(self):
        """重置字幕配置"""
        self.lyrics_width_slider.setValue(0)
        self.lyrics_height_slider.setValue(0)
        self.lyrics_scale_slider.setValue(100)
        self.lyrics_opacity_slider.setValue(100)

        # 调用JS重置
        if hasattr(self.parent_window, 'run_js'):
            self.parent_window.run_js("lyricsmove(0, 0)")
            self.parent_window.run_js("lyricsscale(1)")
            self.parent_window.run_js("lyricsopacity(1)")

    # ========== 重启 ==========
    def reload_spine_html(self):
        spine_config = self.config.get("spine", False)
        skel_config = self.config.get("skel", False)
        alpha_config = self.config.get("alpha", 0)
        anim_filename = self.anim_file_edit.text().strip()
        spine_name = self.spine_version_combo.currentText()
        config_skel_filename = os.path.basename(skel_config) if skel_config else""
        config_spine_name = os.path.basename(spine_config) if spine_config else""
        new_premult_value = 1 if self.premult_checkbox.isChecked() else 0
        if anim_filename != config_skel_filename or spine_name != config_spine_name or new_premult_value != alpha_config:
            
            self.config.delete_config("slot")
            self.config.delete_config("anim")
            self.config.delete_config("anim_idle")
            self.config.delete_config("anim_speak")
            self.config.delete_config("anim_blink")
            self.config.delete_config("anim_config")
            self.config.delete_config("action_config")
            self.config.delete_config("page_width")
            self.config.delete_config("page_height")
            self.config.delete_config("page_scale")

            self.config.update_config("spine", spine_name)
            self.config.update_config("alpha", new_premult_value)
            skel_value = f"{anim_filename}" if anim_filename else False
            self.config.update_config("skel", skel_value)

            cut_filename = self.cut_file_edit.text().strip()
            atlas_value = f"{cut_filename}" if cut_filename else False
            self.config.update_config("atlas", atlas_value)

            self.parent_window.run_js(f"border(0)")
            self.parent_window.close_gmui(0)
            self.accept()
        else:
            self.animation_names = []
            self.save_config()
            self.load_animation_names_from_config()
            self.load_config_to_ui() 

        self.parent_window.init_html()

    def save_config(self):
        """保存所有配置到配置文件"""
        try:
            # 1. 保存窗口配置
            window_width = self.window_size_slider.value()
            window_height = int(window_width * 1)
            self.config.update_config("window_size", (window_width, window_height))
            self.config.update_config("window_opacity", self.opacity_slider.value() / 100.0)
            # 2. 保存页面配置
            self.config.update_config("page_width", self.page_width_slider.value())
            self.config.update_config("page_height", self.page_height_slider.value())
            self.config.update_config("page_scale", self.page_scale_slider.value() / 100.0)
            self.config.update_config("input_opacity", self.api_opacity_slider.value() / 100.0)
            #字幕配置
            self.config.update_config("lyrics_pos", [
                self.lyrics_width_slider.value(),
                self.lyrics_height_slider.value()
            ])
            self.config.update_config("lyrics_scale", self.lyrics_scale_slider.value() / 100.0)
            self.config.update_config("lyrics_opacity", self.lyrics_opacity_slider.value() / 100.0)
            # 4. 动画
            self.config.update_config("anim_idle", self.default_anim_combo.currentText())
            if self.speak_anim_check.isChecked():
                self.config.update_config("anim_speak", self.speak_anim_combo.currentText())
            else:
                self.config.update_config("anim_speak", False)
            if self.blink_anim_check.isChecked():
                self.config.update_config("anim_blink", self.blink_anim_combo.currentText())
            else:
                self.config.update_config("anim_blink", False)
            # 6. 保存动态动画配置
            anim_config = {}
            for anim_type, widget_info in self.anim_widgets.items():
                if not widget_info["state_check"].isChecked():
                    continue
                anim_names = []
                main_anim = widget_info["main_combo"].currentText()
                if main_anim:
                    anim_names.append(main_anim)
                for row_info in widget_info["extra_rows"]:
                    anim_name = row_info["combo"].currentText()
                    if anim_name:
                        anim_names.append(anim_name)
                if anim_names:
                    anim_item = {
                        "state": True,
                        "multi_track": widget_info["multi_track"].isChecked(),
                        "anim": tuple(anim_names)
                    }
                    anim_config[anim_type] = anim_item

            self.config.update_config("anim_config", anim_config)
            self.animation_config_changed.emit(anim_config)

            # 6.slot
            slot_config = {}
            for slot_name, checkbox in self.slot_widgets.items():
                slot_config[slot_name] = checkbox.isChecked()
            self.config.update_config("slot", slot_config)


            # ========== 触发机制 ==========
            action_config = {}
            for tir_key, action_info in self.action_widgets.items():
                tir_state = action_info["tir_state"]
                cod_text = action_info["cod_input"].text().strip() if tir_state in [1, 3] else ""
                state_checked = action_info["state_check"].isChecked() if tir_state in [2, 3] else False
                sequence_checked = action_info["sequence_check"].isChecked() if tir_state in [2, 3] else False

                action_item = {
                    "cod": cod_text,
                    "state": state_checked,
                    "sequence": sequence_checked
                }

                valid_lines = []
                for line_widgets in action_info["lines_widgets"]:
                    text = line_widgets["text_edit"].text().strip()
                    if not text: 
                        continue
                    audio_url = line_widgets["audio_edit"].text().strip()
                    audio_url = audio_url if audio_url else False
                    valid_lines.append({
                        "text": text,
                        "url": audio_url
                    })

                for idx, line_data in enumerate(valid_lines):
                    line_key = f"lines{idx:02d}" 
                    action_item[line_key] = line_data

                if cod_text or state_checked or len(valid_lines) > 0:
                    action_config[tir_key] = action_item

            self.config.update_config("action_config", action_config)

        except ValueError as e:
            error(self,f"保存失败：{e}")
        except Exception as e:
            error(self,f"保存失败：{e}")

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭时自动保存配置"""
        #self.save_config()  # 自动
        #event.accept()
        result = three_choice(self, text="是否保存更改？")

        if result == 0:
            self.save_config()
            self.parent_window.run_js(f"border(0)")
            self.parent_window.close_gmui(1)
            event.accept()
        elif result == 1:
            self.parent_window.run_js(f"border(0)")
            self.parent_window.close_gmui(2)
            event.accept()
        else:
            event.ignore()