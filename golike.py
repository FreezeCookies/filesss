import subprocess, os, threading, time, re, requests, base64, json, platform, random, string, webbrowser
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import psutil
import cv2, numpy as np
import uiautomator2 as u2
from urllib.parse import quote_plus
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
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QThread, pyqtSlot
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
import os, platform, subprocess, hashlib, base64, json, random, string

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


# ========== PHẦN MỚI: TẠO DEVICE ID CỐ ĐỊNH DÍNH PHẦN CỨNG ==========
def _run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def _collect_windows_ids():
    ids = []
    for cmd, key in [
        ('wmic baseboard get serialnumber', 'SerialNumber'),
        ('wmic csproduct get UUID', 'UUID'),
        ('wmic bios get serialnumber', 'SerialNumber'),
        ('wmic diskdrive get serialnumber', 'SerialNumber'),
        ('wmic cpu get ProcessorId', 'ProcessorId'),
    ]:
        out = _run_cmd(cmd)
        for line in out.splitlines():
            line = line.strip()
            if line and key.lower() not in line.lower():
                ids.append(line)
                break
    ids = [x for x in ids if x and x.lower() not in ("to be filled by o.e.m.", "none", "unknown")]
    return ids

def _collect_linux_ids():
    ids = []
    paths = [
        "/sys/class/dmi/id/board_serial",
        "/sys/class/dmi/id/product_uuid",
        "/sys/class/dmi/id/product_serial",
        "/etc/machine-id"
    ]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    v = f.read().strip()
                    if v:
                        ids.append(v)
        except Exception:
            pass
    try:
        out = subprocess.check_output(["lsblk", "-o", "SERIAL", "-dn"], text=True, stderr=subprocess.DEVNULL)
        for ln in out.splitlines():
            ln = ln.strip()
            if ln:
                ids.append(ln)
    except Exception:
        pass
    return [x for x in ids if x and x.lower() not in ("none", "unknown")]

def _generate_fixed_hardware_id():
    system = platform.system()
    ids = _collect_windows_ids() if system == "Windows" else _collect_linux_ids()

    if not ids:
        ids = [platform.node()]  # fallback: hostname

    combined = "||".join(sorted(set(ids)))
    sha = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    num = int(sha, 16) % (10**8)
    return f"Z-Matrix_{num:08d}"


# ========== GHÉP VÀO HÀM CỦA M ==========
def get_device_id():
    # Bỏ toàn bộ phần lưu file, chỉ trả hardware ID
    device_id = _generate_fixed_hardware_id()
    encoded_id = encode_device_id(device_id)
    return decode_device_id(encoded_id)  # vẫn decode lại cho thống nhất flow
# SECRET_KEY = ".zmatrix_keyencode"

# def xor_encrypt_decrypt(data: str, key: str) -> str:
#     return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

# def encode_device_id(device_id: str) -> str:
#     encrypted = xor_encrypt_decrypt(device_id, SECRET_KEY)
#     return base64.b64encode(encrypted.encode()).decode()

# def decode_device_id(encoded: str) -> str:
#     try:
#         decoded_bytes = base64.b64decode(encoded)
#         decrypted = xor_encrypt_decrypt(decoded_bytes.decode(), SECRET_KEY)
#         return decrypted
#     except:
#         return "INVALID_ID"

