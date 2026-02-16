import os
import sys
import keyboard
import threading
import time
import ctypes
import random
from typing import Callable, Any
from PyQt5.QtWidgets import (
    QMainWindow, QMenu, QAction, QApplication,QSystemTrayIcon,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea
)
from PyQt5.QtWebEngineWidgets import QWebEngineView,QWebEngineSettings
from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QPoint,QEvent,QPropertyAnimation,pyqtSignal
)
from PyQt5.QtGui import  QFont, QFontDatabase ,QCursor,QMouseEvent,QIcon,QFontMetrics

from .gmui import GMUIConfigDialog
from .notice import notice
from .url import get_exe_dir,get_exe_url
from .alert import error,yes_or_no

class CustomWebEngineView(QWebEngineView):
    """WebView"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

    def contextMenuEvent(self, event):
        event.ignore()

class DesktopPetWindow(QMainWindow):
    show_error_signal = pyqtSignal(int,str)
    """核心类"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_window()

    # -------------------- 穿透检测逻辑 --------------------
    def check_pixel_transparency(self):
        """定时轮询鼠标位置"""
        if self.is_click_through:
            return
        global_pos =  QCursor.pos()
        if not self.geometry().contains(global_pos) and not self.input_widget.history_widget.geometry().contains(global_pos) and (not self.input_widget.geometry().contains(global_pos)):
            if self.chat and not self.input_widget.hide_timer.isActive():
                self.input_widget.start_hide_timer()
            return
        elif (self.geometry().contains(global_pos) or self.input_widget.geometry().contains(global_pos)):
            if not self.chat or not self.input_widget.isVisible():
                self.input_widget.hide_timer.stop()
        
        local_pos = self.mapFromGlobal(global_pos)
        js_code = f"transparentpixel({local_pos.x()}, {local_pos.y()})"
        self.run_js(js_code, self.handle_transparency_callback)

    def handle_transparency_callback(self, is_transparent):
        """JS动态修改窗口属性"""
        if is_transparent == self.last_transparent_state:
            return
        self.last_transparent_state = is_transparent
        hwnd = self.winId().__int__()
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        WS_EX_TRANSPARENT = 0x20
        WS_EX_LAYERED = 0x80000

        if is_transparent:
            new_style = ex_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
            #print("窗口透明")
        else:#置为实体
            new_style = ex_style & ~WS_EX_TRANSPARENT | WS_EX_LAYERED
            #print("窗口实体")

        ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)
    # -------------------- 穿透固定 --------------------
    def setup_click_through(self):
        """设置窗口穿透模式"""
        self.is_click_through = False

        self.hwnd = self.winId().__int__()
        self.apply_click_through_mode()
        self.set_window_topmost()

    def apply_click_through_mode(self):
        """应用点击穿透模式"""
        if self.is_click_through:
            ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,0x80000 | 0x20 | 0x08000000)
        else:
            ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,0)
            self.last_transparent_state = None 
        self.set_window_no_taskbar()
        ctypes.windll.user32.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0, 0x0040 | 0x0001 | 0x0002)

    def set_window_topmost(self):
        """设置窗口置顶"""
        ctypes.windll.user32.SetWindowPos(self.hwnd,-1,0, 0, 0, 0,0x0001 | 0x0010)

    def set_window_no_taskbar(self):
        """使用Windows API确保窗口不在任务栏显示"""
        ex_style = ctypes.windll.user32.GetWindowLongW(self.hwnd, -20)
        ex_style |= 0x00000080
        ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,ex_style)

    def toggle_click_through(self):
        """切换穿透模式 - 主线程安全调用"""
        QTimer.singleShot(0, self._toggle_click_through_ui)

    def _toggle_click_through_ui(self):
        """在UI线程中切换穿透模式"""
        self.is_click_through = not self.is_click_through
        self.apply_click_through_mode()

        if not self.is_click_through:
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.show()

    def start_global_hotkey_listener(self):
        """启动全局快捷键监听线程"""
        if hasattr(self, 'keyboard_listener_active') and self.keyboard_listener_active:
            return

        self.keyboard_listener_active = True
        self.hotkey_registered = False
        self.hotkey_handlers = {}

        listener_thread = threading.Thread(target=self.global_hotkey_listener)
        listener_thread.daemon = True
        listener_thread.start()
        self.show_error_signal.connect(self.hotkey_error)

    def global_hotkey_listener(self):
        """全局快捷键监听"""
        while self.keyboard_listener_active:
            try:
                if not self.hotkey_registered:
                    keyboard.unhook_all()
                    default_cod = self.action_config.get("keyboard", {}).get("cod")
                    if default_cod:
                        keyboard.add_hotkey(default_cod, self.toggle_click_through)
                    else:
                        keyboard.add_hotkey('alt+`', self.toggle_click_through)
                    for key_name in ["keyboard1", "keyboard2", "keyboard3"]:
                        config = self.action_config.get(key_name, {})
                        cod = config.get("cod")
                        if not cod:
                            continue
                        def create_handler(k):
                            def handler():
                                self.show_error_signal.emit(2,k)
                            return handler
                        try:
                            keyboard.add_hotkey(cod, create_handler(key_name))
                            self.hotkey_handlers[key_name] = cod
                        except Exception as e:
                            self.show_error_signal.emit(1,f"[ <b>{key_name}</b> ] 的快捷键 [ <b>{cod}</b> ] 不可用")
                    self.hotkey_registered = True
                time.sleep(1)
            except Exception as e:
                self.hotkey_registered = False
                time.sleep(5)

    def hotkey_error(self,num,msg):
        if num == 1:
            error(self,msg,2)
        elif num == 2:
            self.play_anim(msg)
            self.play_audio(msg)
    # ========== 初始化 ==========
    def init_window(self):
        """初始化窗口属性"""
        font_path = os.path.join(get_exe_dir(), "assets/SourceHanSansSC.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font = QFont(font_families[0], 10)
                    self.setFont(font)
                    QApplication.setFont(font)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        width, height = self.config.get("window_size")
        self.resize(width, height)
        pos_x, pos_y = self.config.get("window_pos")
        self.move(pos_x, pos_y)
        self.gmui = True
        self.chat = False

        self.init_html()

        self.set_mouse()
        self.init_chat()
        self.init_menu()
        self.setup_click_through()
        self.start_global_hotkey_listener()
        self.init_system_tray()

        self.last_transparent_state = False  
        self.transparency_timer = QTimer(self)
        self.transparency_timer.timeout.connect(self.check_pixel_transparency)
        self.transparency_timer.start(1000) 

    def init_html(self):
        """初始化WebEngine（加载Spine动画）"""
        if hasattr(self, 'browser') and self.browser:
            self.browser.stop()
            self.browser.setHtml("")
            self.browser.deleteLater()
            QApplication.processEvents()
        
        self.browser = CustomWebEngineView(self)
        self.browser.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.browser.installEventFilter(self)
        self.browser.page().setBackgroundColor(Qt.transparent)
        self.setCentralWidget(self.browser)

        self.anim_config = self.config.get("anim_config", {})
        self.action_config = self.config.get("action_config", {})

        if self.config.get('state', 1) == 1:
            safe_mode = yes_or_no(self,title="GMUI",text="检测到先前意外的关闭，是否启用安全模式？",btn1_text="正常启动",btn2_text="安全模式")
        else:
            safe_mode = False

        spine_name = self.config.get('spine', '3.8') 
        html_filename = f"spine{spine_name}.html"
        html_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),"../assets/", html_filename
        ))
        html_path = html_path.replace("\\", "/")
        if not os.path.exists(html_path):
            error(self,"Spine版本错误")
            self.quit_app()
        if not safe_mode:
            self.config.update_config("state", 1)
            self.init_check_html()
        else:
            error(self,"安全模式下不会加载动画文件",s=2)
            self.gmui = False
        self.browser.load(QUrl.fromLocalFile(html_path))

    def init_check_html(self, count=1):
        """超时轮询：直到 window.htmlReady 为 true"""
        def callback(result):
            if result is True:
                self.init_spine()
            else:
                if count >= 6:
                    error(self,"高能粒子加速器发生问题")
                    self.gmui = False
                else:
                    QTimer.singleShot(500, lambda: self.init_check_html(count + 1))
        self.browser.page().runJavaScript(
            "!!window.htmlReady",
            callback
        )


    def init_spine(self):
        """加载Spine资源"""
        skel_name = self.config.get('skel', False)
        atlas_name = self.config.get('atlas', False)
        anim_idle = self.config.get('anim_idle', False)
        alpha_bool = bool(self.config.get('alpha', 1))

        if skel_name is False or atlas_name is False:
            self.run_js("nonono()")
            error(self,"未配置动画文件")
            self.gmui = False
            return

        press_event = QMouseEvent(QEvent.MouseButtonPress,QPoint(10, 10),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
        QApplication.sendEvent(self.browser.focusProxy(), press_event)
        release_event = QMouseEvent(QEvent.MouseButtonRelease,QPoint(10, 10),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
        QApplication.sendEvent(self.browser.focusProxy(), release_event)

        url = os.path.join(get_exe_url(),"assets/").replace("\\", "/")
        skel_path = os.path.abspath(os.path.join(
            url,skel_name
        )).replace("\\", "/")
        atlas_path = os.path.abspath(os.path.join(
            url,atlas_name
        )).replace("\\", "/")    
        anim_param = f"'{anim_idle}'" if anim_idle not in [False, None] else "false"
        self.run_js(f"seturl('{url}')")
        self.run_js(f"ready('{skel_path}', '{atlas_path}', {anim_param}, {str(alpha_bool).lower()})")
        self.init_check_spine()

    def init_check_spine(self, count=1):
        """超时轮询：直到 spineReady 为 true"""
        def callback(result):
            if result is True:
                self.init_spine_config()
            else:
                if count >= 20:
                    error(self,"低维展开失败")
                    self.gmui = False
                else:
                    QTimer.singleShot(200, lambda: self.init_check_spine(count + 1))
        self.browser.page().runJavaScript(
            "!!window.spineReady",
            callback
        )

    def init_spine_config(self):
        """Spine 就绪后应用初始配置"""
        config = self.config
        self.run_js(f"setopacity({config.get('window_opacity')})")
        self.run_js(f"setscale({config.get('page_scale')})")
        self.run_js(f"lyricsmove({config.get('lyrics_pos')[0]}, {config.get('lyrics_pos')[1]})")
        self.run_js(f"lyricsscale({config.get('lyrics_scale')})")
        self.run_js(f"lyricsopacity({config.get('lyrics_opacity')})")
        self.run_js(f"setposition({config.get('page_width')}, {config.get('page_height')})")
        config.get('anim_idle') is not False and self.run_js(f"play('{config.get('anim_idle')}')")
        if config.get("slot") is None:
            self.init_get_slot_name()
        else:
            slot_config = config.get("slot", {})
            disabled_slots = [name for name, state in slot_config.items() if not state]
            for slot_name in disabled_slots:
                self.run_js(f"setslot('{slot_name}',0)")
        if config.get("anim") is None:
            self.init_get_anim_name()
        self.gmui = False

    def init_get_anim_name(self):
        """异步获取动画名称并保存到配置"""
        def _init_get_anim_name(result):
            if isinstance(result, str):
                names = [name.strip() for name in result.split(',') if name.strip()]
            elif isinstance(result, list):
                names = [str(n) for n in result if n]
            else:
                names = []
            self.animation_names = names
            if self.config and names:
                self.config.update_config("anim", ",".join(names))
        self.run_js("getname()", _init_get_anim_name)
    
    def init_get_slot_name(self):
        """异步获取slot名称并保存默认配置"""
        def _init_get_slot_name(result):
            if isinstance(result, str):
                slot_names = [name.strip() for name in result.split(',') if name.strip()]
            elif isinstance(result, list):
                slot_names = [str(n) for n in result if n]
            else:
                slot_names = []
            default_slot_config = {name: True for name in slot_names}
            if self.config:
                self.config.update_config("slot", default_slot_config)
        self.run_js("getslotname()", _init_get_slot_name)      

    def init_menu(self):
        """初始化右键菜单"""
        self.context_menu = QMenu(self)
        
        self.context_gmui = QAction("打开GMUI", self)
        self.context_quit = QAction("退出", self)
        self.context_test = QAction("test", self)

        self.context_gmui.triggered.connect(self.open_gmui)
        self.context_quit.triggered.connect(self.quit_app)
        self.context_test.triggered.connect(self.test)

        self.context_menu.addAction(self.context_gmui)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.context_quit)
        self.context_menu.addAction(self.context_test)
    
    def test(self):
        """测试"""
        self.global_hotkey_listener()

    # -------------------- 核心功能 --------------------
    def run_js(self, js_code: str, callback: Callable[[Any], None] = None):
        """执行JS代码"""
        if callback is not None:
            self.browser.page().runJavaScript(js_code, callback)
        else:
            self.browser.page().runJavaScript(js_code)

    def play_anim(self, event: str, loop_count: int = 1):
        """根据事件名称播放对应动画"""
        if event not in self.anim_config:
            return
        anim_info = self.anim_config[event]
        multi_track = anim_info.get("multi_track", False)
        anims = anim_info.get("anim", [])
        if not anims:
            return
        if multi_track:
            anims_str = ",".join(anims)
            if not anims_str:
                return
            js_code = f"playtrack('{anims_str}', {loop_count})"
        else:
            anims_str = ",".join(anims)
            js_code = f"play('{anims_str}')"
        self.run_js(js_code)

    def play_audio(self, event: str):
        """根据事件名称播放对应音频"""
        if event not in self.action_config:
            return
        audio_config = self.action_config[event]
        if not audio_config.get("state", False):
            return
        lyrics_content = []
        def process_text_content(text_content, config_key=""):
            """处理text内容，检查是否需要分割"""
            if config_key == "lines00" and "/" in text_content:
                parts = text_content.split("/", 1)
                if len(parts) == 2:
                    if not parts[1].strip().startswith("[music:"):
                        notice(parts[0].strip(), parts[1].strip())
                    return parts[1]
            return text_content

        if audio_config.get("sequence", False):
            audio_urls = []
            for i in range(100):
                line_key = f"lines{i:02d}"
                if line_key in audio_config:
                    url = audio_config[line_key].get("url", "")
                    if url:
                        audio_urls.append(url)
                    text_content = audio_config[line_key].get("text", "")
                    text_content = process_text_content(text_content, line_key)
                    if text_content.startswith("[music:"):
                        lyrics_content.append(text_content)
                    else:
                        self.input_widget.update_chat_history(ai_text=text_content)
            
            if audio_urls:
                audio_files = ",".join(audio_urls)
                self.run_js(f"playaudio('{audio_files}')")
        else:
            line_keys = [key for key in audio_config.keys() if key.startswith("lines")]
            if line_keys:
                random_key = random.choice(line_keys)
                audio_file = audio_config[random_key].get("url", "")
                if audio_file:
                    self.run_js(f"playaudio('{audio_file}')")
                text_content = audio_config[random_key].get("text", "")
                text_content = process_text_content(text_content, "lines00")
                if text_content.startswith("[music:"):
                    lyrics_content.append(text_content)
                else:
                    self.input_widget.update_chat_history(ai_text=text_content)
        if lyrics_content:
            lyrics_text = ",".join(lyrics_content)
            self.run_js(f"setlyrics(`{lyrics_text}`)")
    
    # -------------------- 事件处理 --------------------
    def contextMenuEvent(self, event):
        """右键事件"""
        self.show_context_menu(event.globalPos())
        event.accept()

    def show_context_menu(self, pos: QPoint):
        """显示右键菜单"""
        if self.gmui:
            return
        self.context_menu.exec_(pos)

    def open_gmui(self):
        """打开GMUI面板"""
        if self.gmui:
            return
        dialog = GMUIConfigDialog(self.config, self)
        dialog.setModal(False)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        self.run_js(f"border(1)")
        self.config.update_config("window_pos", (self.x(), self.y()))
        self.gmui = True
        dialog.show()

    def close_gmui(self, n: int):
        """关闭GMUI面板"""
        if n == 1 or n == 2:
            config = self.config
            self.init_spine_config()
            self.anim_config = config.get("anim_config", {})
            self.action_config = config.get("action_config", {})
            width, height = config.get("window_size")
            self.run_js(f"lyricsmove({config.get('lyrics_pos')[0]}, {config.get('lyrics_pos')[1]})")
            self.run_js(f"lyricsscale({config.get('lyrics_scale')})")
            self.run_js(f"lyricsopacity({config.get('lyrics_opacity')})")
            self.input_widget.set_opacity(config.get('input_opacity'))
            self.setposition(width, height)
            if n == 2 :
                pos_x, pos_y = config.get("window_pos")
                self.move(pos_x, pos_y)
        self.gmui = False

    def quit_app(self):
        """退出程序"""
        try:
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
            self.config.update_config("window_pos", (self.x(), self.y()))
            self.config.update_config("input_pos", (self.input_widget.history_widget.x(), self.input_widget.history_widget.y()))
            self.config.update_config("state", 0)
            keyboard.unhook_all()
            QApplication.quit()
            sys.exit(0)
        except Exception as e:
            error(self)
            sys.exit(1)

    # -------------------- 对话 --------------------
    def init_chat(self):
        """初始化"""
        self.input_widget = InputWidget(self, self.config)
        if hasattr(self, 'input_widget'):
            input_pos = self.config.get("input_pos")
            self.init_set_opacity(self.config.get("input_opacity"))
            if input_pos and isinstance(input_pos, (tuple, list)) and len(input_pos) == 2:
                self.input_widget.history_widget.move(*input_pos)

    def init_set_opacity(self, value: float):
        """设置输入框整体透明度"""
        self.input_widget.set_opacity(value)

    # ========== 托盘 ==========
    def init_system_tray(self):
        """系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(get_exe_dir(), "assets/gm00.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("GMUI")
        self.tray_menu = QMenu(self)
        self.tray_toggle = QAction("调整维度", self)
        self.tray_gmui = QAction("打开GMUI", self)
        self.tray_quit = QAction("退出", self)
        self.tray_toggle.triggered.connect(self.toggle_click_through)
        self.tray_gmui.triggered.connect(self.open_gmui)
        self.tray_quit.triggered.connect(self.quit_app)
        self.tray_menu.addAction(self.tray_gmui)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.tray_toggle)
        self.tray_menu.addAction(self.tray_quit)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """点击托盘"""
        if reason == QSystemTrayIcon.Trigger:
            pass

    # -------------------- 状态管理 --------------------
    def set_state(self, state: str):
        """设置当前状态，拖拽状态会打断其他所有状态"""
        if state in ["drag", "move"]:
            self.clear_state(force=True)
        self.current_state = state
        if state is not None and self.blink_timer.isActive():
            self.blink_timer.stop()

    def clear_state(self, state: str = None, force: bool = False):
        """清理指定状态，无指定则清理全部，force=True强制清理"""
        if force:
            self.current_state = None
        elif state is None:
            self.current_state = None
        elif self.current_state == state:
            self.current_state = None
        
        if self.current_state is None and self.blink_anim_name is not False:
            self.blink_timer.start()

    def set_mouse(self):
        """初始化"""
        self.current_state = None
        self.has_dragged = False 
        self.is_dragging = False
        self.drag_pos = None
    
        self.enter_timer = QTimer(self)
        self.enter_timer.setSingleShot(True)
        self.enter_timer.timeout.connect(self.on_enter_timeout)
        
        self.set_pet_time()
        self.set_blink_anim()

        self.set_rest_reminder()
        self.set_sleep_reminder()

    # -------------------- 鼠标事件 --------------------
    def mousePressEvent(self, event):
        """鼠标按下事件 - 进入拖拽状态"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_pos = event.globalPos() - self.pos()
            self.has_dragged = False
            self.enter_timer.stop()
            self.reset_pet_timer()
        event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 触发拖拽动画"""
        if self.is_dragging:
            new_pos = event.globalPos() - self.drag_pos
            if new_pos != self.pos():
                self.has_dragged = True
                if self.current_state != "move":
                    self.set_state("move")
                    self.play_anim("move")
                    self.play_audio("move")
                self.move(new_pos)
            self.reset_pet_timer()
        event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 退出拖拽状态并播放对应结束动画"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            if self.has_dragged:
                # 拖拽结束
                self.play_anim("moveend")
                self.play_audio("moveend")
                self.clear_state("move")
                self.has_dragged = False
            else:
                # 点击事件
                self.on_click()
            self.reset_pet_timer()
        event.accept()

    def on_click(self):
        """处理点击事件"""
        if self.current_state == "pet":
            self.play_anim("petend")
            self.play_audio("petend")
            self.clear_state("pet")
        elif self.current_state == "enter":
            self.clear_state("enter")
        elif self.current_state is None:
            self.play_anim("click")
            self.play_audio("click")
        elif self.current_state == "move":
            pass
        else:
            self.clear_state()

    def on_speak(self, text: str):
        self.play_anim("speak", 1)
        self.reset_pet_timer()

    def enterEvent(self, event):
        """鼠标进入窗口 - 启动进入计时"""
        if self.current_state is None:
            in_config = self.action_config.get("inwindow", {})
            cod_value = in_config.get("cod", "")
            if cod_value and cod_value.isdigit():
                self.enter_timer.start(int(cod_value) * 1000)
                self.reset_pet_timer()
        event.accept()

    def leaveEvent(self, event):
        """鼠标离开窗口 - 清理进入状态并播放对应动画"""
        self.enter_timer.stop()
        if self.current_state == "enter":
            self.play_anim("outwindow")
            self.play_audio("outwindow")
            self.clear_state("enter")
            self.reset_pet_timer()
        event.accept()
    # -------------------- 眨眼动画 --------------------
    def set_blink_anim(self):
        # 眨眼动画相关
        self.blink_timer = QTimer(self)
        self.blink_anim_name = self.config.get("anim_blink")
        if self.blink_anim_name is not False:
            interval_seconds = 10
            try:
                blink_config = self.action_config.get("blink", {})
                cod_value = blink_config.get("cod", "")
                if cod_value:
                    interval_seconds = max(float(cod_value), 1)
            except:
                pass
            self.blink_timer.setInterval(int(interval_seconds * 1000))
            self.blink_timer.timeout.connect(self.play_blink_anim)
            self.blink_timer.start()

    def play_blink_anim(self):
        """播放眨眼动画（仅空闲时）"""
        if self.current_state is None and self.blink_anim_name:
            self.run_js(f"playtrack('{self.blink_anim_name}',1)")

    # -------------------- 摸摸动画 --------------------
    def set_pet_time(self):
        # 摸摸动画相关
        self.pet_timer = QTimer(self)
        self.pet_timer.setSingleShot(True)
        self.pet_timer.timeout.connect(self.on_pet_timeout)
        self.last_action_time = time.time()
        self.pet_trigger_minutes = self._parse_pet_time()
        if self.pet_trigger_minutes > 0:
            self.reset_pet_timer()

    def _parse_pet_time(self):
        """解析求摸摸动画触发时间（分钟）"""
        try:
            moveout_config = self.action_config.get("pet", {})
            cod_value = moveout_config.get("cod", "")
            if cod_value:
                seconds = float(cod_value)
                return seconds if seconds > 0 else 0
        except (ValueError, TypeError):
            pass  
        return 0

    def reset_pet_timer(self):
        """重置求摸摸动画计时器"""
        if self.pet_trigger_minutes > 0:
            self.pet_timer.setInterval(int(self.pet_trigger_minutes * 1000))
            self.pet_timer.start()
            self.last_action_time = time.time()

    def on_enter_timeout(self):
        """鼠标进入2秒后触发进入动画"""
        if self.current_state is None:
            self.play_anim("inwindow")
            self.play_audio("inwindow")
            self.set_state("enter")
        self.reset_pet_timer()

    def on_pet_timeout(self):
        """无操作达到指定时间触发求摸摸动画"""
        if self.pet_trigger_minutes <= 0:
            return
        elapsed = round(time.time() - self.last_action_time)
        if elapsed >= self.pet_trigger_minutes and self.current_state is None:
            self.play_anim("pet")
            self.set_state("pet")
        self.reset_pet_timer()

    # -------------------- 睡觉 --------------------
    def set_sleep_reminder(self):
        """设置睡觉提醒"""
        try:
            sleep_config = self.action_config.get("sleep", {})
            cod_value = sleep_config.get("cod", "")
            if cod_value and ":" in cod_value:
                target_hour, target_minute = map(int, cod_value.split(":"))
                now = time.localtime()
                now_seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
                target_seconds = target_hour * 3600 + target_minute * 60
                if target_seconds > now_seconds:
                    delay_ms = (target_seconds - now_seconds) * 1000
                else:
                    delay_ms = (24 * 3600 - now_seconds + target_seconds) * 1000
                self.sleep_timer = QTimer(self)
                self.sleep_timer.setSingleShot(True)
                self.sleep_timer.setInterval(delay_ms)
                self.sleep_timer.timeout.connect(self.on_sleep_timeout)
                self.sleep_timer.start()
                self.sleep_timer.timeout.connect(self.reset_sleep_timer)
        except (ValueError, TypeError):
            pass

    def reset_sleep_timer(self):
        """睡觉定时器"""
        try:
            sleep_config = self.action_config.get("sleep", {})
            cod_value = sleep_config.get("cod", "")
            if cod_value and ":" in cod_value and self.sleep_timer:
                self.sleep_timer.setInterval(24 * 60 * 60 * 1000)
                self.sleep_timer.start()
        except (ValueError, TypeError):
            pass

    def on_sleep_timeout(self):
        """睡觉提醒"""
        if self.current_state is None or self.current_state == "pet":
            self.play_anim("sleep")
            self.play_audio("sleep")
    # -------------------- 休息 --------------------
    def set_rest_reminder(self):
        """设置休息提醒"""
        try:
            rest_config = self.action_config.get("rest", {})
            cod_value = rest_config.get("cod", "")
            if cod_value:
                minutes = int(cod_value)
                if minutes > 0:
                    self.rest_timer = QTimer(self)
                    self.rest_timer.setInterval(minutes * 60 * 1000)
                    self.rest_timer.timeout.connect(self.on_rest_timeout)
                    self.rest_timer.start()
        except (ValueError, TypeError):
            pass

    def on_rest_timeout(self):
        """休息提醒"""
        if self.current_state is None or self.current_state == "pet":
            self.play_anim("rest")
            self.play_audio("rest")
    # -------------------- 页面 --------------------
    def setposition(self, x: int, y: int):
        """设置页面宽高"""
        old_width, old_height = self.width(), self.height()
        old_center_x = self.x() + old_width // 2
        old_center_y = self.y() + old_height // 2
        self.resize(x, y)
        new_x = old_center_x - x // 2
        new_y = old_center_y - y // 2
        self.move(new_x, new_y)
        if hasattr(self, 'input_widget'):
            new_history_width = max(200, min(x - 100, 350))
            self.input_widget.history_widget.setFixedWidth(new_history_width)

    def moveEvent(self, event):
        """跟随移动"""
        if hasattr(self, 'input_widget') and self.input_widget.history_widget.isVisible():
            delta = event.pos() - event.oldPos()
            hist_pos = self.input_widget.history_widget.pos()
            self.input_widget.history_widget.move(hist_pos.x() + delta.x(), hist_pos.y() + delta.y())
        super().moveEvent(event)

class InputWidget(QWidget):
    """独立的输入框组件"""
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.parent_window = parent

        self.alpha = 1
        self.drag_pos = None
        self.chat_history = []
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_all)


        self.init_ui()
        self.hide()


    def init_ui(self):
        self.panel_width = 300
        self.setFixedSize(0, 0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.history_widget = QWidget(self.parent_window)
        self.history_widget.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.history_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.history_widget.setFixedWidth(self.panel_width)
        self.history_widget.setMinimumHeight(0)
        self.history_widget.hide()

        self.history_widget.mousePressEvent = self.on_history_mouse_press
        self.history_widget.mouseMoveEvent = self.on_history_mouse_move
        self.history_widget.mouseReleaseEvent = self.on_history_mouse_release
        self.history_scroll = QScrollArea(self.history_widget)
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                background-color: rgba(218, 221, 228, 0.9);
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
        """)
        self.history_scroll.focusOutEvent = self.history_focus_out_event
        self.history_content = QWidget()
        self.history_content.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(8, 8, 8, 8)
        self.history_layout.setSpacing(5)
        self.history_layout.setAlignment(Qt.AlignTop)

        self.history_scroll.setWidget(self.history_content)
        scroll_layout = QVBoxLayout(self.history_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(self.history_scroll)
        self.main_animation = QPropertyAnimation(self, b"windowOpacity")
        self.main_animation.setDuration(100)
        self.history_animation = QPropertyAnimation(self.history_widget, b"windowOpacity")
        self.history_animation.setDuration(100)

    def set_opacity(self, value: float):
        """透明度"""
        opacity = max(0.01, min(float(value), 1.0))
        self.setWindowOpacity(opacity)
        self.alpha = opacity
        self.history_widget.setWindowOpacity(opacity)

    def history_focus_out_event(self, event):
        """历史文本区域失去焦点"""
        super(QScrollArea, self.history_scroll).focusOutEvent(event)
        if not self.history_scroll.hasFocus():
            self.start_hide_timer()

    def show_all(self):
        """同时显示输入框和历史区域"""
        self.show_message()

    def show_message(self):
        """显示历史区域"""
        if self.history_widget.isHidden():
            self.hide_timer.stop()
            self.parent_window.chat = True
            self.history_widget.setWindowOpacity(0)
            self.history_widget.show()
            self.history_animation.setStartValue(0)
            self.history_animation.setEndValue(self.alpha)
            self.history_animation.start()

    def hide_all(self):
        """隐藏"""
        global_pos =  QCursor.pos()
        if self.parent_window.chat and not self.history_scroll.hasFocus() and not self.history_widget.geometry().contains(global_pos):
            self.parent_window.chat = False
            self.main_animation.setStartValue(self.alpha)
            self.main_animation.setEndValue(0)
            self.main_animation.finished.connect(lambda: self.hide() if self.windowOpacity() == 0 else None)
            self.main_animation.start()
            self.history_animation.setStartValue(self.alpha)
            self.history_animation.setEndValue(0)
            self.history_animation.finished.connect(lambda: self.history_widget.hide() if self.history_widget.windowOpacity() == 0 else None)
            self.history_animation.start()
            
    def start_hide_timer(self):
        """隐藏计时器"""
        if (self.isVisible() or self.history_widget.isVisible()) and not self.history_scroll.hasFocus():
            self.hide_timer.start(3000)  # 3秒后隐藏
        
    def position_history_widget(self):
        """定位历史显示区域在输入框上方居中"""
        if not self.parent_window:
            return
        main_global_pos = self.parent_window.mapToGlobal(QPoint(0, 0))
        main_width, main_height = self.parent_window.width(), self.parent_window.height()
        history_x = main_global_pos.x() + (main_width - self.history_widget.width()) // 2
        history_y = main_global_pos.y() + (main_height - self.history_widget.height()) // 2
        self.history_widget.move(history_x, history_y)

    def wrap_text(self, text, max_width, font):
        """文本换行处理"""
        if not text:
            return ""
        fm = QFontMetrics(font)
        lines = []
        current_line = ""
        for original_line in text.split('\n'):
            if not original_line:
                lines.append("")
                continue
            current_line = ""
            for char in original_line:
                test_line = current_line + char
                text_width = fm.horizontalAdvance(test_line)
                if text_width > max_width and current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line += char
            if current_line:
                lines.append(current_line)
        return "\n".join(lines)
        
    def create_message_bubble(self, msg_type, text, time_str=None):
        """创建单个消息气泡"""
        bubble_container = QWidget()
        container_layout = QVBoxLayout(bubble_container)
        container_layout.setContentsMargins(0, 4, 0, 4)
        container_layout.setSpacing(2)
        bubble = QWidget()
        bubble_layout = QHBoxLayout(bubble)
        if msg_type == 'alret':
            bubble_layout.setContentsMargins(8, 2, 8, 2)
            max_text_width = 245
        else:
            bubble_layout.setContentsMargins(12, 8, 12, 8)
            max_text_width = 176
        font = QFont()
        font.setPointSize(10)
        wrapped_text = self.wrap_text(text, max_text_width, font)
        text_label = QLabel(wrapped_text)
        text_label.setWordWrap(True)
        text_label.setMaximumWidth(200)
        text_label.setFont(font)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setStyleSheet("""
            QLabel {
                padding: 0px;
                margin: 0px;
                text-align: left;
                white-space: pre-wrap;
            }
        """)
        
        bubble_layout.addWidget(text_label)
        if msg_type == 'user':
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #6eb4b3;
                    color: #080c15;
                    border-radius: 8px;
                }
            """)
            container_layout.setAlignment(Qt.AlignRight)
        elif msg_type == 'ai':
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #e8e8f1;
                    color: #080c15;
                    border-radius: 8px;
                }
            """)
            container_layout.setAlignment(Qt.AlignLeft)
        else:  # system
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #b9bdc7;
                    color: #292b36;
                    border-radius: 10px;
                }
            """)
            container_layout.setAlignment(Qt.AlignCenter)
            text_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(bubble)
        if time_str:
            time_label = QLabel(time_str)
            time_label.setStyleSheet("font-size: 10px; color: #999;")
            if msg_type == 'user':
                time_label.setAlignment(Qt.AlignRight)
            else:
                time_label.setAlignment(Qt.AlignLeft)
            container_layout.addWidget(time_label)
        return bubble_container

    def scroll_to_bottom(self):
        """滚动底部"""
        self.history_content.adjustSize()
        self.history_widget.adjustSize()
        doc_height = self.history_content.height()
        new_height = min(doc_height + 20, 200)
        self.history_widget.setFixedHeight(new_height)
        self.history_scroll.setFixedHeight(new_height)
        QApplication.processEvents()
        scroll_bar = self.history_scroll.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def update_chat_history(self, user_text=None, ai_text=None, system_text=None, time_param=False, is_incremental=True):
        """更新聊天历史显示"""
        def process_msg(msg_type, text, time_p):
            if not text:
                return []
            content_parts = text.split("^")
            msg_list = []
            total_parts = len(content_parts)
            for idx, part in enumerate(content_parts):
                part = part.strip()
                if not part:
                    continue
                current_time = ""
                is_last_part = idx == total_parts - 1
                if is_last_part:
                    if time_p is True:
                        current_time = time.strftime('%H:%M')
                    elif isinstance(time_p, str):
                        current_time = time_p
                msg = {
                    'type': msg_type,
                    'text': part,
                    'time': current_time if current_time else None
                }
                msg_list.append(msg)
            return msg_list
        new_msgs = []
        if user_text:
            new_msgs.extend(process_msg("user", user_text, time_param))
        if ai_text:
            new_msgs.extend(process_msg("ai", ai_text, time_param))
        if system_text:
            new_msgs.extend(process_msg("alret", system_text, time_param))
        self.chat_history.extend(new_msgs)
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
        # 增量更新
        if is_incremental and new_msgs:
            for msg in new_msgs:
                bubble = self.create_message_bubble(msg['type'], msg['text'], msg.get('time'))
                self.history_layout.addWidget(bubble)
            self.scroll_to_bottom()
            self.show_message()
            self.start_hide_timer()
        else:
            # 全量更新
            for i in reversed(range(self.history_layout.count())):
                widget = self.history_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            for msg in self.chat_history:
                bubble = self.create_message_bubble(msg['type'], msg['text'], msg.get('time'))
                self.history_layout.addWidget(bubble)
            self.scroll_to_bottom()

    def on_history_mouse_press(self, event):
        """记录拖拽起始位置"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.history_widget.frameGeometry().topLeft()
            self.show_message()
            self.hide_timer.stop()
            event.accept()

    def on_history_mouse_move(self, event):
        """拖拽"""
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            target_global_pos = event.globalPos() - self.drag_pos
            self.history_widget.move(target_global_pos)
            event.accept()

    def on_history_mouse_release(self, event):
        """重启计时器"""
        self.drag_pos = None
        self.start_hide_timer()
        event.accept()