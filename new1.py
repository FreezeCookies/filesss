import subprocess, os, threading, time, re, requests, base64, json, platform, random, string, webbrowser
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import psutil
import uiautomator2 as u2
from multiprocessing import Pool, Manager
from queue import Queue
import signal
from PyQt5.QtGui import QBrush, QColor
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QTextEdit, QLabel,
                             QDialog, QLineEdit, QMessageBox, QSizePolicy, QComboBox, QSplitter, QStackedWidget, QRadioButton)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPixmap, QIcon, QTextCursor
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys
from io import BytesIO
import uuid
import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
# Backend functions
def get_system_path(filename="avt.png"):
    base_path = "D:\\system" if os.path.exists("D:\\") else "C:\\system"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    return os.path.join(base_path, filename)

def load_icon_from_url(url, filename="avt.png"):
    path = get_system_path(filename)
    if not os.path.exists(path):
        try:
            data = requests.get(url, timeout=5).content
            with open(path, "wb") as f:
                f.write(data)
        except Exception as e:
            print("Không tải được icon:", e)
            return None
    return QIcon(path)

reaction_map = {
    "TĂNG LIKE CHO BÀI VIẾT"         : ("Thích", 35),
    "TĂNG LOVE CHO BÀI VIẾT"         : ("Yêu thích", 56),
    "TĂNG HAHA CHO BÀI VIẾT"         : ("Haha", 63),
    "TĂNG WOW CHO BÀI VIẾT"          : ("Wow", 56),
    "TĂNG THƯƠNG THƯƠNG CHO BÀI VIẾT": ("Thương thương", 56),
    "TĂNG SAD CHO BÀI VIẾT"          : ("Buồn", 106),
    "TĂNG ANGRY CHO BÀI VIẾT"        : ("Phẫn nộ", 106),
    "TĂNG COMMENT CHO BÀI VIẾT"      : ("Bình luận", 250)
}

SECRET_KEY = ".zmatrix_keyencode"

def xor_encrypt_decrypt(data: str, key: str) -> str:
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encode_device_id(device_id: str) -> str:
    encrypted = xor_encrypt_decrypt(device_id, SECRET_KEY)
    return base64.b64encode(encrypted.encode()).decode()

def decode_device_id(encoded: str) -> str:
    try:
        decoded_bytes = base64.b64decode(encoded)
        decrypted = xor_encrypt_decrypt(decoded_bytes.decode(), SECRET_KEY)
        return decrypted
    except:
        return "INVALID_ID"

def get_device_id():
    is_android = os.path.exists('/storage/emulated/0')
    is_windows = platform.system() == 'Windows'
    if is_android:
        base_folder = '/storage/emulated/0/Android/.system/_FOLDER IMPORTANT_'
        try:
            os.makedirs(base_folder, exist_ok=True)
        except PermissionError:
            QMessageBox.critical(None, "Access Error", "No permission to access folder on Android. Please grant permissions or change folder.")
            raise RuntimeError("No permission to access folder on Android")
    elif is_windows:
        if os.path.exists('D:\\'):
            base_folder = 'D:\\.system\\_FOLDER IMPORTANT_'
        else:
            base_folder = 'C:\\.system\\_FOLDER IMPORTANT_'
    else:
        base_folder = '_FOLDER IMPORTANT_'
    os.makedirs(base_folder, exist_ok=True)
    config_path = os.path.join(base_folder, 'error_log.zip')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        filename = config.get('file')
        if not filename:
            filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.zip'
            config['file'] = filename
            with open(config_path, 'w') as f:
                json.dump(config, f)
    else:
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.zip'
        config = {'file': filename}
        with open(config_path, 'w') as f:
            json.dump(config, f)
    device_id_file = os.path.join(base_folder, filename)
    if not os.path.exists(device_id_file):
        big_number = str(random.randint(10**19, 10**20 - 1))
        random_id = f"Z-Matrix_{big_number[:8]}"
        encoded_id = encode_device_id(random_id)
        with open(device_id_file, 'w') as f:
            f.write(encoded_id)
        if is_windows:
            os.system(f'attrib +h "{base_folder}"')
            os.system(f'attrib +h "{device_id_file}"')
        return random_id
    else:
        with open(device_id_file, 'r') as f:
            encoded_id = f.read().strip()
        return decode_device_id(encoded_id)

