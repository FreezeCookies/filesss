import subprocess, os, threading, time, re, requests, base64, json, platform, random, string, webbrowser
from concurrent.futures import ThreadPoolExecutor
import psutil
import uiautomator2 as u2
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QTextEdit, QLabel,
                             QDialog, QLineEdit, QMessageBox, QSizePolicy, QComboBox, QSplitter, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPixmap, QIcon, QTextCursor
from PyQt5.QtWidgets import QHeaderView
import sys
from io import BytesIO
import uuid
import requests
from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent
import numpy as np
import cv2
import multiprocessing

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

def check_server():
    try:
        response = requests.get('https://zmatrixtool.x10.mx/Api/server_glfbv1.2.php', timeout=10)
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
        self.setMinimumSize(1000, 700)
        url = "https://zmatrixtool.x10.mx/key/avt.jpg"
        icon = load_icon_from_url(url)
        if icon:
            self.setWindowIcon(icon)
        self.devices = []
        self.device_names = {}
        self.selected_devices = []
        self.running = False
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.job_data = {}
        self.device_rows = {}
        self.device_start_times = {}  # Dictionary to store start times for each device
        self.total_xu_all = 0
        self.min_delay = 1.5  # Default open Facebook delay
        self.max_delay = 2.5
        self.min_reaction_delay = 0.5  # Default reaction delay
        self.max_reaction_delay = 1.0
        self.theme = "black_pink"  # Default theme
        self.setup_ui()
        self.apply_theme()
        self.log_signal.connect(self.log_message)
        self.update_table_signal.connect(self.add_job_to_table)

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
        self.job_btn = QPushButton("GOLIKE TIKTOK")
        self.job_btn.setObjectName("nav_btn")
        self.job_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        nav_layout.addWidget(self.job_btn)
        self.update_btn = QPushButton("Cập Nhật")
        self.update_btn.setObjectName("nav_btn")
        self.update_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(2))
        nav_layout.addWidget(self.update_btn)
        self.theme_btn = QPushButton("Đổi Theme")
        self.theme_btn.setObjectName("nav_btn")
        self.theme_btn.clicked.connect(self.toggle_theme)
        nav_layout.addWidget(self.theme_btn)
        nav_layout.addStretch()
        main_layout.addWidget(nav_widget)

        # Content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel (controls and info)
        left_panel = QWidget()
        left_panel.setObjectName("left_panel")
        left_layout = QVBoxLayout(left_panel)
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

        # Thêm tiêu đề trên đầu box
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

        # Layout ngang cho input và nút
        delay_layout = QHBoxLayout()
        delay_layout.setSpacing(10)

        min_delay_label = QLabel("Min Delay (s):")
        min_delay_label.setObjectName("info")
        self.min_delay_input = QLineEdit("2.0")
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

        # Thêm tiêu đề trên đầu box
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

        # Layout ngang cho input và nút
        reaction_delay_layout = QHBoxLayout()
        reaction_delay_layout.setSpacing(10)

        min_reaction_delay_label = QLabel("Min Delay (s):")
        min_reaction_delay_label.setObjectName("info")
        self.min_reaction_delay_input = QLineEdit("1.0")
        self.min_reaction_delay_input.setFixedWidth(60)
        self.min_reaction_delay_input.setPlaceholderText("Min delay")
        reaction_delay_layout.addWidget(min_reaction_delay_label)
        reaction_delay_layout.addWidget(self.min_reaction_delay_input)

        max_reaction_delay_label = QLabel("Max Delay (s):")
        max_reaction_delay_label.setObjectName("info")
        self.max_reaction_delay_input = QLineEdit("2.0")
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
        splitter.addWidget(left_panel)

        # Right panel (table and logs, prioritized)
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Content stack
        self.content_stack = QStackedWidget()

        # Job content
        job_widget = QWidget()
        job_widget.setObjectName("job_widget")
        job_layout = QVBoxLayout(job_widget)
        table_widget = QWidget()
        table_widget.setObjectName("card")
        table_layout = QVBoxLayout(table_widget)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Chọn", "Thiết Bị", "Done", "FB ID", "Loại Job", "Xu", "Tổng Xu", "Thời Gian Hoạt Động"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 80)
        self.table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.table)
        job_layout.addWidget(table_widget)

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
        job_layout.addWidget(log_widget)

        # Total Xu
        xu_widget = QWidget()
        xu_widget.setObjectName("card")
        xu_layout = QHBoxLayout(xu_widget)
        self.total_xu_label = QLabel("Tổng Xu: 0")
        self.total_xu_label.setObjectName("info")
        xu_layout.addWidget(self.total_xu_label)
        job_layout.addWidget(xu_widget)
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
            "<b>Phiên bản:</b> v1.2<br>"
            "<b>Ngày:</b> 21/08/2025<br><br>"
            "<b>Cập nhật:</b><br>"
            "• Tự động dừng thao tác của máy khi đủ 100 job.<br>"
            "• Thêm cấu hình delay mở Facebook [MIN/MAX].<br>"
            "• Thêm cấu hình delay thả cảm xúc [MIN/MAX].<br>"
            "• Chỉnh sửa tính năng thời gian hoạt động của các thiết bị.<br>"
            "• Hiển thị tổng xu của tất cả thiết bị.<br>"
            "• Fix lỗi chỉnh sửa kích thước bị out.<br>"
            "• Thêm các tông màu Hồng-Đen, Hồng-Trắng, Xanh-Trắng, Xanh-Đen.<br><br>"
            "<b>Thông tin cập nhật sau:</b><br>"
            "• Cập nhật thêm chức năng nuôi tài khoản Facebook.<br>"
            "• Cập nhật thêm chạy bao nhiêu job thì dừng cho mỗi thiết bị.<br>"
            "• Cập nhật thêm tool box phone Golike Tiktok.<br>"
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

        right_layout.addWidget(self.content_stack)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])

        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.update_device_list)
        self.device_timer.start(5000)

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
                    font-weight: bold;
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
            """
        elif self.theme == "pink_white":
            palette.setColor(QPalette.Window, QColor(255, 255, 255))  # #FFFFFF
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.Background, QColor(255, 255, 255))
            style_sheet = """
                QMainWindow, QWidget#main_widget {
                    background: #FFFFFF !important;
                }
                QWidget#left_panel, QWidget#right_panel, QWidget#job_widget, QWidget#update_widget {
                    background: #FFFFFF !important;
                }
                QWidget#nav {
                    background: #FFE4E1;
                    border-bottom: 1px solid #FFCCCB;
                    padding: 3px;
                }
                QPushButton#nav_btn {
                    background: #FFCCCB;
                    color: #FFFFFF;
                    padding: 6px;
                    font-size: 12px;
                    border-radius: 5px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton#nav_btn:hover {
                    background: #FF9999;
                }
                QWidget#card {
                    background: #FFE4E1;
                    border-radius: 6px;
                    border: 1px solid #FFCCCB;
                    padding: 8px;
                }
                QLabel#title {
                    font-size: 16px;
                    font-weight: 580;
                    color: #FF6666;
                }
                QLabel#info {
                    font-size: 13px;
                    color: #FF6666;
                    font-weight: 500;
                }
                QPushButton#action_btn {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFCCCB, stop:1 #FF9999);
                    color: #FFFFFF;
                    padding: 8px;
                    font-size: 13px;
                    border-radius: 6px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton#action_btn:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9999, stop:1 #FF6666);
                }
                QPushButton#action_btn:disabled {
                    background: #FFF5F5;
                    color: #FF9999;
                }
                QTableWidget {
                    background: #FFE4E1;
                    color: #FF6666;
                    border: 2px solid #FFCCCB;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background: #FFF5F5;
                    color: #FF6666;
                    padding: 5px;
                    font-size: 13px;
                    border: 1px solid #FFCCCB;
                    font-weight: bold;
                }
                QTableWidget::item:alternate {
                    background: #FFF5F5;
                }
                QTableWidget::item:selected {
                    background: #FFCCCB;
                    color: #FFFFFF;
                }
                QTextEdit {
                    background: #FFE4E1;
                    color: #FF6666;
                    border: 2px solid #FFCCCB;
                    border-radius: 6px;
                    font-size: 14px;
                    padding: 8px;
                }
                QLineEdit {
                    background-color: #FFE4E1;
                    color: #FF6666;
                    padding: 8px;
                    font-size: 13px;
                    border: 2px solid #FFCCCB;
                    border-radius: 6px;
                }
                QLineEdit:hover {
                    border: 2px solid #FF9999;
                    background-color: #FFF5F5;
                }
            """
        elif self.theme == "green_white":
            palette.setColor(QPalette.Window, QColor(255, 255, 255))  # #FFFFFF
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.Background, QColor(255, 255, 255))
            style_sheet = """
                QMainWindow, QWidget#main_widget {
                    background: #FFFFFF !important;
                }
                QWidget#left_panel, QWidget#right_panel, QWidget#job_widget, QWidget#update_widget {
                    background: #FFFFFF !important;
                }
                QWidget#nav {
                    background: #E0F2F1;
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
                    background: #E0F2F1;
                    border-radius: 6px;
                    border: 1px solid #4DB6AC;
                    padding: 8px;
                }
                QLabel#title {
                    font-size: 16px;
                    font-weight: 580;
                    color: #00897B;
                }
                QLabel#info {
                    font-size: 13px;
                    color: #00897B;
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
                    background: #F5F5F5;
                    color: #4DB6AC;
                }
                QTableWidget {
                    background: #E0F2F1;
                    color: #00897B;
                    border: 2px solid #4DB6AC;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background: #F5F5F5;
                    color: #00897B;
                    padding: 5px;
                    font-size: 13px;
                    border: 1px solid #4DB6AC;
                    font-weight: bold;
                }
                QTableWidget::item:alternate {
                    background: #F5F5F5;
                }
                QTableWidget::item:selected {
                    background: #4DB6AC;
                    color: #FFFFFF;
                }
                QTextEdit {
                    background: #E0F2F1;
                    color: #00897B;
                    border: 2px solid #4DB6AC;
                    border-radius: 6px;
                    font-size: 14px;
                    padding: 8px;
                }
                QLineEdit {
                    background-color: #E0F2F1;
                    color: #00897B;
                    padding: 8px;
                    font-size: 13px;
                    border: 2px solid #4DB6AC;
                    border-radius: 6px;
                }
                QLineEdit:hover {
                    border: 2px solid #26A69A;
                    background-color: #F5F5F5;
                }
            """
        else:  # green_black
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
                    font-weight: bold;
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
            """
        self.setPalette(palette)
        main_widget = self.findChild(QWidget, "main_widget")
        if main_widget:
            main_widget.setPalette(palette)
        self.setStyleSheet(style_sheet)

    def toggle_theme(self):
        themes = ["black_pink", "pink_white", "green_white", "green_black"]
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
        if self.running:
            # Update elapsed time for running devices
            for device in self.selected_devices:
                if device in self.device_rows:
                    row = self.device_rows[device]
                    start_time = self.device_start_times.get(device)
                    self.table.setItem(row, 7, QTableWidgetItem(get_elapsed_time(start_time)))
            return
        current_devices = get_devices()
        if current_devices != self.devices:
            self.devices = current_devices
            self.device_names = {}
            self.table.setRowCount(0)
            for device in self.devices:
                try:
                    name = subprocess.run(f"adb -s {device} shell getprop ro.product.model",
                                        shell=True, capture_output=True, text=True).stdout.strip()
                    self.device_names[device] = name if name else "Unknown"
                except:
                    self.device_names[device] = "Unknown"
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                checkbox = QCheckBox()
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                self.table.setCellWidget(row_count, 0, checkbox)
                self.table.setItem(row_count, 1, QTableWidgetItem(f"{self.device_names.get(device, 'Unknown')} ({device})"))
                self.table.setItem(row_count, 7, QTableWidgetItem("N/A"))
                self.device_rows[device] = row_count

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
        self.selected_devices = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                device_info = self.table.item(row, 1).text()
                device_id = device_info.split('(')[-1].strip(')')
                self.selected_devices.append(device_id)
                self.device_start_times[device_id] = datetime.now()  # Record start time
        if not self.selected_devices:
            self.log_text.append("Vui lòng chọn ít nhất một thiết bị!")
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
        self.running = True
        self.stop_event.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.tick_all_btn.setEnabled(False)
        self.log_text.append(f"Bắt đầu làm việc với các thiết bị: {', '.join(self.selected_devices)}")
        self.job_data = {device: {"stt": 0, "tongxu": 0} for device in self.selected_devices}
        for device in self.selected_devices:
            subprocess.run(f"adb -s {device} shell settings put system accelerometer_rotation 0", shell=True)
            subprocess.run(f"adb -s {device} shell settings put system user_rotation 0", shell=True)
            if device not in self.device_rows:
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                self.device_rows[device] = row_count
                device_name = self.device_names.get(device, 'Unknown')
                checkbox = QCheckBox()
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Checked)
                self.table.setCellWidget(row_count, 0, checkbox)
                self.table.setItem(row_count, 1, QTableWidgetItem(f"{device_name} ({device})"))
                self.table.setItem(row_count, 7, QTableWidgetItem(get_elapsed_time(self.device_start_times.get(device))))
            self.executor.submit(main, device, self, self.stop_event, self.min_delay, self.max_delay, self.min_reaction_delay, self.max_reaction_delay)

    def stop_jobs(self):
        self.running = False
        self.stop_event.set()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.tick_all_btn.setEnabled(True)
        self.log_text.append("Đã dừng tất cả nhiệm vụ.")
        # Reset start times when stopping
        for device in self.selected_devices:
            if device in self.device_rows:
                row = self.device_rows[device]
                self.table.setItem(row, 7, QTableWidgetItem("N/A"))
        self.device_start_times.clear()

    def add_job_to_table(self, device, stt, fb_id, fb_job, xu_job, tongxu, timestamp):
        row = self.device_rows.get(device, 0)
        self.table.setItem(row, 2, QTableWidgetItem(str(stt)))
        self.table.setItem(row, 3, QTableWidgetItem(fb_id))
        self.table.setItem(row, 4, QTableWidgetItem(fb_job))
        self.table.setItem(row, 5, QTableWidgetItem(str(xu_job)))
        self.table.setItem(row, 6, QTableWidgetItem(str(tongxu)))
        self.table.setItem(row, 7, QTableWidgetItem(timestamp))
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

