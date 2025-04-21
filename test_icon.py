import sys
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon

app = QApplication(sys.argv)

# 絶対パスで指定（←重要！）
icon_path = os.path.abspath("icon.ico")
print("[DEBUG] icon path:", icon_path)
print("[DEBUG] exists:", os.path.exists(icon_path))

icon = QIcon(icon_path)
tray = QSystemTrayIcon(icon)
menu = QMenu()
menu.addAction("終了", app.quit)
tray.setContextMenu(menu)
tray.setToolTip("Test Icon")
tray.show()

sys.exit(app.exec())