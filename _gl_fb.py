import subprocess, os, threading, time, re, requests, base64, json, platform, random, string, webbrowser
import psutil
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QTextEdit, QLabel,
                             QDialog, QLineEdit, QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QHeaderView
import sys

# REACTION
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

# Key encoding and device ID
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
        base_folder = 'D:\\.system\\_FOLDER IMPORTANT_'
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

# Debug detection
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
            sys.exit(1)
        time.sleep(interval)

# Server and key checking
def check_server():
    try:
        response = requests.get('https://zmatrixtool.x10.mx/Api/server_glfb.php', timeout=5)
        response.raise_for_status()
        data = response.json()
        if 'status' in data and data['status'] == 'live':
            return True
        else:
            zalo = "https://zalo.me/g/axtnqv555"
            QMessageBox.critical(None, "Server Status", f"Server đã được admin tắt để bảo trì\nBox Zalo: {zalo}\nVui lòng tham gia group để nhận thông báo sớm nhất!")
            raise RuntimeError("Server is under maintenance")
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(None, "Server Error", f"Connection error: {str(e)}\nPlease check your network.")
        raise RuntimeError(f"Server connection error: {str(e)}")
    except ValueError:
        QMessageBox.critical(None, "Server Error", "Invalid server response. Please try again later.")
        raise RuntimeError("Invalid server response")

def check_key_vip(key, hwid):
    try:
        response = requests.get(f'https://zmatrixtool.x10.mx/shop/data/check_key_vip.php?key={key}&hwid={hwid}', timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == "active" and data.get('message') == "Key hợp lệ.":
            with open('Z-Matrix_key_vip.txt', 'w') as file:
                file.write(key)
            return True, data.get('user', 'Unknown'), data.get('expiry', 'Unknown')
        else:
            if os.path.exists('Z-Matrix_key_vip.txt'):
                os.remove('Z-Matrix_key_vip.txt')
            QMessageBox.critical(None, "Key Error", data.get('message', 'Key vip không hợp lệ hoặc đã hết hạn.'))
            return False, None, None
    except requests.exceptions.RequestException as e:
        if os.path.exists('Z-Matrix_key_vip.txt'):
            os.remove('Z-Matrix_key_vip.txt')
        QMessageBox.critical(None, "Key Error", f"Connection error: {str(e)}")
        return False, None, None
    except ValueError:
        if os.path.exists('Z-Matrix_key_vip.txt'):
            os.remove('Z-Matrix_key_vip.txt')
        QMessageBox.critical(None, "Key Error", "Invalid server response.")
        return False, None, None

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
            return True, "Free", expiry
        else:
            if os.path.exists('Z-Matrix_key.txt'):
                os.remove('Z-Matrix_key.txt')
            QMessageBox.critical(None, "Key Error", data.get('message', 'Key free không hợp lệ hoặc đã hết hạn.'))
            return False, None, None
    except requests.exceptions.RequestException as e:
        if os.path.exists('Z-Matrix_key.txt'):
            os.remove('Z-Matrix_key.txt')
        QMessageBox.critical(None, "Key Error", f"Connection error: {str(e)}")
        return False, None, None
    except ValueError:
        if os.path.exists('Z-Matrix_key.txt'):
            os.remove('Z-Matrix_key.txt')
        QMessageBox.critical(None, "Key Error", "Invalid server response.")
        return False, None, None

# Dialog for key input
class KeyInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lí key")
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 16px;
                color: #333333;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                padding: 8px;
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 10px;
            }
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                padding: 8px;
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 10px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cccccc;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px;
                font-size: 14px;
                border-radius: 10px;
                border: 1px solid #218838;
            }
            QPushButton:hover {
                background-color: #34c759;
            }
            QPushButton#cancel {
                background-color: #dc3545;
                border: 1px solid #c82333;
            }
            QPushButton#cancel:hover {
                background-color: #ff4c5b;
            }
            QPushButton#copy {
                background-color: #007bff;
                border: 1px solid #0056b3;
            }
            QPushButton#copy:hover {
                background-color: #0056b3;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

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

        self.label = QLabel("Vui lòng chọn loại key bạn muốn dùng.")
        layout.addWidget(self.label)

        self.key_type = QComboBox()
        self.key_type.addItems(["Free Key", "VIP Key"])
        layout.addWidget(self.key_type)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Nhập key vào đây")
        layout.addWidget(self.key_input)

        button_layout = QHBoxLayout()
        self.get_key_btn = QPushButton("Nhấn vào đây để get key")
        self.get_key_btn.clicked.connect(self.open_key_link)
        button_layout.addWidget(self.get_key_btn)

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.check_key)
        button_layout.addWidget(self.submit_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def copy_device_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.device_id)
        QMessageBox.information(self, "Copied", "Đã copy id device cho bạn.")

    def open_key_link(self):
        key_type = self.key_type.currentText()
        if key_type == "Free Key":
            webbrowser.open("https://zmatrixtool.x10.mx/getkey/")
        else:  # VIP Key
            webbrowser.open("https://zmatrixtool.x10.mx/shop")

    def get_key(self):
        return self.key_input.text().strip()

    def check_key(self):
        key = self.key_input.text().strip()
        key_type = self.key_type.currentText()
        if not key:
            QMessageBox.critical(self, "Key Error", "Vui lòng nhập key!")
            return
        if key_type == "Free Key":
            success, key_name, expire_time = check_key_free(key)
            if success:
                self.key_info = {"type": "Free", "name": key_name, "expire_time": expire_time}
                QMessageBox.information(self, "Success", "Key free đúng! Đang kết nối đến Server...")
                self.accept()
        else:  # VIP Key
            hwid = self.device_id
            success, key_name, expire_time = check_key_vip(key, hwid)
            if success:
                self.key_info = {"type": "VIP", "name": key_name, "expire_time": expire_time}
                QMessageBox.information(self, "Success", "Key vip đúng! Đang kết nối đến Server...")
                self.accept()

