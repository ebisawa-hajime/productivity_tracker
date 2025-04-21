import os
import json
import textwrap
import numpy as np
from datetime import datetime, timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.image import imread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QRadioButton, QButtonGroup, QLabel, QSizePolicy
)

class LogGraphWidget(FigureCanvas):
    def __init__(self, log_dir="logs", icon_dir="icons"):
        self.fig = Figure(figsize=(5, 3))
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.log_dir = log_dir
        self.icon_dir = icon_dir
        self.time_limit_minutes = 60  # default 3 hours
        self.range_mode = "day"  # or "week"

        self.ui = self.create_controls()
        self.update_graph()

    def create_controls(self):
        layout = QVBoxLayout()
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

        layout.addLayout(control_layout)
        layout.addWidget(self)

        container = QWidget()
        container.setLayout(layout)
        return container

    def on_time_limit_changed(self):
        index = self.time_limit_combo.currentIndex()
        self.time_limit_minutes = [60, 180, 360, 720][index]
        self.update_graph()

    def on_range_changed(self):
        self.range_mode = "day" if self.day_radio.isChecked() else "week"
        self.update_graph()

    def load_logs(self):
        if not os.path.exists(self.log_dir):
            return {}

        logs = {}
        today = datetime.today().date()
        for fname in os.listdir(self.log_dir):
            if not fname.endswith(".json"):
                continue
            try:
                date_str = fname.replace(".json", "")
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if self.range_mode == "day" and log_date != today:
                    continue
                elif self.range_mode == "week" and (today - log_date).days > 6:
                    continue
                with open(os.path.join(self.log_dir, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        logs[k] = logs.get(k, 0) + v
            except Exception:
                continue
        return logs

    def update_graph(self):
        self.axes.clear()
        log_data = self.load_logs()
        if not log_data:
            self.draw()
            return

        names = list(log_data.keys())
        total_minutes = [log_data[name] / 60 for name in names]
        limit = self.time_limit_minutes

        stacks = []
        for minutes in total_minutes:
            layers = []
            while minutes > limit:
                layers.append(limit)
                minutes -= limit
            layers.append(minutes)
            stacks.append(layers)

        max_layers = max(len(s) for s in stacks)
        x = np.arange(len(names))
        bottom = np.zeros(len(names))

        for layer_index in range(max_layers):
            heights = []
            for s in stacks:
                if layer_index < len(s):
                    heights.append(s[layer_index])
                else:
                    heights.append(0)
            self.axes.bar(x, heights, bottom=bottom, color="lightgray", edgecolor="black")
            bottom += heights

        for i, name in enumerate(names):
            wrapped = textwrap.fill(name, width=10)
            y = bottom[i] - (stacks[i][-1] / 2)
            self.axes.text(x[i], y, wrapped, ha='center', va='center', fontsize=9, color='black')
            icon_path = os.path.join(self.icon_dir, f"{name}.png")
            if os.path.exists(icon_path):
                try:
                    arr_img = imread(icon_path)
                    imagebox = OffsetImage(arr_img, zoom=0.15)
                    ab = AnnotationBbox(imagebox, (x[i], bottom[i] + 5), frameon=False)
                    self.axes.add_artist(ab)
                except Exception:
                    pass

        self.axes.set_ylim(0, self.time_limit_minutes * 1.1)
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(["" for _ in names])
        self.axes.set_ylabel("アクティブ時間（分）")
        self.axes.set_title("アプリ別アクティブ時間")
        self.fig.tight_layout()
        self.draw()
