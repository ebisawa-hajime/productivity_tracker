import sys, os, json, textwrap
import numpy as np
from PySide6.QtWidgets import (
    QCheckBox,
    QApplication, QLabel, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QMenu,
    QSystemTrayIcon, QHBoxLayout, QSizePolicy, QHeaderView, QComboBox, QRadioButton, 
    QButtonGroup, QSpacerItem
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.image import imread
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib
matplotlib.rcParams['font.family'] = 'Yu Gothic'
from threading import Thread
from tracker import WindowTracker
from logger import Logger
from datetime import datetime, timedelta

def format_seconds(seconds):
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}m {secs}s"

def format_progress(current_sec, target_min):
    target_sec = target_min * 60
    if target_sec == 0:
        return "N/A"
    progress = min(current_sec / target_sec * 100, 100)
    return f"{progress:.1f}%"

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("目標時間の設定")
        self.setMinimumSize(0, 0)
        self.inputs = {}
        layout = QFormLayout()
        for app, time in current_settings.items():
            edit = QLineEdit(str(time))
            self.inputs[app] = edit
            layout.addRow(QLabel(app), edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_settings(self):
        return {
            app: int(edit.text()) if edit.text().isdigit() else 0
            for app, edit in self.inputs.items()
        }

class NameMapDialog(QDialog):
    def __init__(self, name_map, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表示名の編集")
        self.setMinimumSize(0, 0)
        self.inputs = {}
        self.checks = {}

        layout = QFormLayout()
        for process, name in name_map.items():
            container = QWidget()
            row_layout = QHBoxLayout()
            edit = QLineEdit(name)
            check = QCheckBox("表示")
            is_checked = parent.display_flags.get(process, True) if parent and hasattr(parent, 'display_flags') else True
            check.setChecked(is_checked)
            
            self.inputs[process] = edit
            self.checks[process] = check
            row_layout.addWidget(edit)
            row_layout.addWidget(check)
            container.setLayout(row_layout)
            layout.addRow(QLabel(process), container)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_updated_map(self):
        return {
            proc: edit.text() or proc
            for proc, edit in self.inputs.items()
        }

    def get_display_flags(self):
        return {
            proc: check.isChecked()
            for proc, check in self.checks.items()
        }

class LogGraphWidget(FigureCanvas):
    def __init__(self, log_dir="logs", icon_dir="icons"):
        self.fig = Figure(figsize=(5, 3))
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.log_dir = log_dir
        self.icon_dir = icon_dir
        self.time_limit_minutes = 180
        self.range_mode = "day"

        self.toggle_button = QPushButton("グラフ表示")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.toggled.connect(self.toggle_graph_visibility)

        self.ui = self._create_controls()
        self.update_graph({})
        self.toggle_graph_visibility(False)

    def _create_controls(self):
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout = QVBoxLayout(container)
        control_layout = QHBoxLayout()

        self.time_limit_combo = QComboBox()
        self.time_limit_combo.addItems(["60分", "180分", "360分", "720分"])
        self.time_limit_combo.setCurrentIndex(1)
        self.time_limit_combo.currentIndexChanged.connect(self.on_time_limit_changed)
        control_layout.addWidget(QLabel("時間上限:"))
        control_layout.addWidget(self.time_limit_combo)

        self.day_radio = QRadioButton("今日")
        self.week_radio = QRadioButton("1週間")
        self.day_radio.setChecked(True)
        self.range_group = QButtonGroup()
        self.range_group.addButton(self.day_radio)
        self.range_group.addButton(self.week_radio)
        self.day_radio.toggled.connect(self.on_range_changed)
        control_layout.addWidget(QLabel("表示範囲:"))
        control_layout.addWidget(self.day_radio)
        control_layout.addWidget(self.week_radio)

        control_layout.addWidget(self.toggle_button)
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(control_layout)
        layout.addWidget(self)
        self.setVisible(False)
        return container

    def toggle_graph_visibility(self, checked):
        self.setVisible(checked)
        self.toggle_button.setText("グラフ非表示" if checked else "グラフ表示")
        self.ui.adjustSize()

    def on_time_limit_changed(self):
        index = self.time_limit_combo.currentIndex()
        self.time_limit_minutes = [60, 180, 360, 720][index]
        self.update_graph(self.current_log)

    def on_range_changed(self):
        self.range_mode = "day" if self.day_radio.isChecked() else "week"
        self.update_graph(self.current_log)

    def update_graph(self, log_data):
        display_flags = self.parent().display_flags if hasattr(self.parent(), 'display_flags') else {}
        log_data = {k: v for k, v in log_data.items() if display_flags.get(k, True)}
        self.axes.clear()
        self.axes.set_ylim(0, self.time_limit_minutes * 1.1)
        self.current_log = log_data

        # Load additional logs if range_mode is 'week'
        if self.range_mode == "week":
            today = datetime.today().date()
            combined = log_data.copy()
            for i in range(1, 7):
                past_date = today - timedelta(days=i)
                fname = os.path.join(self.log_dir, f"{past_date}.json")
                if os.path.exists(fname):
                    with open(fname, "r", encoding="utf-8") as f:
                        day_log = json.load(f)
                        for k, v in day_log.items():
                            combined[k] = combined.get(k, 0) + v
            log_data = combined

        if not log_data:
            self.draw()
            return

        names = list(log_data.keys())
        total_minutes = [log_data[name] / 60 for name in names]

        bars = self.axes.bar(range(len(names)), total_minutes, color="lightgray")
        self.axes.set_ylabel("時間（分）")
        self.axes.set_title("アプリ別アクティブ時間")
        self.axes.set_xticks(range(len(names)))
        self.axes.set_xticklabels(["" for _ in names])

        for bar, name in zip(bars, names):
            wrapped = textwrap.fill(name, width=10)
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height() / 2
            self.axes.text(x, y, wrapped, ha='center', va='center', fontsize=9, color='black')

        self.fig.tight_layout()
        self.draw()

class TrackerApp(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.setWindowTitle("Window Activity Tracker")
        self.setMinimumSize(0, 0)

        self.logger = Logger()
        self.display_flags = self.logger.load_display_flags()
        self.settings = self.logger.load_settings()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("アクティブウィンドウの時間を記録中…")
        layout.addWidget(self.label)

        self.table = QTableWidget(0, 3)
        self.table.setMinimumSize(0, 0)
        self.table.setHorizontalHeaderLabels(["アプリ名", "累積時間", "進捗率"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self.graph = LogGraphWidget(log_dir="logs", icon_dir="icons")
        layout.addWidget(self.graph.ui)

        button_layout = QHBoxLayout()
        self.settings_button = QPushButton("目標時間を設定")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.name_map_button = QPushButton("表示名を編集")
        self.name_map_button.clicked.connect(self.open_name_map_dialog)
        button_layout.addStretch()
        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.name_map_button)
        layout.addLayout(button_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(1000)

        self.update_table()

    def update_table(self):
        log = self.tracker.get_log()
        name_map = self.tracker.get_name_map()
        sorted_log = dict(sorted(log.items(), key=lambda x: x[1], reverse=True))

        # フィルタリング：非表示のアプリは除外
        display_flags = self.display_flags
        filtered_log = {k: v for k, v in sorted_log.items() if display_flags.get(k, True)}

        self.table.setRowCount(len(filtered_log))
        for i, (title, sec) in enumerate(filtered_log.items()):
            display_name = name_map.get(title, title)
            goal = self.settings.get(title, 0)
            self.table.setItem(i, 0, QTableWidgetItem(display_name))
            self.table.setItem(i, 1, QTableWidgetItem(format_seconds(sec)))
            self.table.setItem(i, 2, QTableWidgetItem(format_progress(sec, goal)))

        self.graph.update_graph(filtered_log)

    def open_settings_dialog(self):
        name_map = self.tracker.get_name_map()
        for app in self.tracker.get_log().keys():
            if app not in self.settings and app in name_map:
                self.settings[app] = 0
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.get_settings()
            self.logger.save_settings(self.settings)
            self.update_table()

    def open_name_map_dialog(self):
        current_map = self.tracker.get_name_map()
        for app in self.tracker.get_log().keys():
            if app not in current_map and app not in current_map.values():
                current_map[app] = app
        dialog = NameMapDialog(current_map, self)
        if dialog.exec():
            new_map = dialog.get_updated_map()
            display_flags = dialog.get_display_flags()
            self.logger.save_name_map(new_map)
            self.display_flags = display_flags
            self.logger.save_display_flags(display_flags)
            self.tracker.set_name_map(new_map)
            self.tracker.set_name_map(new_map)
            self.logger.save_name_map(new_map)
            self.update_table()

    def closeEvent(self, event):
        self.tracker.stop()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tracker = WindowTracker()
    thread = Thread(target=tracker.track, daemon=True)
    thread.start()
    win = TrackerApp(tracker)
    win.show()
    sys.exit(app.exec())
