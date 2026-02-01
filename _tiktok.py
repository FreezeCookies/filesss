import uiautomator2 as u2 
from curl_cffi import requests
from fake_useragent import UserAgent
import subprocess
import os
import time
import random
import numpy as np
import cv2
import multiprocessing

session     = requests.Session() 

bo_job_be     =  int(input("Nhập số xu job muốn bỏ: "))

min_delay_job =  int(input("Nhập min delay mở job: "))
max_delay_job =  int(input("Nhập max delay mở job: "))
min_lam_job   =  int(input("Nhập min sau khi làm job: "))
max_lam_job   =  int(input("Nhập max sau khi làm job: "))

def get_devices():
    return [line.split()[0] for line in subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.strip().split("\n")[1:] if line.strip()]

def get_device_id():
    devices = get_devices()
    if not devices:
        print("Không tìm thấy thiết bị nào.")
        return []
    
    for stt, id in enumerate(devices, 1):
        print(f"{stt}: {id}")
    
    choice = input("\nChọn các thiết bị (VD: 1,2,3 hoặc 'all' để chọn tất cả): ").strip()
    
    if choice.lower() == 'all':
        return devices
    
    selected_devices = []
    choices = choice.split(',')
    for c in choices:
        c = c.strip()
        if c.isdigit() and 0 < int(c) <= len(devices):
            selected_devices.append(devices[int(c) - 1])
        else:
            print(f"Thiết bị {c} không hợp lệ, bỏ qua.")
    
    if not selected_devices:
        print("Không có thiết bị nào được chọn.")
        return []
    
    return selected_devices

aut_file = "authorization.txt"
if os.path.exists(aut_file):
    with open(aut_file, "r", encoding="utf-8") as f:
        aut = f.read().strip()

    doi = input("  Bạn có muốn đổi authorization không? (y/n): ").strip().lower()
    if doi == "y":
        aut = input(" Nhập authorization mới: ").strip()
        with open(aut_file, "w", encoding="utf-8") as f:
            f.write(aut)
        print(" Đã cập nhật authorization mới!")
else:
    # File chưa tồn tại, yêu cầu nhập mới
    aut = input("Nhập aut: ").strip()
    with open(aut_file, "w", encoding="utf-8") as f:
        f.write(aut)
    print(" Đã lưu aut vào aut.txt")

def get_headers():
    headers = {
        'authorization': f'{aut}',
        'origin': 'https://app.golike.net',
        't': 'VFZSak1FOUVSWGhPVkUxNVRWRTlQUT09',
        "user-agent": UserAgent().random,
    }
    return headers

def dat_nick(user_cau_hinh):
    try:
        dat_nick = session.get('https://gateway.golike.net/api/tiktok-account', headers=get_headers(), impersonate="chrome101").json()

        for user in dat_nick['data']:
            if user['unique_username'] == user_cau_hinh:
                account_id             = user['id']
                return account_id
    except :
        return

def die_job(account_id, account_id_die, ads_id, object_id, job_type):
    json_data = {
        'description'         : 'Tôi không muốn làm Job này',
        'users_advertising_id': account_id,
        'type'                : 'ads',
        'provider'            : 'tiktok',
        'fb_id'               : account_id_die ,
        'error_type'          : 0,
    }
    die_job          = session.post(
        "https://gateway.golike.net/api/report/send",
        headers      = get_headers(),
        impersonate  = "chrome101",
        json         = json_data
    ).json()
    die_json_data = {
        'ads_id'    : ads_id,
        'object_id' : object_id,
        'account_id': account_id_die,
        'type'      : job_type,
    }
    die_job_post    = session.post(
        'https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs',
        headers     = get_headers(),
        impersonate = "chrome101",
        json        = die_json_data
    ).json()