def detect_debug_tools():
    suspicious_keywords = ["charles", "fiddler", "httptoolkit", "mitmproxy", "canary", "proxyman"]
    suspicious_ports = ["127.0.0.1:8000", "127.0.0.1:8080", "127.0.0.1:8888", "127.0.0.1:9090"]
    ssl_cert_vars = ["SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "PATH"]
    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    if os.environ.get("HTTP_TOOLKIT_ACTIVE", "").lower() == "true":
        return True
    for var in ssl_cert_vars + proxy_env_vars:
        val = os.environ.get(var, "").lower()
        if any(kw in val for kw in suspicious_keywords):
            return True
        if any(port in val for port in suspicious_ports):
            return True
    if os.environ.get("FIREFOX_PROXY", "") in suspicious_ports:
        return True
    try:
        for proc in psutil.process_iter(['name']):
            name = proc.info.get('name', '').lower()
            if any(kw in name for kw in suspicious_keywords) or 'wireshark' in name:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False

def auto_kill_if_debug_detected(interval=5):
    while True:
        if detect_debug_tools():
            QMessageBox.critical(None, "Debug Detected", "Debug tools detected. Application will exit. Please disable debugging tools.")
            raise SystemExit("Debug tools detected")
        time.sleep(interval)

import webbrowser
import requests
from PyQt5.QtWidgets import QMessageBox

def check_server():
    try:
        response = requests.get('https://zmatrixtool.x10.mx/Api/server_test.php', timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'status' in data and data['status'] == 'live':
            return True
        else:
            zalo = "https://zalo.me/g/axtnqv555"
            QMessageBox.critical(None, "Server Status", f"Đã có tool mới vui lòng cập nhật\nBox Zalo: {zalo}\nVui lòng tham gia group để nhận thông báo sớm nhất!")
            raise SystemExit("Server is under maintenance")
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(None, "Server Error", f"Connection error: {str(e)}\nPlease check your network.")
        raise SystemExit(f"Server connection error: {str(e)}")
    except ValueError:
        QMessageBox.critical(None, "Server Error", "Invalid server response. Please try again later.")
        raise SystemExit("Invalid server response")


def check_key_vip(key, hwid):
    try:
        response = requests.get(f'https://zmatrixtool.x10.mx/shop/data/check_key_vip.php?key={key}&hwid={hwid}', timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == "active" and data.get('message') == "Key hợp lệ.":
            with open('Z-Matrix_key_vip.txt', 'w') as file:
                file.write(key)
            return True, data.get('user', 'Unknown'), data.get('expiry', 'Unknown'), None
        else:
            if os.path.exists('Z-Matrix_key_vip.txt'):
                os.remove('Z-Matrix_key_vip.txt')
            return False, None, None, data.get('message', 'Key vip không hợp lệ hoặc đã hết hạn.')
    except requests.exceptions.RequestException as e:
        if os.path.exists('Z-Matrix_key_vip.txt'):
            os.remove('Z-Matrix_key_vip.txt')
        return False, None, None, f"Connection error: {str(e)}"
    except ValueError:
        if os.path.exists('Z-Matrix_key_vip.txt'):
            os.remove('Z-Matrix_key_vip.txt')
        return False, None, None, "Invalid server response."

def check_key_free(key):
    try:
        response = requests.get(f'https://zmatrixtool.x10.mx/Api/Check_key.php?key={key}', timeout=5)
        response.raise_for_status()
        data = response.json()['data']
        if data.get('status') == "success" and data.get('message') == "Key ĐÚNG":
            with open('Z-Matrix_key.txt', 'w') as file:
                file.write(key)
            if data.get('event'):
                expiry = data.get('expiry', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                expiry = datetime.now().replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S')
            return True, "Free", expiry, None
        else:
            if os.path.exists('Z-Matrix_key.txt'):
                os.remove('Z-Matrix_key.txt')
            return False, None, None, data.get('message', 'Key free không hợp lệ hoặc đã hết hạn.')
    except requests.exceptions.RequestException as e:
        if os.path.exists('Z-Matrix_key.txt'):
            os.remove('Z-Matrix_key.txt')
        return False, None, None, f"Connection error: {str(e)}"
    except ValueError:
        if os.path.exists('Z-Matrix_key.txt'):
            os.remove('Z-Matrix_key.txt')
        return False, None, None, "Invalid server response."

def get_elapsed_time(start_time):
    if start_time is None:
        return "00:00:00"
    elapsed = datetime.now() - start_time
    hours = elapsed.seconds // 3600
    minutes = (elapsed.seconds % 3600) // 60
    seconds = elapsed.seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Updated KeyInputDialog
class KeyInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lí key")
        self.setMinimumSize(400, 400)
        url = "https://zmatrixtool.x10.mx/key/avt.jpg"
        icon = load_icon_from_url(url)
        if icon:
            self.setWindowIcon(icon)
        self.theme = "blue"
        self.apply_theme()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        try:
            response = requests.get('https://zmatrixtool.x10.mx/key/avt.jpg', timeout=5)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.getvalue())
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        except requests.exceptions.RequestException as e:
            logo_label = QLabel("Không thể tải logo!")
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        self.device_id = get_device_id()
        device_layout = QHBoxLayout()
        self.device_label = QLabel(f"Device ID: {self.device_id}")
        device_layout.addWidget(self.device_label)
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copy")
        self.copy_btn.setFixedWidth(80)
        self.copy_btn.clicked.connect(self.copy_device_id)
        device_layout.addWidget(self.copy_btn)
        layout.addLayout(device_layout)

        self.label = QLabel("Vui lòng chọn loại key bạn muốn dùng:")
        layout.addWidget(self.label)

        self.key_type = QComboBox()
        self.key_type.addItems(["Free Key", "Vip Key"])
        layout.addWidget(self.key_type)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Nhập key vào đây")
        layout.addWidget(self.key_input)

        button_layout = QHBoxLayout()
        self.get_key_btn = QPushButton("Get here")
        self.get_key_btn.clicked.connect(self.open_key_link)
        button_layout.addWidget(self.get_key_btn)

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.check_key)
        button_layout.addWidget(self.submit_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel")
        self.cancel_btn.clicked.connect(self.cancel_and_exit)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def apply_theme(self):
        style_sheet = """
            QDialog {
                background: #ffffff;
                border-radius: 15px;
            }
            QLabel {
                font-size: 18px;
                color: #ad1457;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #fce4ec;
                color: #ad1457;
                padding: 12px;
                font-size: 16px;
                border: 2px solid #ff80ab;
                border-radius: 12px;
            }
            QLineEdit:hover {
                border: 2px solid #ec407a;
                background-color: #f8bbd0;
                font-size: 17px;
                color: #ad1457;
            }
            QComboBox {
                background-color: #fce4ec;
                color: #ad1457;
                padding: 12px;
                font-size: 16px;
                border: 2px solid #ff80ab;
                border-radius: 12px;
            }
            QComboBox:hover {
                border: 2px solid #ec407a;
                background-color: #f8bbd0;
                font-size: 17px;
                color: #ad1457;
            }
            QComboBox::drop-down {
                border-left: 2px solid #ff80ab;
                border-radius: 12px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff80ab, stop:1 #f06292);
                color: white;
                padding: 12px;
                font-size: 16px;
                border-radius: 12px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ec407a, stop:1 #d81b60);
                font-size: 17px;
                color: #ffffff;
            }
            QPushButton#cancel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d81b60, stop:1 #c2185b);
            }
            QPushButton#cancel:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c2185b, stop:1 #ad1457);
                font-size: 17px;
                color: #ffffff;
            }
            QPushButton#copy {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e91e63, stop:1 #d81b60);
            }
            QPushButton#copy:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d81b60, stop:1 #c2185b);
                font-size: 17px;
                color: #ffffff;
            }
            QLabel#loading {
                font-size: 18px;
                color: #ad1457;
                font-weight: bold;
            }
        """
        self.setStyleSheet(style_sheet)

    def copy_device_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.device_id)
        QMessageBox.information(self, "Copied", "Đã copy id device cho bạn.")

    def open_key_link(self):
        key_type = self.key_type.currentText()
        if key_type == "Free Key":
            webbrowser.open("https://zmatrixtool.x10.mx/getkey/")
        else:
            webbrowser.open("https://zmatrixtool.x10.mx/shop")

    def get_key(self):
        return self.key_input.text().strip()

    def check_key(self):
        key = self.key_input.text().strip()
        key_type = self.key_type.currentText()
        if not key:
            QMessageBox.critical(self, "Key Error", "Vui lòng nhập key!")
            return
        self.submit_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.get_key_btn.setEnabled(False)
        if key_type == "Free Key":
            success, key_name, expire_time, error_msg = check_key_free(key)
            self.submit_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.get_key_btn.setEnabled(True)
            if success:
                self.key_info = {"type": "Free", "name": key_name, "expire_time": expire_time}
                QMessageBox.information(self, "Success", "Key free đúng! Đang kết nối đến Server...")
                self.accept()
            else:
                QMessageBox.critical(self, "Key Error", error_msg)
        else:
            hwid = self.device_id
            success, key_name, expire_time, error_msg = check_key_vip(key, hwid)
            self.submit_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.get_key_btn.setEnabled(True)
            if success:
                self.key_info = {"type": "VIP", "name": key_name, "expire_time": expire_time}
                QMessageBox.information(self, "Success", "Key vip đúng! Đang kết nối đến Server...")
                self.accept()
            else:
                QMessageBox.critical(self, "Key Error", error_msg)

    def cancel_and_exit(self):
        raise SystemExit(0)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Thoát", "Bạn có chắc chắn muốn thoát?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            raise SystemExit(0)
        else:
            event.ignore()

# MainWindow
class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    update_table_signal = pyqtSignal(str, int, str, str, int, int, str)

    def __init__(self, key_info=None, zalo_link="Unknown"):
        super().__init__()
        self.key_info = key_info or {"type": "Unknown", "name": "Unknown", "expire_time": "Unknown"}
        self.zalo_link = zalo_link
        self.setWindowTitle("Golike FaceBook - ZMATRIX")
        self.resize(1360, 700)
        self.setMinimumSize(1000, 700)
        url = "https://zmatrixtool.x10.mx/key/avt.jpg"
        icon = load_icon_from_url(url)
        if icon:
            self.setWindowIcon(icon)
        self.devices = []
        self.device_names = {}
        self.device_notes = {}
        self.selected_devices = []
        self.running = False
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.job_data = {}
        self.device_rows = {}
        self.device_start_times = {}
        self.total_xu_all = 0
        self.min_delay = 1.5
        self.max_delay = 2.5
        self.min_reaction_delay = 0.5
        self.max_reaction_delay = 1.0
        self.skip_follow_page = False
        self.theme = "green_black"
        self.log_queue = Queue()
        self.log_thread = threading.Thread(target=self.process_log_queue, daemon=True)
        self.log_thread.start()
        # Thêm hai từ điển mới tại đây
        self.device_running = {}  # Từ điển lưu trạng thái chạy của từng thiết bị
        self.device_stop_events = {}  # Từ điển lưu stop_event cho từng thiết bị
        self.setup_ui()
        self.load_device_notes()
        self.update_device_list()
        self.apply_theme()
        self.log_signal.connect(self.log_message)
        self.update_table_signal.connect(self.add_job_to_table)

    def process_log_queue(self):
        while True:
            try:
                message = self.log_queue.get(timeout=1)
                self.log_signal.emit(message)
                self.log_queue.task_done()
            except:
                continue
        
    def update_skip_config(self):
        self.skip_follow_page = self.skip_yes_radio.isChecked()
        self.log_text.append(f"Đã chọn: {'Bỏ qua' if self.skip_follow_page else 'Không bỏ qua'} job Theo Dõi và Like Page")
    def start_device(self, device):
        if self.device_running.get(device, False):
            self.log_text.append(f"[{device}] Thiết bị đang chạy, không thể bắt đầu lại.")
            return
        try:
            self.min_delay = float(self.min_delay_input.text())
            self.max_delay = float(self.max_delay_input.text())
            self.min_reaction_delay = float(self.min_reaction_delay_input.text())
            self.max_reaction_delay = float(self.max_reaction_delay_input.text())
            if self.min_delay < 0 or self.max_delay < self.min_delay:
                self.log_text.append("Min delay mở Facebook phải >= 0 và Max delay phải >= Min delay!")
                return
            if self.min_reaction_delay < 0 or self.max_reaction_delay < self.min_reaction_delay:
                self.log_text.append("Min delay thả cảm xúc phải >= 0 và Max delay phải >= Min delay!")
                return
        except ValueError:
            self.log_text.append("Vui lòng nhập số hợp lệ cho Min và Max delay!")
            return
        
        self.device_running[device] = True
        self.device_stop_events[device].clear()
        self.device_start_times[device] = datetime.now()
        row = self.device_rows.get(device)
        if row is not None:
            start_btn = self.table.cellWidget(row, 9)
            stop_btn = self.table.cellWidget(row, 10)
            if start_btn and stop_btn:
                start_btn.setEnabled(False)
                stop_btn.setEnabled(True)
        
        self.log_text.append(f"[{device}] Bắt đầu làm việc")
        self.job_data[device] = {"stt": 0, "tongxu": 0}
        
        subprocess.run(f"adb -s {device} shell settings put system accelerometer_rotation 0", shell=True)
        subprocess.run(f"adb -s {device} shell settings put system user_rotation 0", shell=True)
        
        self.executor.submit(main, device, self, self.device_stop_events[device], 
                            self.min_delay, self.max_delay, 
                            self.min_reaction_delay, self.max_reaction_delay)

    def stop_device(self, device):
        if not self.device_running.get(device, False):
            self.log_text.append(f"[{device}] Thiết bị không chạy, không thể dừng.")
            return
        self.device_running[device] = False
        self.device_stop_events[device].set()
        row = self.device_rows.get(device)
        if row is not None:
            start_btn = self.table.cellWidget(row, 9)
            stop_btn = self.table.cellWidget(row, 10)
            if start_btn and stop_btn:
                start_btn.setEnabled(True)
                stop_btn.setEnabled(False)
            self.table.setItem(row, 8, QTableWidgetItem("N/A"))
        self.log_text.append(f"[{device}] Đã dừng nhiệm vụ.")
    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("main_widget")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Compact top navigation
        nav_widget = QWidget()
        nav_widget.setObjectName("nav")
        nav_widget.setFixedHeight(40)
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setSpacing(5)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        self.job_btn = QPushButton("GOLIKE FACEBOOK")
        self.job_btn.setObjectName("nav_btn")
        self.job_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        nav_layout.addWidget(self.job_btn)
        self.rename_btn = QPushButton("Rename Phone") 
        self.rename_btn.setObjectName("nav_btn")
        self.rename_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(2))
        nav_layout.addWidget(self.rename_btn)
        self.update_btn = QPushButton("Cập Nhật")
        self.update_btn.setObjectName("nav_btn")
        self.update_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        nav_layout.addWidget(self.update_btn)
        # Add Shop button
        self.shop_btn = QPushButton("Shop Key")
        self.shop_btn.setObjectName("nav_btn")
        self.shop_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(3))
        nav_layout.addWidget(self.shop_btn)
        self.theme_btn = QPushButton("Đổi Theme")
        self.theme_btn.setObjectName("nav_btn")
        self.theme_btn.clicked.connect(self.toggle_theme)
        nav_layout.addWidget(self.theme_btn)
        nav_layout.addStretch()
        main_layout.addWidget(nav_widget)

        # Content stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Job content (GOLIKE FACEBOOK tab)
        job_widget = QWidget()
        job_widget.setObjectName("job_widget")
        job_layout = QHBoxLayout(job_widget)  # Sử dụng HBox để chứa left_panel và right_panel
        job_layout.setSpacing(10)
        job_layout.setContentsMargins(5, 5, 5, 5)

        # Left panel (controls and info)
        left_panel = QWidget()
        left_panel.setObjectName("left_panel")
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(460)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Controls
        control_widget = QWidget()
        control_widget.setObjectName("card")
        control_layout = QHBoxLayout(control_widget)
        self.tick_all_btn = QPushButton("Chọn Tất Cả")
        self.tick_all_btn.setObjectName("action_btn")
        self.tick_all_btn.clicked.connect(self.toggle_all_checkboxes)
        control_layout.addWidget(self.tick_all_btn)
        self.start_btn = QPushButton("Bắt Đầu")
        self.start_btn.setObjectName("action_btn")
        self.start_btn.clicked.connect(self.start_jobs)
        control_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("action_btn")
        self.stop_btn.clicked.connect(self.stop_jobs)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        left_layout.addWidget(control_widget)

        # Delay Configuration (Open Facebook)
        delay_widget = QWidget()
        delay_widget.setObjectName("card")
        delay_main_layout = QVBoxLayout(delay_widget)
        delay_main_layout.setSpacing(10)
        title_label = QLabel("Cấu hình delay mở Facebook")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel#title {
                font-size: 16px;
                font-weight: normal;
                font-weight: 580;
                margin-bottom: 5px;
            }
        """)
        delay_main_layout.addWidget(title_label)
        delay_layout = QHBoxLayout()
        delay_layout.setSpacing(10)
        min_delay_label = QLabel("Min Delay (s):")
        min_delay_label.setObjectName("info")
        self.min_delay_input = QLineEdit("1.0")
        self.min_delay_input.setFixedWidth(60)
        self.min_delay_input.setPlaceholderText("Min delay")
        delay_layout.addWidget(min_delay_label)
        delay_layout.addWidget(self.min_delay_input)
        max_delay_label = QLabel("Max Delay (s):")
        max_delay_label.setObjectName("info")
        self.max_delay_input = QLineEdit("3.0")
        self.max_delay_input.setFixedWidth(60)
        self.max_delay_input.setPlaceholderText("Max delay")
        delay_layout.addWidget(max_delay_label)
        delay_layout.addWidget(self.max_delay_input)
        save_delay_btn = QPushButton("Lưu")
        save_delay_btn.setObjectName("action_btn")
        save_delay_btn.clicked.connect(self.save_delay_config)
        delay_layout.addWidget(save_delay_btn)
        delay_main_layout.addLayout(delay_layout)
        left_layout.addWidget(delay_widget)

        # Delay Configuration (Reaction)
        reaction_delay_widget = QWidget()
        reaction_delay_widget.setObjectName("card")
        reaction_delay_main_layout = QVBoxLayout(reaction_delay_widget)
        reaction_delay_main_layout.setSpacing(10)
        reaction_title_label = QLabel("Cấu hình delay thả cảm xúc")
        reaction_title_label.setObjectName("title")
        reaction_title_label.setAlignment(Qt.AlignCenter)
        reaction_title_label.setStyleSheet("""
            QLabel#title {
                font-size: 16px;
                font-weight: normal;
                font-weight: 580;
                margin-bottom: 5px;
            }
        """)
        reaction_delay_main_layout.addWidget(reaction_title_label)
        reaction_delay_layout = QHBoxLayout()
        reaction_delay_layout.setSpacing(10)
        min_reaction_delay_label = QLabel("Min Delay (s):")
        min_reaction_delay_label.setObjectName("info")
        self.min_reaction_delay_input = QLineEdit("2.0")
        self.min_reaction_delay_input.setFixedWidth(60)
        self.min_reaction_delay_input.setPlaceholderText("Min delay")
        reaction_delay_layout.addWidget(min_reaction_delay_label)
        reaction_delay_layout.addWidget(self.min_reaction_delay_input)
        max_reaction_delay_label = QLabel("Max Delay (s):")
        max_reaction_delay_label.setObjectName("info")
        self.max_reaction_delay_input = QLineEdit("4.0")
        self.max_reaction_delay_input.setFixedWidth(60)
        self.max_reaction_delay_input.setPlaceholderText("Max delay")
        reaction_delay_layout.addWidget(max_reaction_delay_label)
        reaction_delay_layout.addWidget(self.max_reaction_delay_input)
        save_reaction_delay_btn = QPushButton("Lưu")
        save_reaction_delay_btn.setObjectName("action_btn")
        save_reaction_delay_btn.clicked.connect(self.save_reaction_delay_config)
        reaction_delay_layout.addWidget(save_reaction_delay_btn)
        reaction_delay_main_layout.addLayout(reaction_delay_layout)
        left_layout.addWidget(reaction_delay_widget)

        # Bỏ qua theo dõi và like page
        skip_widget = QWidget()
        skip_widget.setObjectName("card")
        skip_main_layout = QVBoxLayout(skip_widget)
        skip_main_layout.setSpacing(10)
        skip_title_label = QLabel("Bỏ qua job Theo Dõi và Like Page")
        skip_title_label.setObjectName("title")
        skip_title_label.setAlignment(Qt.AlignCenter)
        skip_title_label.setStyleSheet("""
            QLabel#title {
                font-size: 16px;
                font-weight: normal;
                font-weight: 580;
                margin-bottom: 5px;
            }
        """)
        skip_main_layout.addWidget(skip_title_label)
        skip_layout = QHBoxLayout()
        skip_layout.setSpacing(10)
        skip_layout.addStretch()
        self.skip_no_radio = QRadioButton("Không")
        self.skip_no_radio.setObjectName("radio")
        self.skip_no_radio.setChecked(True)
        self.skip_yes_radio = QRadioButton("Có")
        self.skip_yes_radio.setObjectName("radio")
        skip_layout.addWidget(self.skip_no_radio)
        skip_layout.addSpacing(20)
        skip_layout.addWidget(self.skip_yes_radio)
        self.skip_yes_radio.toggled.connect(self.update_skip_config)
        skip_layout.addStretch()
        skip_main_layout.addLayout(skip_layout)
        left_layout.addWidget(skip_widget)

        # Key Info
        info_widget = QWidget()
        info_widget.setObjectName("card")
        info_layout = QVBoxLayout(info_widget)
        info_label = QLabel(
            f"Loại Key: {self.key_info['type']}\n"
            f"Tên: {self.key_info['name']}\n"
            f"Hạn: {self.key_info['expire_time']}\n"
            f"Zalo: {self.zalo_link}"
        )
        info_label.setObjectName("info")
        info_layout.addWidget(info_label)
        left_layout.addWidget(info_widget)

        # Instructions
        instructions_widget = QWidget()
        instructions_widget.setObjectName("card")
        instructions_layout = QVBoxLayout(instructions_widget)
        instructions_label = QLabel(
            "Hướng dẫn:\n"
            "1. Kết nối thiết bị Android qua ADB.\n"
            "2. Chọn thiết bị trong bảng.\n"
            "3. Vào app Golike -> Kiếm Thưởng -> Facebook.\n"
            "4. Nhấn 'Bắt Đầu' để chạy job.\n"
            "5. Theo dõi tiến trình và log.\n"
            "Lưu ý: Đảm bảo Golike và Facebook đã được cài."
        )
        instructions_label.setObjectName("info")
        instructions_layout.addWidget(instructions_label)
        left_layout.addWidget(instructions_widget)
        left_layout.addStretch()
        job_layout.addWidget(left_panel)

        # Right panel (table and logs)
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Table
        table_widget = QWidget()
        table_widget.setObjectName("card")
        table_layout = QVBoxLayout(table_widget)
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # Cập nhật số cột
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên Ghi Chú", "Thiết Bị", "Done", "FB ID", "Loại Job", "Xu", "Tổng Xu", "Thời Gian Hoạt Động", "Bắt Đầu", "Dừng"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        # Cập nhật chiều rộng cột
        self.table.setColumnWidth(0, 50)   # Chọn
        self.table.setColumnWidth(1, 130)  # Tên Ghi Chú
        self.table.setColumnWidth(2, 90)   # Thiết Bị
        self.table.setColumnWidth(3, 60)   # Done
        self.table.setColumnWidth(4, 100)  # FB ID
        self.table.setColumnWidth(5, 90)   # Loại Job
        self.table.setColumnWidth(6, 60)   # Xu
        self.table.setColumnWidth(7, 80)   # Tổng Xu
        self.table.setColumnWidth(8, 80)   # Thời Gian Hoạt Động
        self.table.setColumnWidth(9, 80)   # Bắt Đầu
        self.table.setColumnWidth(10, 80)  # Dừng
        self.table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.table)
        right_layout.addWidget(table_widget)

        # Logs
        log_widget = QWidget()
        log_widget.setObjectName("card")
        log_layout = QVBoxLayout(log_widget)
        log_label = QLabel("Logs")
        log_label.setObjectName("info")
        log_layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_widget)

        # Total Xu
        xu_widget = QWidget()
        xu_widget.setObjectName("card")
        xu_layout = QHBoxLayout(xu_widget)
        self.total_xu_label = QLabel("Tổng Xu: 0")
        self.total_xu_label.setObjectName("info")
        xu_layout.addWidget(self.total_xu_label)
        right_layout.addWidget(xu_widget)
        job_layout.addWidget(right_panel)
        self.content_stack.addWidget(job_widget)

        # Update content
        update_widget = QWidget()
        update_widget.setObjectName("update_widget")
        update_layout = QVBoxLayout(update_widget)
        update_card = QWidget()
        update_card.setObjectName("card")
        update_inner_layout = QVBoxLayout(update_card)
        update_title = QLabel("Thông Báo Cập Nhật")
        update_title.setObjectName("title")
        update_inner_layout.addWidget(update_title)
        update_content = QLabel(
            "<b>Phiên bản:</b> v2 (Update nhỏ)<br>"
            "<b>Ngày:</b> 8/09/2025<br><br>"
            "<b>Cập nhật:</b><br>"
            "• Thêm shop Zmatrix cho anh em mua key thẳng trên tool.<br>"
            "• Fix lỗi bấm lung tung.<br>"
            "• Thêm bỏ qua job Theo Dõi và Like Page.<br>"
            "• Thêm phần [Rename Device] cho dễ theo dõi.<br>"
            "<b>Thông tin cập nhật sau:</b><br>"
            "• Cập nhật thêm chức năng nuôi tài khoản Facebook.<br>"
            "• Cập nhật thêm chạy bao nhiêu job thì dừng cho mỗi thiết bị.<br>"
        )
        update_content.setObjectName("info")
        update_content.setWordWrap(True)
        update_inner_layout.addWidget(update_content)
        zalo_btn = QPushButton("Liên Hệ Zalo")
        zalo_btn.setObjectName("action_btn")
        zalo_btn.clicked.connect(lambda: webbrowser.open("https://zalo.me/g/axtnqv555"))
        update_inner_layout.addWidget(zalo_btn)
        update_layout.addWidget(update_card)
        update_layout.addStretch()
        self.content_stack.addWidget(update_widget)

        # Đổi tên phone tab
        rename_widget = QWidget()
        rename_widget.setObjectName("rename_widget")
        rename_layout = QVBoxLayout(rename_widget)
        rename_layout.setSpacing(10)
        rename_layout.setContentsMargins(5, 5, 5, 5)

        # Nút Lưu tất cả
        self.save_button = QPushButton("Lưu Tất Cả")
        self.save_button.setFixedWidth(280) 
        self.save_button.setObjectName("action_btn")
        self.save_button.clicked.connect(self.save_device_notes)
        rename_layout.addWidget(self.save_button, alignment=Qt.AlignCenter)  


        # Bảng thiết bị
        self.rename_table = QTableWidget()
        self.rename_table.setColumnCount(5)
        self.rename_table.setHorizontalHeaderLabels(["STT", "Tên Thiết Bị", "Trạng Thái", "Sửa Tên Ghi Chú", "Kiểm Tra"])
        self.rename_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rename_table.setAlternatingRowColors(True)
        self.rename_table.setColumnWidth(0, 70)   # STT
        self.rename_table.setColumnWidth(1, 270)  # Tên thiết bị
        self.rename_table.setColumnWidth(2, 230)  # Trạng thái
        self.rename_table.setColumnWidth(3, 250)  # Tên ghi chú
        self.rename_table.setColumnWidth(4, 100)  # Check
        self.rename_table.horizontalHeader().setStretchLastSection(True)
        self.rename_table.verticalHeader().setVisible(False)
        self.rename_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rename_layout.addWidget(self.rename_table)
        rename_layout.setContentsMargins(200, 15, 200, 30)  # left, top, right, bottom
        
        self.content_stack.addWidget(rename_widget)
        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.update_device_list)
        self.device_timer.start(5000)
        # Shop content
        shop_widget = QWidget()
        shop_widget.setObjectName("shop_widget")
        shop_layout = QVBoxLayout(shop_widget)
        shop_layout.setSpacing(10)
        shop_layout.setContentsMargins(5, 5, 5, 5)

        # Thanh trên: chứa nút reload nhỏ
        top_bar = QHBoxLayout()
        reload_button = QPushButton("⟳")
        reload_button.setFixedSize(40, 30)
        top_bar.addWidget(reload_button)
        shop_layout.addLayout(top_bar)

        # Web view for shop page
        shop_webview = QWebEngineView()
        shop_webview.setUrl(QUrl("https://zmatrixtool.x10.mx/shop"))
        shop_webview.setObjectName("shop_webview")
        shop_layout.addWidget(shop_webview)

        # Kết nối nút reload với webview
        reload_button.clicked.connect(shop_webview.reload)

        self.content_stack.addWidget(shop_widget)

        # Apply theme to shop webview
        shop_webview.setStyleSheet("""
            QWebEngineView#shop_webview {
                background: #2E2E2E;
                border: 2px solid #4DB6AC;
                border-radius: 6px;
            }
        """ if self.theme == "green_black" else """
            QWebEngineView#shop_webview {
                background: #2E2E2E;
                border: 2px solid #FF9999;
                border-radius: 6px;
            }
        """)
    def load_device_notes(self):
        """Chỉ đọc file device_notes.json, không ghi đè."""
        note_file = get_system_path("device_notes.json")
        if os.path.exists(note_file):
            with open(note_file, 'r') as f:
                self.device_notes = json.load(f)
        else:
            self.device_notes = {}

    def update_note(self, device, text):
        """Cập nhật tên ghi chú cho thiết bị."""
        self.device_notes[device] = text
    def save_device_notes(self):
        note_file = get_system_path("device_notes.json")
        with open(note_file, 'w') as f:
            json.dump(self.device_notes, f)
        self.log_text.append("Đã lưu tất cả tên ghi chú.")
        self.table.setRowCount(0)
        self.device_rows = {}
        for i, device in enumerate(self.devices, 1):
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)
            checkbox = QCheckBox()
            self.table.setCellWidget(row_count, 0, checkbox)
            self.table.setItem(row_count, 1, QTableWidgetItem(self.device_notes.get(device, f"Máy {i}")))
            self.table.setItem(row_count, 2, QTableWidgetItem(f"{self.device_names.get(device, 'Unknown')} ({device})"))
            self.table.setItem(row_count, 8, QTableWidgetItem("N/A"))
            self.device_rows[device] = row_count
        self.update_rename_table()
    
    def get_device_status(self, device_id):
        try:
            result = subprocess.check_output(
                ["adb", "-s", device_id, "get-state"],
                stderr=subprocess.STDOUT
            ).decode().strip()
            if result == "device":
                return "Online"
            else:
                return "Offline"
        except Exception as e:
            print("Lỗi khi lấy trạng thái thiết bị:", e)
            return "Offline"

    def update_rename_table(self):
        """Cập nhật bảng đổi tên thiết bị trong tab Đổi tên phone."""
        self.rename_table.setRowCount(0)
        for i, device in enumerate(self.devices, 1):
            row_count = self.rename_table.rowCount()
            self.rename_table.insertRow(row_count)
            self.rename_table.setRowHeight(row_count, 40)

            # Cột STT
            stt_item = QTableWidgetItem(str(i))
            stt_item.setTextAlignment(Qt.AlignCenter)
            self.rename_table.setItem(row_count, 0, stt_item)

            # Cột Tên thiết bị
            device_name = self.device_names.get(device, 'Unknown')
            self.rename_table.setItem(row_count, 1, QTableWidgetItem(f"{device_name} ({device})"))

            # Cột Trạng thái
            status = self.get_device_status(device)
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.rename_table.setItem(row_count, 2, status_item)

            # Cột Tên ghi chú
            note_edit = QLineEdit(self.device_notes.get(device, f"Máy {i}"))
            note_edit.setObjectName("note_edit")
            note_edit.textChanged.connect(lambda text, dev=device: self.update_note(dev, text))
            self.rename_table.setCellWidget(row_count, 3, note_edit)

            # Cột Check
            check_btn = QPushButton("Check")
            check_btn.setObjectName("action_btn")
            check_btn.clicked.connect(lambda _, dev=device: self.check_device(dev))
            self.rename_table.setCellWidget(row_count, 4, check_btn)


    def update_note(self, device, text):
        """Cập nhật tên ghi chú cho thiết bị."""
        self.device_notes[device] = text

    def check_device(self, device):
        """Thực hiện lệnh ADB để kiểm tra thiết bị."""
        try:
            # Trở về màn hình chính
            subprocess.run(f"adb -s {device} shell input keyevent 3", shell=True)
            time.sleep(1)
            # Vuốt lên
            subprocess.run(f"adb -s {device} shell input swipe 500 1000 500 200 300", shell=True)
            time.sleep(0.5)
            # Vuốt xuống
            subprocess.run(f"adb -s {device} shell input swipe 500 200 500 1000 300", shell=True)
            time.sleep(0.5)
            # Vuốt trái
            subprocess.run(f"adb -s {device} shell input swipe 800 500 200 500 300", shell=True)
            time.sleep(0.5)
            self.log_text.append(f"[{device}] Đã kiểm tra thiết bị thành công.")
        except Exception as e:
            self.log_text.append(f"[{device}] Lỗi khi kiểm tra thiết bị: {e}")
    def apply_theme(self):
      palette = QPalette()
      if self.theme == "black_pink":
        palette.setColor(QPalette.Window, QColor(28, 37, 38))  # #1C2526
        palette.setColor(QPalette.Base, QColor(28, 37, 38))
        palette.setColor(QPalette.Background, QColor(28, 37, 38))
        style_sheet = """
            QMainWindow, QWidget#main_widget {
                background: #1C2526 !important;
            }
            QWidget#left_panel, QWidget#right_panel, QWidget#job_widget, QWidget#update_widget {
                background: #1C2526 !important;
            }
            QWidget#nav {
                background: #2E2E2E;
                border-bottom: 1px solid #FF9999;
                padding: 3px;
            }
            QPushButton#nav_btn {
                background: #FF9999;
                color: #FFFFFF;
                padding: 6px;
                font-size: 12px;
                border-radius: 5px;
                border: none;
                font-weight: bold;
            }
            QPushButton#nav_btn:hover {
                background: #FF6666;
            }
            QWidget#card {
                background: #2E2E2E;
                border-radius: 6px;
                border: 1px solid #FF9999;
                padding: 8px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 580;
                color: #FF9999;
            }
            QLabel#info {
                font-size: 13px;
                color: #FFCCCB;
                font-weight: 500;
            }
            QPushButton#action_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9999, stop:1 #FF6666);
                color: #FFFFFF;
                padding: 8px;
                font-size: 13px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton#action_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6666, stop:1 #FF3333);
            }
            QPushButton#action_btn:disabled {
                background: #3A3A3A;
                color: #FF9999;
            }
            QTableWidget {
                background: #2E2E2E;
                color: #FFCCCB;
                border: 2px solid #FF9999;
                border-radius: 6px;
                font-size: 14px;
            }
            QHeaderView::section {
                background: #3A3A3A;
                color: #FFCCCB;
                padding: 5px;
                font-size: 13px;
                border: 1px solid #FF9999;
                border-right: 1px solid #FF9999; 
                font-weight: bold;
            }
            QTableWidget::item {
                border-right: 1px solid #FF9999; 
            }
            QTableWidget::item:alternate {
                background: #3A3A3A;
            }
            QTableWidget::item:selected {
                background: #FF9999;
                color: #FFFFFF;
            }
            QTextEdit {
                background: #2E2E2E;
                color: #FFCCCB;
                border: 2px solid #FF9999;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px;
            }
            QLineEdit {
                background-color: #2E2E2E;
                color: #FFCCCB;
                padding: 8px;
                font-size: 13px;
                border: 2px solid #FF9999;
                border-radius: 6px;
            }
            QLineEdit:hover {
                border: 2px solid #FF6666;
                background-color: #3A3A3A;
            }
            QRadioButton#radio {
                color: #FFCCCB;
                font-size: 13px;
                font-weight: 500;
            }
            QRadioButton#radio::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #FF9999;
                border-radius: 8px;
                background-color: #2E2E2E;
            }
            QRadioButton#radio::indicator:checked {
                background-color: #FF6666;
                border: 2px solid #FF3333;
            }
            QRadioButton#radio::indicator:hover {
                border: 2px solid #FF6666;
            }
        """
      if self.theme == "green_black":# green_black
        palette.setColor(QPalette.Window, QColor(18, 32, 28))  # #12201C
        palette.setColor(QPalette.Base, QColor(18, 32, 28))
        palette.setColor(QPalette.Background, QColor(18, 32, 28))
        style_sheet = """
            QMainWindow, QWidget#main_widget {
                background: #12201C !important;
            }
            QWidget#left_panel, QWidget#right_panel, QWidget#job_widget, QWidget#update_widget {
                background: #12201C !important;
            }
            QWidget#nav {
                background: #1E2F29;
                border-bottom: 1px solid #4DB6AC;
                padding: 3px;
            }
            QPushButton#nav_btn {
                background: #4DB6AC;
                color: #FFFFFF;
                padding: 6px;
                font-size: 12px;
                border-radius: 5px;
                border: none;
                font-weight: bold;
            }
            QPushButton#nav_btn:hover {
                background: #26A69A;
            }
            QWidget#card {
                background: #1E2F29;
                border-radius: 6px;
                border: 1px solid #4DB6AC;
                padding: 8px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 580;
                color: #4DB6AC;
            }
            QLabel#info {
                font-size: 13px;
                color: #80CBC4;
                font-weight: 500;
            }
            QPushButton#action_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4DB6AC, stop:1 #26A69A);
                color: #FFFFFF;
                padding: 8px;
                font-size: 13px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton#action_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #26A69A, stop:1 #00897B);
            }
            QPushButton#action_btn:disabled {
                background: #2A3D38;
                color: #4DB6AC;
            }
            QTableWidget {
                background: #1E2F29;
                color: #80CBC4;
                border: 2px solid #4DB6AC;
                border-radius: 6px;
                font-size: 14px;
            }
            QHeaderView::section {
                background: #2A3D38;
                color: #80CBC4;
                padding: 5px;
                font-size: 13px;
                border: 1px solid #4DB6AC;
                border-right: 1px solid #4DB6AC; 
                font-weight: bold;
            }
            QTableWidget::item {
                border-right: 1px solid #4DB6AC; 
            }
            QTableWidget::item:alternate {
                background: #2A3D38;
            }
            QTableWidget::item:selected {
                background: #4DB6AC;
                color: #FFFFFF;
            }
            QTextEdit {
                background: #1E2F29;
                color: #80CBC4;
                border: 2px solid #4DB6AC;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px;
            }
            QLineEdit {
                background-color: #1E2F29;
                color: #80CBC4;
                padding: 8px;
                font-size: 13px;
                border: 2px solid #4DB6AC;
                border-radius: 6px;
            }
            QLineEdit:hover {
                border: 2px solid #26A69A;
                background-color: #2A3D38;
            }
            QRadioButton#radio {
                color: #80CBC4;
                font-size: 13px;
                font-weight: 500;
            }
            QRadioButton#radio::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #4DB6AC;
                border-radius: 8px;
                background-color: #1E2F29;
            }
            QRadioButton#radio::indicator:checked {
                background-color: #26A69A;
                border: 2px solid #00897B;
            }
            QRadioButton#radio::indicator:hover {
                border: 2px solid #26A69A;
            }
        """
      self.setPalette(palette)
      main_widget = self.findChild(QWidget, "main_widget")
      if main_widget:
        main_widget.setPalette(palette)
      self.setStyleSheet(style_sheet)

    def toggle_theme(self):
        themes = ["black_pink", "green_black"]
        current_index = themes.index(self.theme)
        self.theme = themes[(current_index + 1) % len(themes)]
        self.apply_theme()

    def toggle_all_checkboxes(self):
        all_checked = all(self.table.cellWidget(row, 0).isChecked() for row in range(self.table.rowCount()) if self.table.cellWidget(row, 0))
        new_state = Qt.Unchecked if all_checked else Qt.Checked
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setCheckState(new_state)

    def update_device_list(self):
        if self.device_running:  # Kiểm tra nếu có thiết bị đang chạy
            for device in self.device_running:
                if self.device_running.get(device, False):  # Chỉ cập nhật cho thiết bị đang chạy
                    if device in self.device_rows:
                        row = self.device_rows[device]
                        start_time = self.device_start_times.get(device)
                        self.table.setItem(row, 8, QTableWidgetItem(get_elapsed_time(start_time)))
            return
        current_devices = get_devices()
        if current_devices != self.devices:
            self.devices = current_devices
            self.device_names = {}
            self.table.setRowCount(0)
            self.device_rows = {}
            for i, device in enumerate(self.devices, 1):
                try:
                    name = subprocess.run(f"adb -s {device} shell getprop ro.product.model",
                                        shell=True, capture_output=True, text=True).stdout.strip()
                    self.device_names[device] = name if name else "Unknown"
                except:
                    self.device_names[device] = "Unknown"
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                checkbox = QCheckBox()
                self.table.setCellWidget(row_count, 0, checkbox)
                self.table.setItem(row_count, 1, QTableWidgetItem(self.device_notes.get(device, f"Máy {i}")))
                self.table.setItem(row_count, 2, QTableWidgetItem(f"{self.device_names.get(device, 'Unknown')} ({device})"))
                self.table.setItem(row_count, 8, QTableWidgetItem("N/A"))
                
                # Thêm nút Bắt đầu
                start_btn = QPushButton("Bắt Đầu")
                start_btn.setObjectName("action_btn")
                start_btn.clicked.connect(lambda _, dev=device: self.start_device(dev))
                self.table.setCellWidget(row_count, 9, start_btn)
                
                # Thêm nút Dừng
                stop_btn = QPushButton("Dừng")
                stop_btn.setObjectName("action_btn")
                stop_btn.setEnabled(False)  # Ban đầu nút Dừng bị vô hiệu hóa
                stop_btn.clicked.connect(lambda _, dev=device: self.stop_device(dev))
                self.table.setCellWidget(row_count, 10, stop_btn)
                
                self.device_rows[device] = row_count
                self.device_running[device] = False  # Khởi tạo trạng thái không chạy
                self.device_stop_events[device] = threading.Event()  # Khởi tạo stop_event
            self.update_rename_table()  # Cập nhật bảng đổi tên
    def save_delay_config(self):
        try:
            min_delay = float(self.min_delay_input.text())
            max_delay = float(self.max_delay_input.text())
            if min_delay < 0 or max_delay < min_delay:
                QMessageBox.critical(self, "Lỗi", "Min delay phải >= 0 và Max delay phải >= Min delay!")
                return
            self.min_delay = min_delay
            self.max_delay = max_delay
            self.log_text.append(f"Đã lưu cấu hình delay mở Facebook: Min = {min_delay}s, Max = {max_delay}s")
        except ValueError:
            QMessageBox.critical(self, "Lỗi", "Vui lòng nhập số hợp lệ cho Min và Max delay!")

    def save_reaction_delay_config(self):
        try:
            min_reaction_delay = float(self.min_reaction_delay_input.text())
            max_reaction_delay = float(self.max_reaction_delay_input.text())
            if min_reaction_delay < 0 or max_reaction_delay < min_reaction_delay:
                QMessageBox.critical(self, "Lỗi", "Min delay thả cảm xúc phải >= 0 và Max delay phải >= Min delay!")
                return
            self.min_reaction_delay = min_reaction_delay
            self.max_reaction_delay = max_reaction_delay
            self.log_text.append(f"Đã lưu cấu hình delay thả cảm xúc: Min = {min_reaction_delay}s, Max = {max_reaction_delay}s")
        except ValueError:
            QMessageBox.critical(self, "Lỗi", "Vui lòng nhập số hợp lệ cho Min và Max delay thả cảm xúc!")

    def start_jobs(self):
        self.update_device_list()
        if not self.devices:
            self.log_text.append("Không tìm thấy thiết bị nào! Vui lòng kết nối thiết bị qua ADB.")
            return
        selected_devices = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                device_info = self.table.item(row, 2).text()
                device_id = device_info.split('(')[-1].strip(')')
                selected_devices.append(device_id)
        if not selected_devices:
            self.log_text.append("Vui lòng chọn ít nhất một thiết bị!")
            return
        for device in selected_devices:
            if not self.device_running.get(device, False):  # Chỉ chạy thiết bị chưa chạy
                self.start_device(device)
            else:
                self.log_text.append(f"[{device}] Thiết bị đã chạy, bỏ qua.")
        # Cập nhật trạng thái nút chính
        any_running = any(self.device_running.get(device, False) for device in self.device_running)
        self.start_btn.setEnabled(not any_running)
        self.stop_btn.setEnabled(any_running)
        self.tick_all_btn.setEnabled(not any_running)
        self.log_text.append(f"Bắt đầu công việc cho {len(selected_devices)} thiết bị: {', '.join(selected_devices)}")

    def stop_jobs(self):
        for device in list(self.device_running.keys()):
            if self.device_running.get(device, False):
                self.stop_device(device)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.tick_all_btn.setEnabled(True)
        self.log_text.append("Đã dừng tất cả nhiệm vụ.")

    def add_job_to_table(self, device, stt, fb_id, fb_job, xu_job, tongxu, timestamp):
        row = self.device_rows.get(device)
        if row is None:
            for r in range(self.table.rowCount()):
                item = self.table.item(r, 2)
                if item and device in item.text():
                    row = r
                    self.device_rows[device] = r
                    break
        if row is None:
            try:
                self.log_text.append(f"[WARN] Không tìm thấy hàng cho device {device}. Bỏ qua cập nhật Done.")
            except:
                pass
            return
        self.table.setItem(row, 3, QTableWidgetItem(str(stt)))
        self.table.setItem(row, 4, QTableWidgetItem(fb_id))
        self.table.setItem(row, 5, QTableWidgetItem(fb_job))
        self.table.setItem(row, 6, QTableWidgetItem(str(xu_job)))
        self.table.setItem(row, 7, QTableWidgetItem(str(tongxu)))
        self.table.setItem(row, 8, QTableWidgetItem(timestamp))
        if device in self.job_data:
            self.job_data[device]["stt"] = stt
            self.job_data[device]["tongxu"] = tongxu
        self.update_total_xu()

    def update_total_xu(self):
        self.total_xu_all = sum(data["tongxu"] for data in self.job_data.values())
        self.total_xu_label.setText(f"Tổng Xu: {self.total_xu_all}")

    def log_message(self, message):
        self.log_text.append(message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        if self.running:
            reply = QMessageBox.question(self, "Thoát", "Công việc đang chạy. Bạn có chắc chắn muốn thoát? Hành động này sẽ dừng tất cả công việc.",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        else:
            reply = QMessageBox.question(self, "Thoát", "Bạn có chắc chắn muốn thoát?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.running:
                self.stop_jobs()
            event.accept()
            raise SystemExit(0)
        else:
            event.ignore()

def get_devices():
    devices = []
    output = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.strip().split("\n")[1:]
    for line in output:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device": 
            devices.append(parts[0])
    return list(dict.fromkeys(devices))

def check_type(d):
    for golike_job, (fb_job, xu_job) in reaction_map.items():
        if d(text=golike_job).exists:
            return golike_job, fb_job, xu_job
    return "none", None, 0

def check_job(d):
    xml = d.dump_hierarchy()
    job_id = re.search(r"Job Id:\s*(\d+)", xml).group(1) if re.search(r"Job Id:\s*(\d+)", xml) else None
    fb_id_golike = re.search(r"Fb Id:\s*([^\s<]+)", xml).group(1).strip() if re.search(r"Fb Id:\s*([^\s<]+)", xml) else None
    if fb_id_golike:
        fb_id_golike = fb_id_golike.strip().strip('"').strip("'")
    
    try:
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5,ru;q=0.4',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://id.traodoisub.com',
            'Priority': 'u=1, i',
            'Referer': 'https://id.traodoisub.com/',
            'Sec-CH-UA': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = {'link': f'https://facebook.com/{fb_id_golike}'}
        retries = 3
        for _ in range(retries):
            response = requests.post('https://id.traodoisub.com/api.php', headers=headers, data=data)
            response.raise_for_status()
            try:
                id_data = response.json()
            except ValueError:
                fb_id = "none"
                return job_id, fb_id
            if id_data.get('success') == 200 and id_data.get('code') == 200:
                fb_id = id_data.get('id', 'none')
                break
            else:
                error_value = id_data.get('error', '')
                if error_value and "thao tác chậm lại" in error_value.lower():
                    time.sleep(2)
                    continue
                else:
                    fb_id = "none"
                    return job_id, fb_id
        else:
            fb_id = "none"
    except Exception as e:
        print("Lỗi khi lấy id:", e)
        fb_id = "none"
    return job_id, fb_id

def bao_loi(d):
    if d(text = "OK").exists(timeout=5):
        d(text = "OK").click()
        time.sleep(0.5)
    d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.3)
    time.sleep(0.5)
    if d(text="Báo lỗi").exists(timeout=5):
       d(text="Báo lỗi").click()
    d.swipe(0.5, 0.8, 0.5, 0.3, duration=0.3)
    time.sleep(1)
    if d(text="Gửi báo cáo").exists(timeout=7):
      d(text="Gửi báo cáo").click()
    time.sleep(2)
    if d(text="OK").exists(timeout=4): 
       d(text="OK").click()
    d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1) 
    d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)

def reset_golike(d, device, gui, tongxu, stt):
    try:
        os.system(f"adb -s {device} shell am force-stop com.golike")
        time.sleep(1)
        os.system(f"adb -s {device} shell am start -n com.golike/.MainActivity -a android.intent.action.VIEW -d 'golike://reward/facebook' >nul 2>&1")
        time.sleep(15)

        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(2)
        if not d(text="Kiếm Thưởng").exists(timeout=20):
            return reset_golike(d, device, gui, tongxu, stt)
        d(text="Kiếm Thưởng").click()
        time.sleep(0.5)
        if d(text="Kiếm Thưởng").exists(timeout=5):
            d(text="Kiếm Thưởng").click()
        time.sleep(1)
        if d(text="Facebook").exists(timeout=15):
            d(text="Facebook").click()
        time.sleep(2)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(1)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(2)

        # Thông báo giới hạn job
        if d(resourceId="swal2-content").exists(timeout=5):
            print(f"[{device}] Xuất hiện thông báo giới hạn job, dừng luồng.")
            gui.log_queue.put(f"[{device}] Đã đạt giới hạn công việc, dừng thiết bị này.")
            gui.update_table_signal.emit(device, stt, "N/A", "Stopped", 0, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
            return False

        return True
    except:
        return reset_golike(d, device, gui, tongxu, stt)
    
def main(device, gui, stop_event, min_delay=1.5, max_delay=2.5, min_reaction_delay=0.5, max_reaction_delay=1.0):
    tongxu = stt = 0
    while True:
        try:
            d = u2.connect(device)
            break
        except:
            if stop_event.is_set():
                return
            continue
    while not stop_event.is_set():
        try:
            d.swipe(0.5, 0.7, 0.5, 0.6, duration=0.1)
            if d(textContains="Còn lại").exists(timeout=25):
                d(textContains="Còn lại").click()
            else:
                raise Exception("Không tìm thấy Job")
            time.sleep(0.5)
            if d(text="OK").exists(timeout=3.5):
                d(text="OK").click()
                time.sleep(0.3)
                if d(textContains="Còn lại").exists(timeout=10):
                    d(textContains="Còn lại").click()
                else:
                    raise Exception("Không tìm thấy Job")
            time.sleep(1)
            d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
            d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)
            time.sleep(1.1)
            golike_job, fb_job, xu_job = check_type(d)
            if golike_job == "none":
                if gui.skip_follow_page:
                    bao_loi(d)
                    if random.random() < 0.1:
                        gui.log_queue.put(f"[{device}] Đã bỏ qua job Theo Dõi hoặc Like Page")
                    continue
                time.sleep(1.5)
                if d(text="Facebook").exists:
                    d(text="Facebook").click()
                else:
                    d(text="Facebook Làm việc bằng ứng dụng Facebook trên điện thoại. chevron_right").click()
                time.sleep(random.uniform(min_delay, max_delay))
                map_type_job = {
                    "Thích": 40,
                    "Theo dõi": 65
                }
                for fb_job, xu_job in map_type_job.items():
                    if d(text=fb_job).exists:
                        d(text=fb_job).click()
                        break
                time.sleep(1)
                subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity -f 0x20000000", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                if d(text="Hoàn thành").exists(timeout=5):
                    d(text="Hoàn thành").click()
                    time.sleep(1)
                    if d(text="OK").exists(timeout=3):
                        d(text="OK").click()
                    tongxu += xu_job
                    stt += 1
                    gui.update_table_signal.emit(device, stt, "NONE", fb_job, xu_job, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
                else:
                    bao_loi(d)
                    gui.log_queue.put(f"[{device}] Đã báo lỗi cho công việc")
                continue
            job_id, fb_id = check_job(d)
            if fb_id == "none":
                bao_loi(d)
                gui.log_queue.put(f"[{device}] Đã báo lỗi do bài viết không hợp lệ")
                continue
            if d(text="Click để Copy bình luận").exists:
                d(text="Click để Copy bình luận").click()
            time.sleep(1)
            if d(text="Facebook").exists:
                d(text="Facebook").click()
            else:
                d(text="Facebook Làm việc bằng ứng dụng Facebook trên điện thoại. chevron_right").click()
            time.sleep(random.uniform(min_delay, max_delay))
            text = f"S:_I{job_id}:{fb_id}"
            s = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            link = s.rstrip('=')
            command = f'adb -s {device} shell am start -a android.intent.action.VIEW -d "fb://native_post/{link}" -f 0x10008000'
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            xml = d.dump_hierarchy()
            if "Nội dung này không hiển thị" in xml or "Điều này có thể xảy ra khi nội dung đã bị gỡ" in xml:
                subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity --activity-reorder-to-front",
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                bao_loi(d)
                gui.log_queue.put(f"[{device}] Đã báo lỗi do bài viết không hiển thị")
                continue
            time.sleep(1)
            success = False
            for i in range(4):
                if d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").exists:
                    if fb_job == "Bình luận":
                        try:
                            d(description=f"{fb_job}").click()
                            time.sleep(1)
                            d.clipboard
                            os.system(f"adb -s {device} shell input keyevent 279")
                            time.sleep(1)
                            d(description="Gửi").click()
                            success = True
                        except:
                            success = False
                    else:
                        time.sleep(0.5)
                        try:
                            d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").long_click()
                            if d(description=f"{fb_job}").exists:
                                d(description=f"{fb_job}").click()
                                success = True
                            else:
                                d(text="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").click()
                                if fb_job == "Thích":
                                    success = True
                                else:
                                    success = False
                        except:
                            success = False
                    time.sleep(random.uniform(min_reaction_delay, max_reaction_delay))
                    break
                else:
                    d.swipe(0.4, 0.8, 0.4, 0.5, duration=0.1)
                    time.sleep(1)
            subprocess.run(
                f"adb -s {device} shell am start -n com.golike/.MainActivity -f 0x20000000",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)
            job_completed = False
            if success:
                if d(text="Hoàn thành").exists(timeout=5):
                    d(text="Hoàn thành").click()
                    time.sleep(1)
                    if d(text="OK").exists(timeout=3):
                        d(text="OK").click()
                    job_completed = True
                else:
                    bao_loi(d)
                    gui.log_queue.put(f"[{device}] Không tìm thấy nút Hoàn thành, đã báo lỗi job.")
            else:
                bao_loi(d)
                gui.log_queue.put(f"[{device}] Không tìm thấy nút Like, đã báo lỗi job.")
            if job_completed:
                tongxu += xu_job
                stt += 1
                gui.update_table_signal.emit(
                    device, stt, fb_id, fb_job, xu_job, tongxu,
                    get_elapsed_time(gui.device_start_times.get(device))
                )
            time.sleep(1)
            if d(text="OK").wait(timeout=10):
                try:
                    d(text="OK").click()
                except:
                    try:
                        x1, y1, x2, y2 = d(text="OK").bounds()
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        d.click(center_x, center_y)
                    except:
                        pass
            d.swipe(0.5, 0.7, 0.5, 0.6, duration=0.1)
            d.swipe(0.5, 0.6, 0.5, 0.7, duration=0.1)
            time.sleep(1)
        except Exception as e:
            if stop_event.is_set():
                return
            gui.log_queue.put(f"[{device}] Exception: {e}")
            result = reset_golike(d, device, gui, tongxu, stt)
            if result is False:
                break
            gui.log_queue.put(f"[{device}] Đang khởi động lại app Golike")
    gui.stop_device(device)  # Gọi stop_device khi thoát vòng lặp
# Xác định đường lưu PID (ưu tiên ổ D, fallback sang ổ C)
# if os.path.exists("D:/"):
#     PID_FILE = "D:/tool.pid"
# else:
#     PID_FILE = "C:/tool.pid"

# def check_and_kill_old_instance():
#     if os.path.exists(PID_FILE):
#         try:
#             with open(PID_FILE, "r") as f:
#                 old_pid = int(f.read().strip())
#             if psutil.pid_exists(old_pid):
#                 # Nếu tool cũ còn chạy → cảnh báo và thoát
#                 app = QApplication(sys.argv)
#                 QMessageBox.warning(None, "Cảnh báo", "Tool đã chạy trong 1 cửa sổ CMD khác!")
#                 sys.exit(0)
#         except Exception:
#             pass  # nếu lỗi đọc file thì bỏ qua

#     # Ghi PID mới
#     with open(PID_FILE, "w") as f:
#         f.write(str(os.getpid()))
def get_system_path(filename):
    """Xác định đường dẫn thư mục lưu file và tạo nếu chưa tồn tại."""
    base_path = "D:\\system" if os.path.exists("D:\\") else "C:\\system"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        # Ẩn thư mục trên Windows
        if os.name == "nt":  # Kiểm tra hệ điều hành là Windows
            os.system(f'attrib +h "{base_path}"')
    return os.path.join(base_path, filename)

def load_font_from_url(url, filename="Roboto.ttf"):
    """Tải file font từ URL và lưu vào base_path, ẩn file."""
    path = get_system_path(filename)
    if not os.path.exists(path):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Kiểm tra lỗi HTTP
            with open(path, "wb") as f:
                f.write(response.content)
            # Ẩn file trên Windows
            if os.name == "nt":
                os.system(f'attrib +h "{path}"')
            print()
        except Exception as e:
            print()
            return None
    return path

class LoadingScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Tải font Roboto từ Google Fonts (hoặc URL bạn cung cấp)
        font_url = "https://fonts.google.com/download?family=Roboto"  # Thay bằng URL file .ttf cụ thể nếu cần
        font_path = load_font_from_url(font_url, "Roboto.ttf")

        # Label hiển thị "Đang tải tool..." với font Roboto, màu hồng, không nền
        self.label = QLabel("ĐANG VÀO TOOL", self)
        self.label.setFont(QFont("Roboto", 30, QFont.Bold))  # Sử dụng font Roboto
        self.label.setStyleSheet("color: #fffff0; background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.adjustSize()  # Tự động điều chỉnh kích thước theo nội dung chữ
        self.setFixedSize(self.label.size())  # Kích thước cửa sổ bằng kích thước chữ

        # Định vị giữa màn hình
        screen = QApplication.desktop().screenGeometry()
        self.setGeometry(
            (screen.width() - self.label.width()) // 2,
            (screen.height() - self.label.height()) // 2,
            self.label.width(), self.label.height()
        )

        # Chuyển sang giao diện chính sau 2 giây
        QTimer.singleShot(2000, self.show_main_interface)

    def show_main_interface(self):
        self.close()

if __name__ == "__main__":
    # check_and_kill_old_instance()
    app = QApplication(sys.argv)
    loading_screen = LoadingScreen()
    loading_screen.show()
    if detect_debug_tools():
        QMessageBox.critical(None, "Debug Detected", "Debug tools detected. Application will exit. Please disable debugging tools.")
        raise SystemExit(1)
    debug_thread = threading.Thread(target=auto_kill_if_debug_detected, daemon=True)
    debug_thread.start()
    try:
        check_server()
        zalo_link = "https://zalo.me/g/axtnqv555"
        max_attempts = 3
        attempt = 0
        if os.path.exists('Z-Matrix_key_vip.txt'):
            with open('Z-Matrix_key_vip.txt', 'r') as file:
                key_vip = file.read().strip()
            hwid = get_device_id()
            success, key_name, expire_time, error_msg = check_key_vip(key_vip, hwid)
            if success:
                window = MainWindow(key_info={"type": "VIP", "name": key_name, "expire_time": expire_time}, zalo_link=zalo_link)
                window.show()
                app.exec_()
                raise SystemExit(0)
            else:
                QMessageBox.critical(None, "Key Error", error_msg)
                attempt += 1
        elif os.path.exists('Z-Matrix_key.txt'):
            with open('Z-Matrix_key.txt', 'r') as file:
                key_free = file.read().strip()
            success, key_name, expire_time, error_msg = check_key_free(key_free)
            if success:
                window = MainWindow(key_info={"type": "Free", "name": key_name, "expire_time": expire_time}, zalo_link=zalo_link)
                window.show()
                app.exec_()
                raise SystemExit(0)
            else:
                QMessageBox.critical(None, "Key Error", error_msg)
                attempt += 1
        while attempt < max_attempts:
            key_dialog = KeyInputDialog()
            if key_dialog.exec_():
                window = MainWindow(key_info=key_dialog.key_info, zalo_link=zalo_link)
                window.show()
                app.exec_()
                raise SystemExit(0)
            else:
                raise SystemExit(0)
        QMessageBox.critical(None, "Key Error", "Đã quá 3 lần nhập key sai. Vui lòng thử lại sau.")
        raise SystemExit(1)
    except SystemExit:
        raise
    except RuntimeError as e:
        raise SystemExit(1)