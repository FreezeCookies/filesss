import subprocess
import os
import threading
import time
import re
import requests
import base64
import unicodedata
import uiautomator2 as u2
from datetime import datetime
from fake_useragent import UserAgent

# REACTION MAP
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

headers = {
    "referer": "https://id.traodoisub.com/",
    "user-agent": UserAgent().random,
}

def get_devices():
    output = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.strip()
    lines = output.split("\n")[1:]
    return [line.split()[0] for line in lines if line.strip()]

def device_id():
    devices = get_devices()
    if not devices:
        print("Không tìm thấy thiết bị nào. Vui lòng kiểm tra kết nối ADB.")
        exit(1)
    for stt, dev_id in enumerate(devices, 1):
        print(f"{stt}: {dev_id}")
    choices = input("\nChọn thiết bị (VD: 1,3,4): ").split(",")
    selected = [devices[int(c.strip()) - 1] for c in choices if c.strip().isdigit() and 0 < int(c.strip()) <= len(devices)]
    print("\n ================= Bắt đầu làm việc ================= \n")
    return selected

def check_type(d):
    for golike_job, (fb_job, xu_job) in reaction_map.items():
        if d(text=golike_job).exists:
            return golike_job, fb_job, xu_job
    return "none", None, 0

def check_job(d):
    xml = d.dump_hierarchy()
    job_id_match = re.search(r"Job Id:\s*(\d+)", xml)
    job_id = job_id_match.group(1) if job_id_match else None
    
    fb_id_golike_match = re.search(r"Fb Id:\s*([^\s<]+)", xml)
    fb_id_golike = fb_id_golike_match.group(1).strip() if fb_id_golike_match else None
    if fb_id_golike:
        fb_id_golike = fb_id_golike.strip().strip('"').strip("'")
    
    print(f"FB ID from Golike: {fb_id_golike}")
    
    try:
        data = {"link": f"https://www.facebook.com/{fb_id_golike}"}
        while True:
            response = requests.post("https://id.traodoisub.com/api.php", headers=headers, data=data).json()
            print(f"Response from API: {response}")
            if "error" in response:
                err = unicodedata.normalize("NFC", response["error"])
                if err in ["Vui lòng thao tác chậm lại", "Vui lòng thử lại!"]:
                    time.sleep(2)
                    continue
                else:
                    return job_id, "none"
            else:
                return job_id, response['id']
    except Exception as e:
        print(f"Lỗi khi lấy FB ID: {e}")
        return job_id, "none"

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
    except Exception as e:
        print(f"Lỗi reset Golike: {e}")
        reset_golike(d, device)

def main(device):
    tongxu = stt = 0
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            print(f"Đang kết nối tới thiết bị: {device}")
            d = u2.connect(device)
            print(f"Kết nối thành công tới thiết bị: {device}")
            break
        except Exception as e:
            print(f"Lỗi kết nối tới {device}: {e}")
            retry_count += 1
            if retry_count == max_retries:
                print(f"Không thể kết nối tới {device} sau {max_retries} lần thử. Thoát.")
                return
            print(f"Thử lại lần {retry_count}/{max_retries}...")
            time.sleep(5)  # Tăng thời gian chờ để tránh lặp quá nhanh

    while True:
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
                selected_fb_job = None
                selected_xu_job = 0
                for job, xu in map_type_job.items():
                    if d(text=job).exists:
                        d(text=job).click()
                        selected_fb_job = job
                        selected_xu_job = xu
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
                else:
                    tongxu += selected_xu_job
                    stt += 1
                    print(f"[{device}] | {stt} |         NONE         | {selected_fb_job:<15} | {selected_xu_job} | {tongxu} | {datetime.now().strftime('%H:%M:%S')}")
                continue

            job_id, fb_id = check_job(d)
            print(f"Golike Job: {golike_job}")
            print(f"FB Job: {fb_job}")
            print(f"Xu Job: {xu_job}")
            print(f"Job ID: {job_id}")
            print(f"FB ID: {fb_id}")

            if fb_id == "none":
                bao_loi(d)
                continue

            if d(text="Click để Copy bình luận").exists:
                d(text="Click để Copy bình luận").click()

            d(text="Facebook").click()
            time.sleep(1.5)
            text = f"S:_I{job_id}:{fb_id}"
            s = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            link = s.rstrip('=')
            print(f"Generated link: {link}")

            command = f'adb -s {device} shell am start -a android.intent.action.VIEW -d "fb://native_post/{link}" -f 0x10008000'
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            time.sleep(1)
            action_success = False
            for i in range(5):
                if d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").exists:
                    if fb_job == "Bình luận":
                        d(description=f"{fb_job}").click()
                        time.sleep(1)
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
                                d(description="Nút Thích. Hãy nhấn đúp và giữ để bày tỏ cảm xúc về bình luận.").click()
                            except:
                                break
                    time.sleep(1)
                    action_success = True
                    break
                else:
                    d.swipe(0.4, 0.7, 0.4, 0.5, duration=0.1)
                    time.sleep(0.5)

            if not action_success:
                print("Không tìm thấy nút tương tác. Resetting...")
                reset_golike(d, device)
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
                        bounds = d(text="OK").bounds()
                        center_x = (bounds[0] + bounds[2]) // 2
                        center_y = (bounds[1] + bounds[3]) // 2
                        d.click(center_x, center_y)
                    except:
                        pass
            d.swipe(0.5, 0.7, 0.5, 0.6, duration=0.1)
            d.swipe(0.5, 0.6, 0.5, 0.7, duration=0.1)
            time.sleep(1)
            if d(text="Hoàn thành").exists:
                bao_loi(d)
            else:
                tongxu += xu_job
                stt += 1
                print(f"[{device}] | {stt} | {fb_id:<20} | {fb_job:<15} | {xu_job} | {tongxu} | {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Lỗi trong quá trình thực hiện trên {device}: {e}")
            reset_golike(d, device)

def threading_device():
    devices = device_id()
    threads = []
    for dev in devices:
        t = threading.Thread(target=main, args=(dev,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

if __name__ == "__main__":
    threading_device()