# def get_device_id():
#     is_android = os.path.exists('/storage/emulated/0')
#     is_windows = platform.system() == 'Windows'
#     if is_android:
#         base_folder = '/storage/emulated/0/Android/.system/_FOLDER IMPORTANT_'
#         try:
#             os.makedirs(base_folder, exist_ok=True)
#         except PermissionError:
#             QMessageBox.critical(None, "Access Error", "No permission to access folder on Android. Please grant permissions or change folder.")
#             raise RuntimeError("No permission to access folder on Android")
#     elif is_windows:
#         if os.path.exists('D:\\'):
#             base_folder = 'D:\\.system\\_FOLDER IMPORTANT_'
#         else:
#             base_folder = 'C:\\.system\\_FOLDER IMPORTANT_'
#     else:
#         base_folder = '_FOLDER IMPORTANT_'
#     os.makedirs(base_folder, exist_ok=True)
#     config_path = os.path.join(base_folder, 'error_log.zip')
#     if os.path.exists(config_path):
#         with open(config_path, 'r') as f:
#             config = json.load(f)
#         filename = config.get('file')
#         if not filename:
#             filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.zip'
#             config['file'] = filename
#             with open(config_path, 'w') as f:
#                 json.dump(config, f)
#     else:
#         filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.zip'
#         config = {'file': filename}
#         with open(config_path, 'w') as f:
#             json.dump(config, f)
#     device_id_file = os.path.join(base_folder, filename)
#     if not os.path.exists(device_id_file):
#         big_number = str(random.randint(10**19, 10**20 - 1))
#         random_id = f"Z-Matrix_{big_number[:8]}"
#         encoded_id = encode_device_id(random_id)
#         with open(device_id_file, 'w') as f:
#             f.write(encoded_id)
#         if is_windows:
#             os.system(f'attrib +h "{base_folder}"')
#             os.system(f'attrib +h "{device_id_file}"')
#         return random_id
#     else:
#         with open(device_id_file, 'r') as f:
#             encoded_id = f.read().strip()
#         return decode_device_id(encoded_id)

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
        response = requests.get('https://zmatrixtool.x10.mx/Api/server/face.php', timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'status' in data and data['status'] == 'live':
            return True
        else:
            zalo = "https://zalo.me/g/axtnqv555"
            QMessageBox.critical(None, "Server Status", f"Đã có tool mới vui lòng cập nhật\nBox Zalo: {zalo}\nVui lòng tham gia group để nhận thông báo sớm nhất!")
            raise SystemExit("Server is under maintenance")
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(None, "Server Error", f"Connection error!\nPlease check your network.")
        raise SystemExit(f"Server connection error")
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
        return False, None, None, f"Connection error!"
    except ValueError:
        if os.path.exists('Z-Matrix_key_vip.txt'):
            os.remove('Z-Matrix_key_vip.txt')
        return False, None, None, "Invalid server response."

# def check_key_free(key):
#     try:
#         response = requests.get(f'https://zmatrixtool.x10.mx/Api/Check_key.php?key={key}', timeout=5)
#         response.raise_for_status()
#         data = response.json()['data']
#         if data.get('status') == "success" and data.get('message') == "Key ĐÚNG":
#             with open('Z-Matrix_key.txt', 'w') as file:
#                 file.write(key)
#             if data.get('event'):
#                 expiry = data.get('expiry', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
#             else:
#                 expiry = datetime.now().replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S')
#             return True, "Free", expiry, None
#         else:
#             if os.path.exists('Z-Matrix_key.txt'):
#                 os.remove('Z-Matrix_key.txt')
#             return False, None, None, data.get('message', 'Key free không hợp lệ hoặc đã hết hạn.')
#     except requests.exceptions.RequestException as e:
#         if os.path.exists('Z-Matrix_key.txt'):
#             os.remove('Z-Matrix_key.txt')
#         return False, None, None, f"Connection error!"
#     except ValueError:
#         if os.path.exists('Z-Matrix_key.txt'):
#             os.remove('Z-Matrix_key.txt')
#         return False, None, None, "Invalid server response."

def get_elapsed_time(start_time):
    if start_time is None:
        return "00:00:00"
    elapsed = datetime.now() - start_time
    hours = elapsed.seconds // 3600
    minutes = (elapsed.seconds % 3600) // 60
    seconds = elapsed.seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
# Thread chuyên dụng xử lý log
class LogProcessor(QThread):
    log_ready = pyqtSignal(str)
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.running = True
        
    def run(self):
        while self.running:
            try:
                message = self.log_queue.get(timeout=0.1)
                self.log_ready.emit(message)
                self.log_queue.task_done()
            except:
                continue
                
    def stop(self):
        self.running = False
        self.quit()
        self.wait(1000)
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
        self.key_type.addItems(["Vip Key"])
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
        if key_type == "Vip Key":
        #     success, key_name, expire_time, error_msg = check_key_free(key)
        #     self.submit_btn.setEnabled(True)
        #     self.cancel_btn.setEnabled(True)
        #     self.get_key_btn.setEnabled(True)
        #     if success:
        #         self.key_info = {"type": "Free", "name": key_name, "expire_time": expire_time}
        #         QMessageBox.information(self, "Success", "Key free đúng! Đang kết nối đến Server...")
        #         self.accept()
        #     else:
        #         QMessageBox.critical(self, "Key Error", error_msg)
        # else:
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
# Updated Product Intro Dialog
class ProductIntroDialog(QDialog):
    def __init__(self, key_info=None):
        super().__init__()
        self.key_info = key_info or {"type": "Unknown", "name": "Unknown", "expire_time": "Unknown"}
        self.setWindowTitle("Giới thiệu Z-Matrix Tool")
        self.setMinimumSize(500, 600)
        url = "https://zmatrixtool.x10.mx/key/avt.jpg"
        icon = load_icon_from_url(url)
        if icon:
            self.setWindowIcon(icon)
        self.theme = "black_pink"  
        self.apply_theme()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Logo
        try:
            response = requests.get('https://zmatrixtool.x10.mx/key/avt.jpg', timeout=5)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.getvalue())
            pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        except requests.exceptions.RequestException as e:
            logo_label = QLabel("Z-MATRIX TOOL")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4DB6AC;")
            layout.addWidget(logo_label)

        # Tiêu đề
        title_label = QLabel("Chào mừng đến với Z-Matrix Tool - Golike Facebook!")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Thông tin key
        key_info_text = f"""
        <b>Loại Key:</b> {self.key_info['type']}<br>
        <b>Tên:</b> {self.key_info['name']}<br>
        <b>Hạn sử dụng:</b> {self.key_info['expire_time']}
        """
        key_label = QLabel(key_info_text)
        key_label.setObjectName("info")
        key_label.setWordWrap(True)
        key_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(key_label)

        # Mô tả sản phẩm
        desc_text = """
        <b>Tính năng chính:</b><br>
        • Tự động hóa job Golike Facebook<br>
        • Hỗ trợ nhiều thiết bị Android qua ADB.<br>
        • Cấu hình delay linh hoạt cho mở Facebook và thả cảm xúc.<br>
        • Bỏ qua job Theo Dõi/Like Page tùy chọn.<br>
        • Đổi tên thiết bị dễ dàng để theo dõi.<br>
        • Shop Key tích hợp để mua key VIP.<br><br>
        <b>Phiên bản:</b> v2.0 (Cập nhật 11/09/2025)<br>
        <b>Nhà phát triển:</b> Z-Matrix Team<br>
        <b>Liên hệ:</b> Zalo Group - https://zalo.me/g/axtnqv555
        """
        desc_label = QLabel(desc_text)
        desc_label.setObjectName("info")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(desc_label)

        # Nút đóng
        button_layout = QHBoxLayout()
        enter_btn = QPushButton("Vào Tool")
        enter_btn.setObjectName("action_btn")
        enter_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(enter_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_theme(self):
        if self.theme == "green_black":
            style_sheet = """
                QDialog {
                    background: #12201C;
                    border-radius: 15px;
                }
                QLabel#title {
                    font-size: 20px;
                    color: #4DB6AC;
                    font-weight: bold;
                    padding: 10px;
                }
                QLabel#info {
                    font-size: 14px;
                    color: #80CBC4;
                    font-weight: 500;
                    padding: 10px;
                    border: 1px solid #4DB6AC;
                    border-radius: 8px;
                    background: #1E2F29;
                }
                QPushButton#action_btn {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4DB6AC, stop:1 #26A69A);
                    color: #FFFFFF;
                    padding: 12px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton#action_btn:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #26A69A, stop:1 #00897B);
                }
            """
        else:  # black_pink
            style_sheet = """
                QDialog {
                    background: #1C2526;
                    border-radius: 15px;
                }
                QLabel#title {
                    font-size: 20px;
                    color: #FF9999;
                    font-weight: bold;
                    padding: 10px;
                }
                QLabel#info {
                    font-size: 14px;
                    color: #FFCCCB;
                    font-weight: 500;
                    padding: 10px;
                    border: 1px solid #FF9999;
                    border-radius: 8px;
                    background: #2E2E2E;
                }
                QPushButton#action_btn {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9999, stop:1 #FF6666);
                    color: #FFFFFF;
                    padding: 12px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton#action_btn:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6666, stop:1 #FF3333);
                }
            """
        self.setStyleSheet(style_sheet)
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
        self.device_status = {}  
        self.device_threads = {}  
        self.button_timer = QTimer()
        self.button_timer.timeout.connect(self.update_button_states)
        self.button_timer.start(1000)
        self.device_stop_events = {}  
        self.selected_for_stop = []
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
        self.theme = "black_pink"
        self.log_queue = Queue()
        self.log_processor = LogProcessor(self.log_queue)
        self.log_processor.log_ready.connect(self.log_message)
        self.log_processor.start()
        self.pending_table_updates = {}
        self.table_update_timer = QTimer()
        self.table_update_timer.timeout.connect(self.process_pending_table_updates)
        self.table_update_timer.start(100)  
        self.last_device_update = 0
        self.last_button_update = 0
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
        self.stop_btn.setEnabled(False)  # Ban đầu disable
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
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên Ghi Chú", "Thiết Bị", "Done", "FB ID", "Loại Job", "Xu", "Tổng Xu", "Thời Gian Hoạt Động"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 60)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 80)
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
        "<b>Tính năng chính:</b><br>"
        "• Tự động hóa job Golike Facebook<br>"
        "• Hỗ trợ nhiều thiết bị Android qua ADB.<br>"
        "• Cấu hình delay linh hoạt cho mở Facebook và thả cảm xúc.<br>"
        "• Bỏ qua job Theo Dõi/Like Page tùy chọn.<br>"
        "• Đổi tên thiết bị dễ dàng để theo dõi.<br>"
        "• Shop Key tích hợp để mua key VIP.<br><br>"
        "<b>Phiên bản:</b> v2.0 (Cập nhật 11/09/2025)<br>"
        "<b>Nhà phát triển:</b> Z-Matrix Team<br>"
        "<b>Liên hệ:</b> Zalo Group - https://zalo.me/g/axtnqv555"
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
        self.rename_table.setHorizontalHeaderLabels(["STT", "Tên Thiết Bị", "Trạng Thái", "Sửa Tên Ghi Chú", "Kiểm Tra Kết Nối"])
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
            check_btn = QPushButton("Check thao tác")
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
    
    def initialize_device_status(self):
        """Khởi tạo trạng thái cho tất cả thiết bị"""
        for device in self.devices:
            if device not in self.device_status:
                self.device_status[device] = "stopped"
            if device not in self.device_stop_events:
                self.device_stop_events[device] = threading.Event()

    def update_device_list(self):
        if self.running:
            current_time = time.time()
            if current_time - self.last_device_update < 3:
                return
            self.last_device_update = current_time
            
            for device, status in self.device_status.items():
                if status == "running" and device in self.device_rows:
                    row = self.device_rows[device]
                    start_time = self.device_start_times.get(device)
                    self.table.setItem(row, 8, QTableWidgetItem(get_elapsed_time(start_time)))
            return
        current_devices = get_devices()
        if current_devices != self.devices:
            self.devices = current_devices
            self.initialize_device_status()
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
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                self.table.setCellWidget(row_count, 0, checkbox)
                # Hiển thị tên ghi chú từ device_notes
                self.table.setItem(row_count, 1, QTableWidgetItem(self.device_notes.get(device, f"Máy {i}")))
                self.table.setItem(row_count, 2, QTableWidgetItem(f"{self.device_names.get(device, 'Unknown')} ({device})"))
                self.table.setItem(row_count, 8, QTableWidgetItem("N/A"))
                self.device_rows[device] = row_count
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
    
    def update_button_states(self):
        current_time = time.time()
        if current_time - self.last_button_update < 2:
            return
        self.last_button_update = current_time
        
        running_devices = [dev for dev, status in self.device_status.items() if status == "running"]
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(len(running_devices) > 0)
        self.running = len(running_devices) > 0
     
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
                if self.device_status.get(device_id) != "running":
                    selected_devices.append(device_id)
                    self.device_status[device_id] = "running"
                    self.device_start_times[device_id] = datetime.now()
        
        if not selected_devices:
            self.log_text.append("Không có thiết bị nào được chọn để bắt đầu!")
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
        self.stop_btn.setEnabled(True)
        
        for device in selected_devices:
            if device not in self.device_stop_events:
                self.device_stop_events[device] = threading.Event()
            else:
                self.device_stop_events[device].clear()
            subprocess.run(f"adb -s {device} shell settings put system accelerometer_rotation 0", shell=True)
            subprocess.run(f"adb -s {device} shell settings put system user_rotation 0", shell=True)
            
            thread = threading.Thread(
                target=main, 
                args=(device, self, self.device_stop_events[device], 
                    self.min_delay, self.max_delay, 
                    self.min_reaction_delay, self.max_reaction_delay)
            )
            thread.daemon = True
            self.device_threads[device] = thread
            thread.start()
            
            # Cập nhật giao diện
            if device not in self.device_rows:
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                self.device_rows[device] = row_count
                device_name = self.device_names.get(device, 'Unknown')
                checkbox = QCheckBox()
                self.table.setCellWidget(row_count, 0, checkbox)
                self.table.setItem(row_count, 1, QTableWidgetItem(self.device_notes.get(device, f"Máy {row_count+1}")))
                self.table.setItem(row_count, 2, QTableWidgetItem(f"{device_name} ({device})"))
                self.table.setItem(row_count, 8, QTableWidgetItem(get_elapsed_time(self.device_start_times.get(device))))
            
            self.log_text.append(f"Đã bắt đầu thiết bị: {device}")

    def stop_jobs(self):
        devices_to_stop = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                device_info = self.table.item(row, 2).text() 
                device_id = device_info.split('(')[-1].strip(')')
                if self.device_status.get(device_id) == "running":
                    devices_to_stop.append(device_id)
        
        if not devices_to_stop:
            self.log_text.append("Không có thiết bị nào đang chạy được chọn để dừng!")
            return
        
        for device in devices_to_stop:
            if device in self.device_stop_events:
                self.device_stop_events[device].set()
                self.device_status[device] = "stopped"
                if device in self.device_rows:
                    row = self.device_rows[device]
                    self.table.setItem(row, 8, QTableWidgetItem("Đã dừng"))
                self.log_text.append(f"Đã dừng thiết bị: {device}")
        running_devices = [dev for dev, status in self.device_status.items() if status == "running"]
        self.start_btn.setEnabled(True)
        if not running_devices:
            self.running = False
            self.stop_btn.setEnabled(False)
            self.log_text.append("Tất cả thiết bị đã dừng.")
        else:
            self.log_text.append(f"Còn {len(running_devices)} thiết bị đang chạy.")

    @pyqtSlot(str, int, str, str, int, int, str)
    def add_job_to_table(self, device, stt, fb_id, fb_job, xu_job, tongxu, timestamp):
        self.pending_table_updates[device] = (stt, fb_id, fb_job, xu_job, tongxu, timestamp)

    def update_total_xu(self):
        self.total_xu_all = sum(data["tongxu"] for data in self.job_data.values())
        self.total_xu_label.setText(f"Tổng Xu: {self.total_xu_all}")
    def process_pending_table_updates(self):
        if not self.pending_table_updates:
            return
            
        for device, data in self.pending_table_updates.items():
            row = self.device_rows.get(device)
            if row is not None:
                stt, fb_id, fb_job, xu_job, tongxu, timestamp = data
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
        self.pending_table_updates.clear()    
    def log_message(self, message):
        if self.log_text.document().lineCount() > 500: 
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
        self.log_text.append(message)
        import random
        if random.random() < 0.05: 
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        self.log_processor.stop()
        running_devices = [dev for dev, status in self.device_status.items() if status == "running"]
        
        if running_devices:
            reply = QMessageBox.question(
                self, "Thoát", 
                f"Có {len(running_devices)} thiết bị đang chạy. Bạn có chắc chắn muốn thoát? Hành động này sẽ dừng tất cả thiết bị.",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                for device in running_devices:
                    if device in self.device_stop_events:
                        self.device_stop_events[device].set()
                        self.device_status[device] = "stopped"
                event.accept()
                raise SystemExit(0)
            else:
                event.ignore()
        else:
            reply = QMessageBox.question(
                self, "Thoát", 
                "Bạn có chắc chắn muốn thoát?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
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

    if not fb_id_golike:
        return job_id, "none"
    def normalize_fb_link(raw):
        raw = raw.strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        if raw.startswith("www.") or raw.startswith("facebook.com") or raw.startswith("m.facebook.com"):
            return "https://" + raw if not raw.startswith("http") else raw
        return f"https://facebook.com/{raw}"
    fb_link = normalize_fb_link(fb_id_golike)
    fb_id = "none"
    url = f"https://ffb.vn/api/tool/get-id-fb?idfb={quote_plus(fb_link)}"
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=6)
            text = resp.text.strip()
            try:
                data = resp.json()
            except ValueError:
                data = None

            if isinstance(data, dict) and int(data.get("error", 1)) == 0:
                fb_id_val = data.get("id")
                if fb_id_val:
                    fb_id = str(fb_id_val)
                    return job_id, fb_id
            else:
                m = re.search(r'"id"\s*:\s*"?(?P<id>\d{5,})"?', text)
                if m:
                    fb_id = m.group("id")
                    return job_id, fb_id
        except Exception as e:
            print("Lỗi khi gọi ffb.vn:", e)
            time.sleep(1 + attempt)
            continue
    try:
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.6,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://id.traodoisub.com',
            'Referer': 'https://id.traodoisub.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = {'link': f'https://facebook.com/{fb_id_golike}'}
        retries = 2
        for _ in range(retries):
            response = requests.post('https://id.traodoisub.com/api.php', headers=headers, data=data, timeout=6)
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
        print("Lỗi khi get uid:", e)
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
        if not d(text="Facebook").exists(timeout=5):
            os.system(f"adb -s {device} shell screencap -p /sdcard/screen.png >nul 2>&1")
            os.system(f"adb -s {device} pull /sdcard/screen.png ./screen.png >nul 2>&1")
            img = cv2.imread("screen.png")
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_img, np.array([100, 100, 100]), np.array([130, 255, 255]))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            os.system(f"adb -s {device} shell input tap {x + w // 2} {y + h // 2}")
        time.sleep(2)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(1)
        d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        time.sleep(2)

        # Thông báo giới hạn job
        if d(text="Bạn đã làm quá 100 jobs mỗi ngày chắc mệt mỏi lắm rồi nhỉ :D. GoLike là ứng dụng giúp bạn kiếm thêm ít tiền lúc rảnh rổi, đừng làm dụng quá nhé. Nghỉ ngơi để đảm bảo sức khỏe và quay lại vào ngày mai để làm việc tiếp nhé !").exists(timeout=5):
            print(f"[{device}] Xuất hiện thông báo giới hạn job, dừng luồng.")
            gui.log_queue.put(f"[{device}] Đã đạt giới hạn công việc, dừng thiết bị này.")
            gui.update_table_signal.emit(device, stt, "N/A", "Stopped", 0, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
            return False

        return True
    except:
        return reset_golike(d, device, gui, tongxu, stt)
    
def main(device, gui, stop_event, min_delay=1.5, max_delay=2.5, min_reaction_delay=0.5, max_reaction_delay=1.0):
    tongxu = stt = 0
    last_log_time = time.time()
    log_interval = 3.0
    
    # Kết nối device
    while True:
        try:
            d = u2.connect(device)
            break
        except:
            if stop_event.is_set():
                gui.log_queue.put(f"[{device}] Đã dừng trước khi kết nối")
                return
            continue
    
    # Kiểm tra trạng thái trước khi bắt đầu vòng lặp
    if stop_event.is_set():
        gui.log_queue.put(f"[{device}] Đã dừng trước khi bắt đầu công việc")
        return
    
    gui.log_queue.put(f"[{device}] Đã kết nối và bắt đầu làm việc")
    
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
                    tongxu += xu_job
                    stt += 1
                    gui.update_table_signal.emit(device, stt, "NONE", fb_job, xu_job, tongxu, get_elapsed_time(gui.device_start_times.get(device)))
                    if d(resourceId="swal2-content").exists(timeout=2):
                        bao_loi(d)
                    elif d(text="OK").exists(timeout=5):
                        d(text="OK").click()
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
            subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity -f 0x20000000", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            job_completed = False
            if success:
                if d(text="Hoàn thành").exists(timeout=5):
                    d(text="Hoàn thành").click()
                    time.sleep(1)
                    if d(resourceId="swal2-content").exists(timeout=3):
                        bao_loi(d)
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
                
                current_time = time.time()
                if current_time - last_log_time >= log_interval:
                    gui.log_queue.put(f"[{device}] Đã hoàn thành job {stt}, tổng xu: {tongxu}")
                    last_log_time = current_time
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
            if stop_event.is_set():
                break
        except Exception as e:
            if stop_event.is_set():
                return
            gui.log_queue.put(f"[{device}] Exception: {e}")
            result = reset_golike(d, device, gui, tongxu, stt)
            if result is False:
                break
            gui.log_queue.put(f"[{device}] Đang khởi động lại app Golike")
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
    #check_and_kill_old_instance()
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
                # Hiển thị popup giới thiệu
                intro_dialog = ProductIntroDialog(key_info={"type": "VIP", "name": key_name, "expire_time": expire_time})
                intro_dialog.exec_()  # Chờ người dùng đóng popup
                window.show()
                app.exec_()
                raise SystemExit(0)
        #     else:
        #         QMessageBox.critical(None, "Key Error", error_msg)
        #         attempt += 1
        # elif os.path.exists('Z-Matrix_key.txt'):
        #     with open('Z-Matrix_key.txt', 'r') as file:
        #         key_free = file.read().strip()
        #     success, key_name, expire_time, error_msg = check_key_free(key_free)
        #     if success:
        #         window = MainWindow(key_info={"type": "Free", "name": key_name, "expire_time": expire_time}, zalo_link=zalo_link)
        #         # Hiển thị popup giới thiệu
        #         intro_dialog = ProductIntroDialog(key_info={"type": "Free", "name": key_name, "expire_time": expire_time})
        #         intro_dialog.exec_()  # Chờ người dùng đóng popup
        #         window.show()
        #         app.exec_()
        #         raise SystemExit(0)
            else:
                QMessageBox.critical(None, "Key Error", error_msg)
                attempt += 1
        while attempt < max_attempts:
            key_dialog = KeyInputDialog()
            if key_dialog.exec_():
                window = MainWindow(key_info=key_dialog.key_info, zalo_link=zalo_link)
                # Hiển thị popup giới thiệu
                intro_dialog = ProductIntroDialog(key_info=key_dialog.key_info)
                intro_dialog.exec_()  # Chờ người dùng đóng popup
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