import win32gui, win32process, psutil, time
from logger import Logger

class WindowTracker:
    def __init__(self):
        self.current_app = None
        self.start_time = time.time()
        self.logger = Logger()
        self.log = self.logger.load_log()
        self.name_map = self.logger.load_name_map()
        self._running = True

    def get_log(self):
        return self.log

    def get_name_map(self):
        return self.name_map

    def set_name_map(self, new_map):
        self.name_map = new_map
        self.logger.save_name_map(new_map)

    def stop(self):
        self._running = False

    def get_active_app_name(self):
        hwnd = win32gui.GetForegroundWindow()
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
            return self.name_map.get(process_name, process_name)
        except Exception:
            return "Unknown"

    def track(self):
        try:
            while self._running:
                active_app = self.get_active_app_name()
                if active_app != self.current_app:
                    now = time.time()
                    if self.current_app:
                        duration = now - self.start_time
                        self.log[self.current_app] = self.log.get(self.current_app, 0) + duration
                        self.logger.save_log(self.log)
                    self.current_app = active_app
                    self.start_time = now
                time.sleep(1)
        except KeyboardInterrupt:
            print("Tracker stopped.")