class MainWindow(QMainWindow):
    def __init__(self, key_info=None, zalo_link="Unknown"):
        super().__init__()
        self.key_info = key_info or {"type": "Unknown", "name": "Unknown", "expire_time": "Unknown"}
        self.zalo_link = zalo_link
        self.setWindowTitle("Golike FaceBook - ZMATRIX")
        self.setGeometry(100, 100, 1200, 800)
        self.devices = []
        self.device_names = {}
        self.selected_devices = []
        self.running = False
        self.threads = []
        self.job_data = {}
        self.device_rows = {}
        self.init_ui()

    def init_ui(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
        palette.setColor(QPalette.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ButtonText, QColor(51, 51, 51))
        self.setPalette(palette)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)

        # Device and buttons layout
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        # Device selection
        device_layout = QVBoxLayout()
        device_label = QLabel("Chọn thiết bị để chạy:", styleSheet="font-size: 16px; color: #333333;")
        device_layout.addWidget(device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(500)
        self.device_combo.setFixedHeight(40)
        self.device_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                padding: 10px;
                font-size: 16px;
                border: 1px solid #cccccc;
                border-radius: 10px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cccccc;
                border-radius: 10px;
            }
        """)
        self.device_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.update_device_list()
        device_layout.addWidget(self.device_combo)
        top_layout.addLayout(device_layout, 4)  # 40% width

        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedSize(150, 50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 10px;
                border: 1px solid #218838;
            }
            QPushButton:hover {
                background-color: #34c759;
            }
            QPushButton:disabled {
                background-color: #d3d3d3;
                border: 1px solid #b0b0b0;
            }
        """)
        self.start_btn.clicked.connect(self.start_jobs)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(150, 50)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 10px;
                border: 1px solid #c82333;
            }
            QPushButton:hover {
                background-color: #ff4c5b;
            }
            QPushButton:disabled {
                background-color: #d3d3d3;
                border: 1px solid #b0b0b0;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_jobs)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        top_layout.addLayout(button_layout, 2)  # 20% width

        # Key info and instructions (right side, full height in full-screen)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        # Key info
        key_info_label = QLabel(
            f"Loại Key: {self.key_info['type']}\n"
            f"Tên người sở hữu: {self.key_info['name']}\n"
            f"Thời hạn: {self.key_info['expire_time']}\n"
            f"Zalo Contact: {self.zalo_link}"
        )
        key_info_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            background-color: #ffffff;
            padding: 15px;
            border: 1px solid #cccccc;
            border-radius: 10px;
        """)
        key_info_label.setMinimumWidth(300)
        key_info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout.addWidget(key_info_label)

        # Instructions
        instructions_label = QLabel(
            "Hướng dẫn sử dụng tool:\n"
            "1. Kết nối thiết bị Android qua ADB.\n"
            "2. Chọn thiết bị từ danh sách bên trái.\n"
            "3. Lên điện thoại, vào app Golike -> Kiếm Thưởng -> FaceBook.\n"
            "4. Sau khi hoàn tất các bước trên. Bấm start để bắt đầu chạy.\n"
            "5. Theo dõi tiến trình trong bảng và log bên dưới.\n"
            "6. Nhấn 'Stop' để dừng công việc.\n"
            "Lưu ý: Đảm bảo Golike và Facebook đã được cài đặt trên thiết bị."
        )
        instructions_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            background-color: #ffffff;
            padding: 15px;
            border: 1px solid #cccccc;
            border-radius: 10px;
        """)
        instructions_label.setMinimumWidth(300)
        instructions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(instructions_label)
        right_layout.addStretch()  # Stretch to fill right side in full-screen
        top_layout.addLayout(right_layout, 4)  # 40% width
        
        main_layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Device", "STT", "FB ID", "Job Type", "Xu", "Total Xu", "Time"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #333333;
                gridline-color: #cccccc;
                font-size: 14px;
                border: 1px solid #cccccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 8px;
                font-size: 14px;
                border: 1px solid #cccccc;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:alternate {
                background-color: #f9f9f9;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setFixedHeight(300)
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        main_layout.addWidget(self.table)

        # Logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
            font-size: 14px;
            padding: 5px;
            border-radius: 10px;
        """)
        main_layout.addWidget(QLabel("Bảng theo dõi Logs:", styleSheet="font-size: 16px; color: #333333;"))
        main_layout.addWidget(self.log_text)

        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.update_device_list)
        self.device_timer.start(5000)

    def update_device_list(self):
        current_devices = get_devices()
        if current_devices != self.devices:
            self.devices = current_devices
            self.device_names = {}
            for device in self.devices:
                try:
                    name = subprocess.run(f"adb -s {device} shell getprop ro.product.model",
                                        shell=True, capture_output=True, text=True).stdout.strip()
                    self.device_names[device] = name if name else "Unknown"
                except:
                    self.device_names[device] = "Unknown"
            self.device_combo.clear()
            self.device_combo.addItem("Chọn thiết bị để chạy")
            for device in self.devices:
                self.device_combo.addItem(f"{self.device_names[device]} ({device})")

    def start_jobs(self):
        if self.device_combo.currentIndex() == 0:
            self.log_text.append("Vui lòng chọn thiết bị!")
            return
        # Update device list before starting jobs to ensure it's not empty
        self.update_device_list()
        if not self.devices:
            self.log_text.append("Không tìm thấy thiết bị nào! Vui lòng kết nối thiết bị qua ADB.")
            return
        try:
            self.selected_devices = [self.devices[self.device_combo.currentIndex() - 1]]
        except IndexError:
            self.log_text.append("Lỗi: Thiết bị được chọn không hợp lệ. Vui lòng thử lại.")
            return
        self.running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.append(f"Bắt đầu làm việc với id: {self.selected_devices[0]}")
        self.threads = []
        for device in self.selected_devices:
            if device not in self.device_rows:
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)
                self.device_rows[device] = row_count
                device_name = self.device_names.get(device, 'Unknown')
                self.table.setItem(row_count, 0, QTableWidgetItem(f"{device_name} ({device})"))
            self.job_data[device] = {"stt": 0, "tongxu": 0}
            t = threading.Thread(target=main, args=(device, self))
            self.threads.append(t)
            t.start()

    def stop_jobs(self):
        self.running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_text.append("Đang dừng nhiệm vụ...")

    def add_job_to_table(self, device, stt, fb_id, fb_job, xu_job, tongxu, timestamp):
        row = self.device_rows.get(device, 0)
        self.table.setItem(row, 1, QTableWidgetItem(str(stt)))
        self.table.setItem(row, 2, QTableWidgetItem(fb_id))
        self.table.setItem(row, 3, QTableWidgetItem(fb_job))
        self.table.setItem(row, 4, QTableWidgetItem(str(xu_job)))
        self.table.setItem(row, 5, QTableWidgetItem(str(tongxu)))
        self.table.setItem(row, 6, QTableWidgetItem(timestamp))

    def log_message(self, message):
        self.log_text.append(message)

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
        while True:
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
            reset_golike(d, device)
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
    except:
        reset_golike(d, device)

def main(device, gui):
    tongxu = stt = 0
    while True:
        try:
            d = u2.connect(device)
            break
        except:
            continue
    while gui.running:
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
                d(text="Facebook").click()
                time.sleep(2)
                map_type_job = {
                    "Thích": 40,
                    "Theo dõi": 65
                }
                for fb_job, xu_job in map_type_job.items():
                    if d(text=fb_job).exists:
                        d(text=fb_job).click()
                        break
                time.sleep(1)
                subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity --activity-reorder-to-front", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                d(text="Hoàn thành").click()
                time.sleep(1)
                d(text="OK").click()
                d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
                d.swipe(0.5, 0.6, 0.5, 0.8, duration=0.1)
                time.sleep(1)
                if d(text="Hoàn thành").exists:
                    bao_loi(d)
                    gui.log_message(f"[{device}] Đã báo lỗi cho công việc")
                else:
                    tongxu += xu_job
                    stt += 1
                    gui.add_job_to_table(device, stt, "NONE", fb_job, xu_job, tongxu, datetime.now().strftime("%H:%M:%S"))
                continue
            job_id, fb_id = check_job(d)
            if fb_id == "none":
                bao_loi(d)
                gui.log_message(f"[{device}] Đã báo lỗi cho công việc")
                continue

            if d(text="Click để Copy bình luận").exists:
                d(text="Click để Copy bình luận").click()

            d(text="Facebook").click()
            time.sleep(1.5)
            text = f"S:_I{job_id}:{fb_id}"
            s = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            link = s.rstrip('=')
            command = f'adb -s {device} shell am start -a android.intent.action.VIEW -d "fb://native_post/{link}" -f 0x10008000'
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
                    time.sleep(1)
                    break
                else:
                    d.swipe(0.4, 0.7, 0.4, 0.5, duration=0.1)
                    time.sleep(0.5)
                    continue
            
            subprocess.run(f"adb -s {device} shell am start -n com.golike/.MainActivity --activity-reorder-to-front", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                gui.log_message(f"[{device}] Đã báo lỗi cho công việc")
            else:
                tongxu += xu_job
                stt += 1
                gui.add_job_to_table(device, stt, fb_id, fb_job, xu_job, tongxu, datetime.now().strftime("%H:%M:%S"))
        except Exception as e:
            gui.log_message(f"[{device}] Exception: {str(e)}")
            reset_golike(d, device)
            gui.log_message(f"[{device}] Đang khởi động lại app Golike")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Check debug tools first
    # if detect_debug_tools():
    #     QMessageBox.critical(None, "Debug Detected", "Debug tools detected. Application will exit. Please disable debugging tools.")
    #     sys.exit(1)

    # # Start debug detection thread
    # debug_thread = threading.Thread(target=auto_kill_if_debug_detected, daemon=True)
    # debug_thread.start()

    try:
        # Check server
        check_server()

        # Get Zalo link
        try:
            zalo_link = "https://zalo.me/g/axtnqv555"
        except:
            zalo_link = "https://zalo.me/g/axtnqv555"

        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            # Check existing keys
            if os.path.exists('Z-Matrix_key_vip.txt'):
                with open('Z-Matrix_key_vip.txt', 'r') as file:
                    key_vip = file.read().strip()
                hwid = get_device_id()
                success, key_name, expire_time = check_key_vip(key_vip, hwid)
                if success:
                    window = MainWindow(key_info={"type": "VIP", "name": key_name, "expire_time": expire_time}, zalo_link=zalo_link)
                    window.show()
                    sys.exit(app.exec_())
                attempt += 1
                continue
            if os.path.exists('Z-Matrix_key.txt'):
                with open('Z-Matrix_key.txt', 'r') as file:
                    key_free = file.read().strip()
                success, key_name, expire_time = check_key_free(key_free)
                if success:
                    window = MainWindow(key_info={"type": "Free", "name": key_name, "expire_time": expire_time}, zalo_link=zalo_link)
                    window.show()
                    sys.exit(app.exec_())
                attempt += 1
                continue

            # Show key input dialog
            key_dialog = KeyInputDialog()
            if key_dialog.exec_():
                window = MainWindow(key_info=key_dialog.key_info, zalo_link=zalo_link)
                window.show()
                sys.exit(app.exec_())
            attempt += 1
        QMessageBox.critical(None, "Key Error", "Đã quá 3 lần thử.")
        sys.exit(1)
    except RuntimeError:
        sys.exit(1)