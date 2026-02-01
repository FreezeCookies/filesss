import uiautomator2 as u2
import subprocess
import time
import re
import base64
import requests
import sys
from datetime import datetime
import json
import unicodedata
import os
import threading
from queue import Queue
import psutil
import platform

# Biến toàn cục chia sẻ giữa các luồng
tong_tien_chung = 0
dem_job_chung = 0
DELAY_DEFAULT = 3
print_lock = threading.Lock()
last_stats = ""  # Lưu trữ thống kê lần trước để tránh in trùng

# Công cụ thuộc quyền sở hữu của Z-MATRIX
Z_MATRIX_TOOLS = ["VUI LÒNG KHÔNG PHÁ HAY CAN THIỆP VÀO TOOL", "uiautomator2", "requests", "adb"]

# Lớp lỗi tùy chỉnh
class TikTokToolError(Exception):
    pass

# Kiểm tra hệ điều hành
def check_os():
    if platform.system() != "Windows":
        print("Lỗi: Tool này chỉ hỗ trợ chạy trên Windows.")
        raise SystemExit()

check_os()

def check_server():
    try:
        url = "https://zmatrixtool.x10.mx/Api/secret.php"
        r = requests.get(url, timeout=10)
        data = r.json()  # Parse JSON
        status = data.get("status", "").lower()
        if status != "live":
            try:
                os.remove(sys.argv[0])
            except Exception as e:
                print("")
            raise SystemExit(0)
    except Exception as e:
        raise SystemExit(0)

check_server()

# ====== Hàm tiện ích ======
def delay(sec=DELAY_DEFAULT):
    time.sleep(sec)

def remove_vietnamese_diacritics(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text

def print_stats(workers):
    global last_stats, tong_tien_chung, dem_job_chung
    
    # Tạo nội dung thống kê mới với giao diện box double-line
    stats = "╔════════════════════════════════════╗\n"
    stats += "║         THỐNG KÊ TỔNG HỢP         ║\n"
    stats += "╚════════════════════════════════════╝\n"
    stats += f"║ Tổng job: {dem_job_chung:<22} ║\n"
    stats += f"║ Tổng tiền: {tong_tien_chung}₫{' ':<19} ║\n"
    stats += "╚════════════════════════════════════╝\n"
    
    for worker in workers:
        stats += f"║ Thiết bị {worker.device_id}: {worker.dem_job} job - {worker.tong_tien}₫{' ':<6} ║\n"
    
    stats += "╚════════════════════════════════════╝\n"
    
    # Chỉ in nếu khác với lần trước
    if stats != last_stats:
        with print_lock:
            os.system('cls')
            print(f"Powered by Z-MATRIX Tools: {', '.join(Z_MATRIX_TOOLS)}")
            print(stats)
            last_stats = stats

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

# ====== Quét và chọn thiết bị ======
def lay_danh_sach_thiet_bi():
    result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")[1:]
    devices = [line.split("\t")[0] for line in lines if "\tdevice" in line]
    
    if not devices:
        safe_print("Không tìm thấy thiết bị nào ở trạng thái 'device'. Hãy kiểm tra kết nối ADB.")
        raise SystemExit()
    
    return devices

# ====== Phát hiện công cụ debug ======
def detect_debug_tools():
    suspicious_keywords = [
        "charles", "fiddler", "httptoolkit", "mitmproxy", "canary", "proxyman",
        "burp", "wireshark", "tcpdump", "mitm", "proxy"
    ]
    suspicious_ports = [
        "127.0.0.1:8000", "127.0.0.1:8080", "127.0.0.1:8888",
        "127.0.0.1:9090", "127.0.0.1:8081", "127.0.0.1:8889"
    ]
    ssl_cert_vars = ["SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"]
    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]
    
    # Danh sách trắng để tránh false positives
    allowed_processes = ["python", "cmd", "powershell", "explorer", "adb"]
    allowed_ports = ["127.0.0.1:5037"]  # Cổng ADB mặc định
    
    # Kiểm tra biến môi trường
    if os.environ.get("HTTP_TOOLKIT_ACTIVE", "").lower() == "true":
        safe_print("Cảnh báo debug: Phát hiện HTTP_TOOLKIT_ACTIVE được bật.")
        return True
    
    for var in ssl_cert_vars + proxy_env_vars:
        val = os.environ.get(var, "").lower()
        if val and (any(kw in val for kw in suspicious_keywords) or any(port in val for port in suspicious_ports)):
            safe_print(f"Cảnh báo debug: Phát hiện biến môi trường nghi ngờ: {var} = {val}")
            return True
    
    # Kiểm tra proxy của trình duyệt
    if os.environ.get("FIREFOX_PROXY", "") in suspicious_ports:
        safe_print("Cảnh báo debug: Phát hiện FIREFOX_PROXY sử dụng cổng nghi ngờ.")
        return True
    
    # Kiểm tra các tiến trình đang chạy
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            name = proc.info.get('name', '').lower()
            cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
            if name not in allowed_processes and any(kw in name or kw in cmdline for kw in suspicious_keywords):
                safe_print(f"Cảnh báo debug: Phát hiện tiến trình nghi ngờ: {name} (cmdline: {cmdline})")
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    # Kiểm tra các cổng mạng đang mở
    try:
        for conn in psutil.net_connections():
            if conn.laddr.ip == "127.0.0.1" and str(conn.laddr.port) in [port.split(":")[1] for port in suspicious_ports] and f"{conn.laddr.ip}:{conn.laddr.port}" not in allowed_ports:
                safe_print(f"Cảnh báo debug: Phát hiện cổng mạng nghi ngờ: {conn.laddr.ip}:{conn.laddr.port}")
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    return False