# Backend functions
def get_devices():
    return [line.split()[0] for line in subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.strip().split("\n")[1:] if line.strip()]

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
        fb_id = "none"
    return job_id, fb_id

def bao_loi(d):
    if d(text="OK").exists:
        d(text="OK").click()
    d(text="Báo lỗi").click()
    d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.3)
    time.sleep(1)
    d(text="Gửi báo cáo").click()
    time.sleep(2)
    d(text="OK").click()
    d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
    d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)

def reset_golike(d, device):
    try:
        os.system(f"adb -s {device} shell am start -n com.golike/.MainActivity -a android.intent.action.VIEW -d 'golike://reward/facebook' >nul 2>&1")
        time.sleep(10)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(2)
        if not d(text="Kiếm Thưởng").exists(timeout=10):
            return reset_golike(d, device)

        d(text="Kiếm Thưởng").click()
        time.sleep(0.5)
        if d(text="Kiếm Thưởng").exists(timeout=5):
            d(text="Kiếm Thưởng").click()
        time.sleep(1)

        if d(text="Facebook").exists(timeout=5):
            d(text="Facebook").click()
        time.sleep(2)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(1)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(2)

        # thông báo giới hạn job → dừng
        if d(resourceId="swal2-content").exists(timeout=3):
            print(f"[{device}] Xuất hiện thông báo giới hạn job, dừng luồng.")
            return False

        return True
    except:
        return reset_golike(d, device)

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
    while gui.running and not stop_event.is_set():
        if stt >= 100:
            gui.log_signal.emit(f"[{device}] Đã đạt 100 công việc, dừng thiết bị này.")
            gui.update_table_signal.emit(device, stt, "N/A", "Stopped", 0, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
            break
        try:
            d.swipe(0.5, 0.7, 0.5, 0.6, duration=0.1)
            d.swipe(0.5, 0.6, 0.5, 0.7, duration=0.1)
            d(textContains="Còn lại").click()
            time.sleep(0.5)
            d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
            d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)
            time.sleep(1.1)
            golike_job, fb_job, xu_job = check_type(d)
            if golike_job == "none":
                time.sleep(1)
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
                d(text="Hoàn thành").click()
                time.sleep(1)
                d(text="OK").click()
                d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
                d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)
                time.sleep(1)
                if d(text="Hoàn thành").exists:
                    bao_loi(d)
                    gui.log_signal.emit(f"[{device}] Đã báo lỗi cho công việc")
                else:
                    tongxu += xu_job
                    stt += 1
                    gui.update_table_signal.emit(device, stt, "NONE", fb_job, xu_job, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
                continue
            job_id, fb_id = check_job(d)
            if fb_id == "none":
                bao_loi(d)
                gui.log_signal.emit(f"[{device}] Đã báo lỗi cho công việc")
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
                gui.log_signal.emit(f"[{device}] Đã báo lỗi do bài viết không hiển thị")
                continue
            time.sleep(1)
            for i in range(5):
                if d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").exists:
                    if fb_job == "Bình luận":
                        d(description=f"{fb_job}").click()
                        time.sleep(1)
                        d.clipboard
                        os.system(f"adb -s {device} shell input keyevent 279")
                        time.sleep(1)
                        d(description="Gửi").click()
                    else:
                        time.sleep(0.5)
                        d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").long_click()
                        if d(description=f"{fb_job}").exists:
                            d(description=f"{fb_job}").click()
                        else:
                            try:
                                d(text="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").click()
                            except:
                                break
                    time.sleep(random.uniform(min_reaction_delay, max_reaction_delay))
                    break
                else:
                    d.swipe(0.4, 0.8, 0.4, 0.5, duration=0.1)
                    time.sleep(1)
                    continue
            subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity -f 0x20000000", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            d(text="Hoàn thành").click()
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
            if d(text="Hoàn thành").exists:
                bao_loi(d)
                gui.log_signal.emit(f"[{device}] Đã báo lỗi cho công việc")
            else:
                tongxu += xu_job
                stt += 1
                gui.update_table_signal.emit(device, stt, fb_id, fb_job, xu_job, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
        except Exception as e:
            if stop_event.is_set():
                return
            gui.log_signal.emit(f"[{device}] Exception: {str(e)}")
            result = reset_golike(d, device)
            if result is False:  # gặp giới hạn job
                gui.log_signal.emit(f"[{device}] Dừng luồng do vượt quá 100 job.")
                break
            gui.log_signal.emit(f"[{device}] Đang khởi động lại app Golike")

# Thêm backend cho TikTok
aut_file = "authorization.txt"

def save_authorization(aut):
    with open(aut_file, "w", encoding="utf-8") as f:
        f.write(aut)
    return aut

def load_authorization():
    if os.path.exists(aut_file):
        with open(aut_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def get_headers_tiktok(aut):
    headers = {
        'authorization': aut,
        'origin': 'https://app.golike.net',
        't': 'VFZSak1FOUVSWGhPVkUxNVRWRTlQUT09',
        "user-agent": UserAgent().random,
    }
    return headers

def dat_nick(user_cau_hinh, aut):
    try:
        session = curl_requests.Session()
        dat_nick = session.get('https://gateway.golike.net/api/tiktok-account', headers=get_headers_tiktok(aut), impersonate="chrome101").json()
        for user in dat_nick['data']:
            if user['unique_username'] == user_cau_hinh:
                return user['id']
        return None
    except Exception as e:
        print(f"Lỗi dat_nick: {e}")
        return None

def die_job(account_id, account_id_die, ads_id, object_id, job_type, aut):
    json_data = {
        'description': 'Tôi không muốn làm Job này',
        'users_advertising_id': account_id,
        'type': 'ads',
        'provider': 'tiktok',
        'fb_id': account_id_die,
        'error_type': 0,
    }
    session = curl_requests.Session()
    die_job = session.post(
        "https://gateway.golike.net/api/report/send",
        headers=get_headers_tiktok(aut),
        impersonate="chrome101",
        json=json_data
    ).json()
    die_json_data = {
        'ads_id': ads_id,
        'object_id': object_id,
        'account_id': account_id_die,
        'type': job_type,
    }
    die_job_post = session.post(
        'https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs',
        headers=get_headers_tiktok(aut),
        impersonate="chrome101",
        json=die_json_data
    ).json()

def tiktok_main(device, gui, stop_event, min_delay_job, max_delay_job, min_lam_job, max_lam_job, bo_job_be, aut):
    done = fail = tong_xu = 0
    try:
        while True:
            try:
                d = u2.connect(device)
                gui.log_signal.emit(f"[{device}] Đã kết nối thành công tới TikTok")
                break
            except Exception as e:
                gui.log_signal.emit(f"[{device}] Kết nối thất bại, thử lại: {str(e)}")
                time.sleep(2)
                if stop_event.is_set():
                    return

        # Mở profile và lấy user_cau_hinh
        os.system(f"adb -s {device} shell monkey -p com.ss.android.ugc.trill -c android.intent.category.LAUNCHER 1 >nul 2>&1")
        time.sleep(5)
        while True:
            subprocess.run([
                "adb", "-s", device, "shell", "am", "start",
                "-n", "com.ss.android.ugc.trill/com.ss.android.ugc.aweme.deeplink.DeepLinkActivityV2",
                "-a", "android.intent.action.VIEW",
                "-d", "snssdk1233://user/profile"
            ], check=True)
            time.sleep(5)
            if d(textContains="@").exists:
                d(textContains="@").click()
                user_cau_hinh = d.clipboard
                gui.log_signal.emit(f"[{device}] Đã lấy được tên user TikTok: {user_cau_hinh}")
                os.system(f"adb -s {device} shell input keyevent 4")
                break
            else:
                gui.log_signal.emit(f"[{device}] Lấy user TikTok thất bại, thử lại")
                time.sleep(2)
                continue

        # Lấy id acc
        account_id = dat_nick(user_cau_hinh, aut)
        if not account_id:
            gui.log_signal.emit(f"[{device}] Không lấy được account_id cho user {user_cau_hinh}")
            return

        # Đặt nick get job
        session = curl_requests.Session()
        while gui.running and not stop_event.is_set():
            try:
                job = []
                try:
                    get_job = session.get(
                        f'https://gateway.golike.net/api/advertising/publishers/tiktok/jobs?account_id={account_id}&data=null',
                        headers=get_headers_tiktok(aut),
                        impersonate="chrome101",
                        timeout=10
                    ).json()
                except Exception as e:
                    gui.log_signal.emit(f"[{device}] Lỗi lấy job TikTok: {str(e)}")
                    time.sleep(30)
                    continue

                if not get_job.get('data'):
                    gui.log_signal.emit(f"[{device}] Đợi job TikTok...")
                    time.sleep(15)
                    continue

                if 'lock' not in get_job or 'ads_id' not in get_job.get('lock', {}) or get_job.get('code') == 429:
                    gui.log_signal.emit(f"[{device}] Đợi luồng TikTok 10s")
                    time.sleep(10)
                    continue

                if get_job['data']:
                    job.append({
                        'ads_id': get_job['lock']['ads_id'],
                        'object_id': get_job['lock']['object_id'],
                        'account_id': get_job['lock']['account_id'],
                        'type': get_job['lock']['type'],
                    })

                    first_job = job[0]
                    ads_id = first_job['ads_id']
                    object_id = first_job['object_id']
                    account_id_die = first_job['account_id']
                    job_type = first_job['type']
                    type_job = get_job['data']['type'][:4] + "..." if len(get_job['data']['type']) > 6 else get_job['data']['type']
                    xu_job = get_job['data']['price_after_cost']
                    link_job = get_job['data']['link']
                    id_job = get_job['data']['id']

                    gui.log_signal.emit(f"[{device}] Đã get được job TikTok {type_job} với {xu_job} xu")
                    gui.update_table_signal.emit(device, done + 1, id_job, type_job, xu_job, tong_xu, get_elapsed_time(gui.device_start_times.get(device)))

                    if xu_job <= bo_job_be and type_job == "follow":
                        gui.log_signal.emit(f"[{device}] Bỏ qua job TikTok {type_job} do xu thấp ({xu_job} <= {bo_job_be})")
                        die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                        continue

                    with open("link_job.txt", "w", encoding="utf-8") as f:
                        f.write(link_job)

                    cmd = [
                        "adb", "-s", device, "shell", "am", "start",
                        "-a", "android.intent.action.VIEW",
                        "-d", link_job
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    if job_type == "follow":
                        ten = link_job.split("@")[-1]
                        gui.log_signal.emit(f"[{device}] Follow TikTok {ten}")
                        time.sleep(random.uniform(min_delay_job, max_delay_job))

                        if d(text="Đây là tài khoản riêng tư").exists:
                            gui.log_signal.emit(f"[{device}] Bỏ qua tài khoản riêng tư")
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            continue
                        elif d(text="Tài khoản đã bị cấm").exists:
                            gui.log_signal.emit(f"[{device}] Bỏ qua tài khoản cấm")
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            continue

                        if d(text="Follow").exists:
                            d(text="Follow").click()
                            time.sleep(1)
                            subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(2)
                            if d(text="Không cho phép").exists:
                                d(text="Không cho phép").click()
                            for _ in range(8):
                                if d(text="Trang chủ").exists:
                                    break
                                else:
                                    os.system(f"adb -s {device} shell input keyevent 4")
                                    time.sleep(1)
                        else:
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(0.1)
                            continue

                    elif job_type == "like":
                        time.sleep(random.uniform(min_delay_job, max_delay_job))
                        like_btn = d(description="Thích")
                        if like_btn.exists and not like_btn.info.get("selected", False):
                            like_btn.click()

                    elif job_type == "comment":
                        comment_id = get_job['lock']['comment_id']
                        message_comment = get_job['lock']['message']
                        gui.log_signal.emit(f"[{device}] Bình luận TikTok: {message_comment[:15]}... | ID job: {comment_id}")
                        time.sleep(random.uniform(min_delay_job, max_delay_job))

                        moc = d(description="Thích")
                        if not moc.exists:
                            gui.log_signal.emit(f"[{device}] Job TikTok lỗi")
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            continue

                        button = d(text="Đề xuất").bounds()
                        y = button[3] + 100
                        w, h = d.window_size()
                        x = w // 2

                        bounds = moc.info['bounds']
                        x_moc = (bounds['left'] + bounds['right']) // 2
                        y_moc = (bounds['top'] + bounds['bottom']) // 2
                        height = bounds['bottom'] - bounds['top']
                        y_click = y_moc + height * 2
                        x_click = x_moc

                        d.click(x_click, y_click)
                        time.sleep(10)

                        button = d(text="Thêm bình luận...")
                        if button.exists:
                            button.click()
                            time.sleep(1)
                            button.send_keys(message_comment)
                            time.sleep(2)
                        else:
                            gui.log_signal.emit(f"[{device}] Job TikTok lỗi")
                            os.system(f"adb -s {device} shell input keyevent 4")
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            continue

                        d.click(x, y)
                        time.sleep(2)

                        img = None
                        for _ in range(5):
                            os.system(f"adb -s {device} shell screencap /sdcard/screen.png >nul 2>&1")
                            os.system(f"adb -s {device} pull /sdcard/screen.png >nul 2>&1")
                            if not os.path.exists("screen.png"):
                                continue
                            else:
                                img = cv2.imread('screen.png')
                                if img is None:
                                    time.sleep(1)
                                    continue
                                break
                        else:
                            d.click(x, y)

                        if img is not None:
                            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                            lower_red1 = np.array([0, 100, 100])
                            upper_red1 = np.array([10, 255, 255])
                            lower_red2 = np.array([160, 100, 100])
                            upper_red2 = np.array([179, 255, 255])
                            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                            mask_red = cv2.bitwise_or(mask1, mask2)
                            contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                            for cnt in contours:
                                area = cv2.contourArea(cnt)
                                if area > 1000:
                                    x, y, w, h = cv2.boundingRect(cnt)
                                    roi = img[y:y+h, x:x+w]
                                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                                    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                                    white_pixels = cv2.countNonZero(thresh)
                                    if white_pixels > (w*h)*0.1:
                                        cx = x + w//2
                                        cy = y + h//2
                                        os.system(f"adb -s {device} shell input tap {cx} {cy}")
                                        time.sleep(2)
                                        if os.path.exists('screen.png'):
                                            os.remove('screen.png')
                                        time.sleep(2)
                                        os.system(f"adb -s {device} shell input keyevent 4")

                    else:
                        gui.log_signal.emit(f"[{device}] Bỏ qua job TikTok lỗi")
                        die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                        continue

                    gui.log_signal.emit(f"[{device}] Đã {type_job} TikTok thành công")
                    time.sleep(1)
                    d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.1)
                    time.sleep(random.uniform(min_lam_job, max_lam_job))

                    gui.log_signal.emit(f"[{device}] Bắt đầu done job TikTok lần 1")
                    done_job_data = {
                        'ads_id': id_job,
                        'account_id': account_id,
                        'async': True,
                        'data': None,
                    }
                    if type_job == "comment":
                        done_job_data.update({
                            'comment_id': comment_id,
                            'message': message_comment,
                        })

                    done_job = session.post(
                        "https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs",
                        headers=get_headers_tiktok(aut),
                        impersonate="chrome101",
                        json=done_job_data
                    ).json()

                    if done_job.get('message') == "Tài khoản chưa công khai danh sách like vui lòng mở danh sách đã like":
                        gui.log_signal.emit(f"[{device}] Đang bật công khai danh sách like")
                        time.sleep(2)
                        d(text="Hồ sơ").click()
                        time.sleep(2)
                        d(description="Menu hồ sơ").click()
                        time.sleep(2)
                        d(text="Cài đặt và quyền riêng tư").click()
                        time.sleep(2)
                        d(text="Quyền riêng tư").click()
                        time.sleep(2)
                        d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.1)
                        time.sleep(2)
                        d(text="Video đã thích").click()
                        time.sleep(2)
                        d(text="Mọi người").click()
                        subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(0.5)
                        subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(0.5)
                        subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        gui.log_signal.emit(f"[{device}] Đã bật công khai thành công, lấy lại job")
                        continue

                    if not done_job.get('success'):
                        gui.log_signal.emit(f"[{device}] Đang done job TikTok lần 2")
                        done_job_1 = session.post(
                            "https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs",
                            headers=get_headers_tiktok(aut),
                            impersonate="chrome101",
                            json=done_job_data
                        ).json()
                        if not done_job_1.get('success'):
                            die_job(account_id, account_id_die, ads_id, object_id, job_type, aut)
                            fail += 1
                            gui.log_signal.emit(f"[{device}] Job TikTok Fail")
                            time.sleep(1)
                        else:
                            done += 1
                            tong_xu += xu_job
                            gui.log_signal.emit(f"[{device}] Job TikTok Done")
                            gui.update_table_signal.emit(device, done, id_job, type_job, xu_job, tong_xu, get_elapsed_time(gui.device_start_times.get(device)))
                            time.sleep(1)
                    else:
                        done += 1
                        tong_xu += xu_job
                        gui.log_signal.emit(f"[{device}] Job TikTok Done")
                        gui.update_table_signal.emit(device, done, id_job, type_job, xu_job, tong_xu, get_elapsed_time(gui.device_start_times.get(device)))
                        time.sleep(1)
                else:
                    gui.log_signal.emit(f"[{device}] Đang đi lấy job TikTok")
                    time.sleep(10)
                    continue
            except Exception as e:
                gui.log_signal.emit(f"[{device}] Lỗi TikTok: {str(e)}")
                time.sleep(5)
                continue
    except Exception as e:
        gui.log_signal.emit(f"[{device}] Lỗi TikTok nghiêm trọng: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
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