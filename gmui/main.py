import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import psutil

from core.config import ConfigManager
from core.window import DesktopPetWindow


def set_cpu_affinity_to_last_core():
    cpu_count = psutil.cpu_count(logical=True)
    if cpu_count > 0:
        last_core = cpu_count - 1
        current_process = psutil.Process(os.getpid())
        current_process.cpu_affinity([last_core])

def main():
    """主程序"""
    set_cpu_affinity_to_last_core()

    os.environ["QT_FONT_DPI"] = "96"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    if hasattr(Qt, 'AA_DisableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)    

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = ConfigManager()
    
    pet_window = DesktopPetWindow(config)
    pet_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()