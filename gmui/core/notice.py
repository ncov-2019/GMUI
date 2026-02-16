# notice.py
import os
from plyer import notification
from .url import get_exe_url

resource_dir = get_exe_url()
def show_first_run_notice():
    """通知"""
    try:
        app_name = "GMUI"
        notification.notify(
            title=f"按下 Alt + ` 锁定GMUI",
            message="  ",
            timeout=5,
            app_name=app_name,
            app_icon=os.path.join(resource_dir, "assets/img/use.ico")
        )
    except Exception:
        pass

def notice(title: str, message: str):
    """通知"""
    try:
        app_name = "GMUI"
        notification.notify(
            title=title,
            message=message,
            timeout=5,
            app_name=app_name,
            app_icon=os.path.join(resource_dir, "assets/img/use.ico")
        )
    except Exception:
        pass