def main(device_id):
    done = fail = tong_xu = 0

    try:
        # kết nối thiết bị
        while True:
            try:
                d = u2.connect(device_id)
                print("Đã kết nối thành công")
                break
            except:
                print("Kết nối thất bại đang kết nối lại")
                continue
        
        # Mở profile và lấy user_cau_hinh
        os.system(f"adb -s {device_id} shell monkey -p com.ss.android.ugc.trill -c android.intent.category.LAUNCHER 1 >nul 2>&1")
        time.sleep(5)

        while True:
            subprocess.run([
                "adb", "-s", f"{device_id}",  "shell", "am", "start",
                "-n", "com.ss.android.ugc.trill/com.ss.android.ugc.aweme.deeplink.DeepLinkActivityV2",
                "-a", "android.intent.action.VIEW",
                "-d", "snssdk1233://user/profile"
            ], check=True)
            time.sleep(5)
            if d(textContains="@").exists:
                d(textContains="@").click()
                user_cau_hinh = d.clipboard
                print("Đã lấy được tên user là ", user_cau_hinh)
                os.system(f"adb -s {device_id} shell input keyevent 4")
                break
            else:
                print("Lấy user thất bại đang tiến hành lấy lại")
                continue

        # Lấy id acc
        account_id = dat_nick(user_cau_hinh)

        # Đặt nick get job
        while True:
                try:
                    job   = []
                    try:
                        get_job = session.get(
                            f'https://gateway.golike.net/api/advertising/publishers/tiktok/jobs?account_id={account_id}&data=null',
                            headers     = get_headers(),
                            impersonate = "chrome101",
                            timeout=10
                        ).json()
                    except Exception as e:
                        print(f"{type(e).__name__[:35 - len(' : Delay 30s')]}: Delay 30s")
                        time.sleep(30)
                        continue 
                    
                    if not get_job['data']:
                        print("Đợi job")
                        time.sleep(15)
                        continue

                    if 'lock' not in get_job or 'ads_id' not in get_job['lock'] or get_job.get('code') == 429:
                        print("Đợi luồng 10s")
                        time.sleep(10)
                        continue

                    # Làm job
                    if get_job['data'] :
                        job.append({
                            'ads_id'    : get_job['lock']['ads_id'],
                            'object_id' : get_job['lock']['object_id'],
                            'account_id': get_job['lock']['account_id'],
                            'type'      : get_job['lock']['type'],
                        })

                        first_job       = job[0]
                        ads_id          = first_job['ads_id']
                        object_id       = first_job['object_id']
                        account_id_die  = first_job['account_id']
                        job_type        = first_job['type']
                        
                        type_job        = get_job['data']['type'][:4] + "..." if len(get_job['data']['type']) > 6 else get_job['data']['type']
                        xu_job          = get_job['data']['price_after_cost']
                        link_job        = get_job['data']['link']
                        id_job          = get_job['data']['id']

                        status = f"Đã get được job {job_type} với {xu_job}đ"
                        xu     = xu_job
                        print(f"{status}")

                        # Bỏ qua 
                        if xu_job <= int(bo_job_be) and type_job == "follow":
                            status = f"Bỏ qua job {bo_job_be}"
                            die_job(account_id, account_id_die, ads_id, object_id, job_type)
                            continue
                        
                        with open("link_job.txt", "w", encoding="utf-8") as f:
                            f.write(link_job)

                        cmd = [
                            "adb", "-s", device_id, "shell", "am", "start",
                            "-a", "android.intent.action.VIEW",
                            "-d", link_job
                        ]
                        
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        # Job follow
                        if job_type == "follow":
                            ten = link_job.split("@")[-1]

                            status = f"Follow {ten}"
                            print(status)

                            time.sleep(random.randint(min_delay_job,max_delay_job))

                            if d(text = "Đây là tài khoản riêng tư").exists:
                                print("Bỏ qua tài khoản riêng tư")
                                die_job (account_id, account_id_die, ads_id, object_id, job_type)
                                subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                continue

                            elif d(text = "Tài khoản đã bị cấm").exists:
                                print("Bỏ qua tài khoản cấm")
                                die_job (account_id, account_id_die, ads_id, object_id, job_type)
                                subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                continue

                            if d(text  = "Follow").exists:
                                d(text  = "Follow").click()

                                time.sleep(1)
                                
                                subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                time.sleep(2)

                                if d(text = "Không cho phép").exists:
                                    d(text = "Không cho phép").click()

                                for _ in range(8):
                                    if d(text = "Trang chủ").exists:
                                        break
                                    else:
                                        os.system(f"adb -s {device_id} shell input keyevent 4")
                                        time.sleep(1)
                                        continue
                                
                            else:
                                die_job         (account_id, account_id_die, ads_id, object_id, job_type)
                                subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                time.sleep(0.1)
                                continue
                        
                        # Job like
                        elif job_type == "like":
                            time.sleep(random.randint(min_delay_job, max_delay_job))
                            like_btn = d(description ="Thích")
                            if like_btn.exists and not like_btn.info.get("selected", False):
                                like_btn.click()
                        
                        # Job bình luận
                        elif job_type == "comment":
                            comment_id      = get_job['lock']['comment_id']
                            message_comment = get_job['lock']['message']
                            
                            status          = f"Nội dung: {message_comment[:15]}... | ID job: {comment_id} "
                            print(status)

                            time.sleep(random.randint(min_delay_job, max_delay_job))

                            moc = d(description="Thích")
                            if not moc.exists:
                                print("Job lỗi")
                                die_job(account_id, account_id_die, ads_id, object_id, job_type)
                                continue

                            button = d(text = "Đề xuất").bounds()
                            y = (button[3]) + 100
                            w, h = d.window_size()
                            x = w // 2

                            bounds  = moc.info['bounds']

                            x_moc   = (bounds['left'] + bounds['right']) // 2
                            y_moc   = (bounds['top'] + bounds['bottom']) // 2
                            height  = bounds['bottom'] - bounds['top']
                            
                            y_click = y_moc + height * 2
                            x_click = x_moc
                            
                            d.click(x_click, y_click)
                            time.sleep(10)
                            # bình luận
                            button = d(text = "Thêm bình luận...")
                            if button.exists:
                                button.click()
                                time.sleep(1)
                                button.send_keys(message_comment)
                                time.sleep(2)
                            else:
                                print("Job lỗi")
                                os.system(f"adb -s {device_id} shell input keyevent 4")
                                die_job(account_id, account_id_die, ads_id, object_id, job_type)
                                continue
                                
                            d.click(x, y)
                            time.sleep(2)

                            # Xử lí gửi bình luận
                            img = None
                            for _ in range(5):
                                os.system(f"adb -s {device_id} shell screencap /sdcard/screen.png >nul 2>&1")
                                os.system(f"adb -s {device_id} pull /sdcard/screen.png >nul 2>&1")
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

                            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

                            lower_red1 = np.array([0, 100, 100])
                            upper_red1 = np.array([10, 255, 255])
                            lower_red2 = np.array([160, 100, 100])
                            upper_red2 = np.array([179, 255, 255])

                            mask1    = cv2.inRange(hsv, lower_red1, upper_red1)
                            mask2    = cv2.inRange(hsv, lower_red2, upper_red2)
                            mask_red = cv2.bitwise_or(mask1, mask2)

                            contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                            for cnt in contours:
                                area = cv2.contourArea(cnt)
                                if area > 1000:  
                                    x,y,w,h      = cv2.boundingRect(cnt)
                                    roi          = img[y:y+h, x:x+w]
                                    gray         = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                                    _, thresh    = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                                    white_pixels = cv2.countNonZero(thresh)

                                    if white_pixels > (w*h)*0.1: 
                                        cx = x + w//2
                                        cy = y + h//2
                                        
                                        os.system(f"adb -s {device_id} shell input tap {cx} {cy}")
                                        time.sleep(2)
                                        #Xóa ảnh để nhẹ máy
                                        if os.path.exists('screen.png'):
                                            os.remove('screen.png')
                                        time.sleep(2)
                                        os.system(f"adb -s {device_id} shell input keyevent 4")
                        # Job share,...              
                        else:
                            print("Bỏ qua job lỗi")
                            die_job         (account_id, account_id_die, ads_id, object_id, job_type)
                            continue
                        
                        print(f"Đã {type_job} thành công")
                        time.sleep(1)
                        d.swipe   (0.5, 0.8, 0.5, 0.2, duration=0.1)
                        time.sleep(random.randint(min_lam_job, max_lam_job))

                        print("Bắt đầu done job lần 1")

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

                        done_job = session.post("https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs", headers=get_headers(), impersonate="chrome101", json=done_job_data).json()
                        
                        if done_job['message'] == "Tài khoản chưa công khai danh sách like vui lòng mở danh sách đã like":
                            status = "Đang đi bật công khai tim"
                            print(status)
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
                            subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(0.5)
                            subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(0.5)
                            subprocess.run(["adb", "-s", device_id, "shell", "input", "keyevent", "4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            status = "Đã bật thành công đang lấy lại job"
                            print(status)
                            continue

                        if not done_job ['success']:
                            print("Đang done job lần 2")
                            done_job_1 = session.post("https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs", headers=get_headers(), impersonate="chrome101", json=done_job_data).json()
                            
                            if not done_job_1 ['success']:
                                die_job(account_id, account_id_die, ads_id, object_id, job_type)
                                fail           += 1
                                print("Job Fail")
                                time.sleep(1)
                            else:
                                done     += 1
                                tong_xu  += xu_job
                                print("Job done")                
                                time.sleep(1)       
                        else:
                            done     += 1
                            tong_xu  += xu_job
                            print("Job done")                
                            time.sleep(1)
        
                    else:
                        print("Đang đi lấy job")
                        time.sleep(10)
                        continue
                except Exception as e:
                    print(e) 
                    continue
    except Exception as e:
        print(e)

if __name__ == '__main__':
    devices = get_device_id()
    print(f"Tìm thấy {len(devices)} thiết bị: {devices}")
    processes = []

    # Start a process for each device
    for device_id in devices:
        p = multiprocessing.Process(target=main, args=(device_id,))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()
