import os

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtCore import Qt

from .url import get_exe_dir

def error(self,text="",s=1):
    msg_box = QMessageBox(self)
    msg_box.setWindowTitle("GMUI") 
    msg_box.setWindowIcon(QIcon(os.path.join(get_exe_dir(), "assets/gm00.ico")))
    if s == 1:
        icon_pixmap = "assets/gm01.ico"
        message = f"<b>哎呀，出错了。。。</b><br>不是导演的错，而是我的问题。<br><br>{text}"
    else:
        icon_pixmap = "assets/gm03.ico"
        message = f"{text}"
    msg_box.setIconPixmap(QPixmap(os.path.join(get_exe_dir(), icon_pixmap)).scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation))
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.NoButton)
    ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
    msg_box.setDefaultButton(ok_btn)
    style = """
    QMessageBox {
        background-color: #d0d1d8;
    }
    QPushButton {
        background-color: #080c15;
        color: #d0d1d8;
        border: none;
        padding: 4px 10px;
        border-radius: 1px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #2d3038;
    }
    QPushButton:pressed {
        background-color: #1c1c1e;
    }
    """
    msg_box.setStyleSheet(style)
    msg_box.exec_()

def yes_or_no(self,title="",text="",btn1_text="取消",btn2_text="确定",s=1):
    """确认取消"""
    msg_box = QMessageBox(self)
    msg_box.setWindowTitle(f"{title}")
    msg_box.setWindowIcon(QIcon(os.path.join(get_exe_dir(), "assets/gm00.ico")))
    if s == 1:
        icon_pixmap = "assets/gm02.ico"
    else:
        icon_pixmap = "assets/gm03.ico"
    msg_box.setIconPixmap(QPixmap(os.path.join(get_exe_dir(), icon_pixmap)).scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation))
    msg_box.setText(f"{text}")
    msg_box.setStandardButtons(QMessageBox.NoButton) 
    discard_btn = msg_box.addButton(f"{btn2_text}", QMessageBox.RejectRole)
    save_btn = msg_box.addButton(f"{btn1_text}", QMessageBox.AcceptRole)
    msg_box.setDefaultButton(save_btn)
    style = """
    QMessageBox {
        background-color: #d0d1d8;
    }
    QPushButton {
        background-color: #080c15;
        color: #d0d1d8;
        border: none;
        padding: 4px 10px;
        border-radius: 1px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #2d3038;
    }
    QPushButton:pressed {
        background-color: #1c1c1e;
    }
    """
    msg_box.setStyleSheet(style)
    msg_box.exec_()
    clicked_btn = msg_box.clickedButton()
    if clicked_btn == save_btn:
        return False
    elif clicked_btn == discard_btn:
        return True

def three_choice(self, title="保存", text="是否保存更改？",btn1="保存", btn2="不保存", btn3="先等等"):
    """三选一"""
    msg_box = QMessageBox(self)
    msg_box.setWindowTitle(f"{title}")
    msg_box.setIconPixmap(QPixmap(os.path.join(get_exe_dir(), "assets/gm02.ico")).scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation))
    msg_box.setText(f"{text}")
    msg_box.setStandardButtons(QMessageBox.NoButton)
    save_btn = msg_box.addButton(f"{btn1}", QMessageBox.AcceptRole)
    discard_btn = msg_box.addButton(f"{btn2}", QMessageBox.RejectRole)
    cancel_btn = msg_box.addButton(f"{btn3}", QMessageBox.RejectRole)
    msg_box.setDefaultButton(save_btn)
    style = """
    QMessageBox {
        background-color: #d0d1d8;
    }
    QPushButton {
        background-color: #080c15;
        color: #d0d1d8;
        border: none;
        padding: 4px 10px;
        border-radius: 1px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #2d3038;
    }
    QPushButton:pressed {
        background-color: #1c1c1e;
    }
    """
    msg_box.setStyleSheet(style)
    msg_box.exec_()
    clicked_btn = msg_box.clickedButton()
    if clicked_btn == save_btn:
        return 0
    elif clicked_btn == discard_btn:
        return 1
    else:
        return 2