def auto_kill_if_debug_detected(interval=5, bypass=False):
    if bypass:
        safe_print("Cảnh báo: Kiểm tra debug đã bị tắt theo yêu cầu người dùng.")
        return
    while True:
        if detect_debug_tools():
            with print_lock:
                print("╔════════════════════════════════════╗")
                print("║         PHÁT HIỆN DEBUG          ║")
                print("╚════════════════════════════════════╝")
                print("║ Phát hiện công cụ debug, tool sẽ dừng ngay lập tức! ║")
                print("║ Vui lòng tắt các công cụ debug trước khi tiếp tục. ║")
                print("╚════════════════════════════════════╝")
            raise TikTokToolError("Phát hiện công cụ debug")
        time.sleep(interval)

# ====== Lớp xử lý cho từng thiết bị ======
class DeviceWorker(threading.Thread):
    def __init__(self, device_id, result_queue):
        threading.Thread.__init__(self)
        self.device_id = device_id
        self.result_queue = result_queue
        self.adb_prefix = f"adb -s {device_id}"
        self.d = u2.connect(device_id)
        self.tong_tien = 0
        self.dem_job = 0
        self.running = True
        
    def run(self):
        safe_print(f"Bắt đầu xử lý trên thiết bị: {self.device_id} (Powered by Z-MATRIX Tools)")
        try:
            self.reset_golike()
            while self.running:
                self.xu_ly_job()
        except Exception as e:
            safe_print(f"Lỗi trên thiết bị {self.device_id}: {str(e)}")
            raise
        finally:
            safe_print(f"Kết thúc xử lý trên thiết bị: {self.device_id}")
    
    def reset_golike(self):
        os.system(f"{self.adb_prefix} shell am start -n com.golike/.MainActivity >nul 2>&1")
        delay(10)
        self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
        delay(1)
        if self.d(text="Đã hiểu").exists:
            self.d(text="Đã hiểu").click()
        delay(1)
        if self.d(text="Kiếm Thưởng").exists:
            self.d(text="Kiếm Thưởng").click()
        delay(2)
        if self.d(text="Facebook").exists:
            self.d(text="Facebook").click()
        delay(4)
    
    def bao_loi(self):
        self.d.swipe(0.5, 0.8, 0.5, 0.4, duration=0.2)
        delay(0.5)
        if self.d(text="Báo lỗi").exists:
            self.d(text="Báo lỗi").click()
            delay(1)
            self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.2)
            delay(1)
            if self.d(text="Gửi báo cáo").exists:
                self.d(text="Gửi báo cáo").click()
                if self.d(text="OK").wait(timeout=10):
                    self.d(text="OK").click()
    
    def lay_job_info(self):
        price_map = {
            "LIKE cho bài viết:": 35,
            "LOVE cho bài viết:": 56,
            "HAHA cho bài viết:": 63,
            "WOW cho bài viết:": 56,
            "SAD cho bài viết:": 100,
            "ANGRY cho bài viết:": 100,
            "Tăng Thương thương cho bài viết:": 56,
            "Tăng LIKE cho Fanpage:": 40  # job cần bỏ qua
        }

        for keyword, gia in price_map.items():
            if self.d(text=keyword).exists:
                if keyword == "Tăng LIKE cho Fanpage:":
                    self.bao_loi()
                    raise Exception("Job không hỗ trợ")

                title_job = keyword
                gia_job = gia
                self.d(text=keyword).click()
                delay(1)

                if self.d(text="OK").exists:
                    self.d(text="OK").click()
                    delay(0.5)
                    if self.d(text=keyword).exists:
                        self.d(text=keyword).click()
                        delay(1.5)
                break
        else:
            raise Exception("Không tìm thấy job phù hợp")

        xml = self.d.dump_hierarchy()

        job_id_match = re.search(r"Job Id:\s*(\d+)", xml)
        job_id = job_id_match.group(1) if job_id_match else None

        fb_id_match = re.search(r"Fb Id:\s*([^\s<]+)", xml)
        fb_id = fb_id_match.group(1).strip() if fb_id_match else None
        if fb_id:
            fb_id = fb_id.strip().strip('"').strip("'")

        return job_id, fb_id, title_job, gia_job
    
    def xu_ly_fb_id(self, fb_id):
        if not fb_id:
            return None

        if fb_id.isdigit():
            return fb_id

        url = f"https://zmatrixtool.x10.mx/id.php?url=https://www.facebook.com/{fb_id}"
        for attempt in range(1, 3):
            try:
                r = requests.get(url, timeout=10)
                text = r.text.strip()

                if "Vui lòng thao tác chậm lại" in text:
                    delay(2)
                    return None

                match = re.search(r'\{.*\}', text, re.S)
                if match:
                    try:
                        data = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        data = {}
                    uid = data.get("response", {}).get("id")
                    if uid:
                        return uid
            except Exception:
                delay(2)
        self.bao_loi()
        return None
    
    def mo_job(self, id_job, numeric_fbid):
        text_string = f"S:_I{id_job}:{numeric_fbid}"
        encoded_text = base64.b64encode(text_string.encode()).decode()
        cmd = f'{self.adb_prefix} shell am start -a android.intent.action.VIEW -d "fb://native_post/{encoded_text}?story_cache_id=null"'
        if self.d(text="Facebook").exists:
            self.d(text="Facebook").click()
            delay(1.5)
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        delay(1)
    
    def tha_cam_xuc(self, loai_job):
        reaction = "Thích"
        like_selectors = [
            self.d(text="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận."),
            self.d.xpath('//*[@content-desc="Chi tiết video"]/android.view.ViewGroup[4]/android.widget.Button[1]'),
            self.d(description="Nút Thích"),
            self.d.xpath('//android.widget.Button[contains(@content-desc, "Thích")]')
        ]

        for vuot in range(3):
            if vuot > 0:
                self.d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.15)
                delay(1)

            found = False
            start_time = time.time()
            while time.time() - start_time < 2:
                for selector in like_selectors:
                    try:
                        if selector.exists:
                            found = selector
                            break
                    except:
                        continue
                if found:
                    break
                time.sleep(0.2)

            if found:
                try:
                    found.long_click(duration=1)
                    delay(0.7)
                    if self.d(description=reaction).exists:
                        self.d(description=reaction).click()
                        delay(1)
                        return True
                    else:
                        found.click()
                        return True
                except:
                    continue
        self.bao_loi()
        return False
    
    def xu_ly_job(self):
        try:
            job_id, fb_id, title_job, gia_job = self.lay_job_info()
            if not job_id or not fb_id or not title_job:
                delay(2)
                return

            numeric_fbid = self.xu_ly_fb_id(fb_id)
            if not numeric_fbid:
                self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
                delay(2)
                return

            loai_job = remove_vietnamese_diacritics(title_job).upper().replace(" ", "")

            self.mo_job(job_id, numeric_fbid)
            delay(3)

            if not self.tha_cam_xuc(loai_job):
                subprocess.run(f"{self.adb_prefix} shell am start -n com.golike/.MainActivity --activity-reorder-to-front",
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                delay(2)
                self.bao_loi()
                return

            subprocess.run(f"{self.adb_prefix} shell am start -n com.golike/.MainActivity --activity-reorder-to-front",
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            delay(3)

            if self.d(text="Hoàn thành").exists:
                self.d(text="Hoàn thành").click()
                delay(1)
                for _ in range(20):
                    if self.d(text="Lỗi").exists:
                        self.d(text="OK").click()
                        self.bao_loi()
                        break
                    elif self.d(text="OK").exists:
                        self.d(text="OK").click()
                        self.dem_job += 1
                        self.tong_tien += gia_job
                        
                        # Cập nhật biến toàn cục
                        global tong_tien_chung, dem_job_chung
                        with print_lock:
                            tong_tien_chung += gia_job
                            dem_job_chung += 1
                        
                        safe_print(f"[Thiết bị: {self.device_id}] | Job {self.dem_job} | +{gia_job}₫ | Tổng: {self.tong_tien}₫ | {datetime.now().strftime('%H:%M:%S')} | Powered by Z-MATRIX Tools")
                        break
                    delay(1)

            delay(1)
            self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
            self.d.swipe(0.5, 0.8, 0.5, 0.6, duration=0.1)
            delay(2)

        except Exception as e:
            self.reset_golike()
            raise

# ====== Hàm chính ======
def main():
    check_server()
    
    # Hỏi người dùng có muốn tắt kiểm tra debug không
    bypass_debug = input("Bỏ qua kiểm tra công cụ debug? (y/n): ").lower() == 'y'
    if not bypass_debug:
        threading.Thread(target=auto_kill_if_debug_detected, args=(5, False), daemon=True).start()
    else:
        safe_print("Kiểm tra debug đã bị tắt theo yêu cầu người dùng.")
    
    global tong_tien_chung, dem_job_chung
    
    devices = lay_danh_sach_thiet_bi()
    
    print(f"Danh sách thiết bị (Powered by Z-MATRIX Tools: {', '.join(Z_MATRIX_TOOLS)}):")
    for i, dev in enumerate(devices, start=1):
        print(f"{i}. {dev}")
    
    selected_indices = input("Chọn thiết bị để chạy (nhập số cách nhau bằng dấu phẩy, hoặc 'all' để chọn tất cả): ")
    
    if selected_indices.lower() == 'all':
        selected_devices = devices
    else:
        try:
            selected_indices = list(map(int, selected_indices.split(',')))
            selected_devices = [devices[i-1] for i in selected_indices if 1 <= i <= len(devices)]
        except:
            print("Lựa chọn không hợp lệ")
            raise SystemExit()
    
    if not selected_devices:
        print("Không có thiết bị nào được chọn")
        raise SystemExit()
    
    result_queue = Queue()
    workers = []
    
    for device_id in selected_devices:
        worker = DeviceWorker(device_id, result_queue)
        worker.start()
        workers.append(worker)
    
    try:
        # Hiển thị thống kê khi có thay đổi
        while True:
            print_stats(workers)
            time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nĐang dừng các luồng...")
        for worker in workers:
            worker.running = False
        for worker in workers:
            worker.join()
        
        # In kết quả cuối cùng
        print_stats(workers)

if __name__ == "__main__":
    main()