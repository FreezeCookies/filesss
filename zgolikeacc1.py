from curl_cffi import requests
import json, time, threading
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, TextColumn
import uuid

# Khởi tạo console rich và thời gian bắt đầu
console = Console()
start_time = time.time()  # Thời điểm mở tool

# Headers (cập nhật token nếu cần)
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6',
    'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9nYXRld2F5LmdvbGlrZS5uZXRcL2FwaVwvbG9naW4iLCJpYXQiOjE3NTY1MzM1NTcsImV4cCI6MTc4ODA2OTU1NywibmJmIjoxNzU2NTMzNTU3LCJqdGkiOiJmSDgzRUc3OTNsczNuODAxIiwic3ViIjozMDczNzUwLCJwcnYiOiJiOTEyNzk5NzhmMTFhYTdiYzU2NzA0ODdmZmYwMWUyMjgyNTNmZTQ4In0.puelkDEHPfebrfUunjkWYrwU-BkW3xrPTxDLAHf2Bew',
    'content-type': 'application/json;charset=utf-8',   
    'origin': 'https://app.golike.net',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    't': 'VFZSak1VMVVSVE5QUkZrd1RsRTlQUT09',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
}

account_ids = ['45245', '45244', '45243', '45242', '45241']

# Biến toàn cục
tong_xu_all = 0
lock = threading.Lock()
job_stats = {acc_id: {'count': 0, 'total_coins': 0, 'last_status': 'Đang chờ', 'last_update': time.strftime("%H:%M:%S"), 'thread_active': False, 'start_time': time.time()} for acc_id in account_ids}
log_lines = []  # Lưu trữ các dòng log
run_24_7 = False  # Chế độ treo 24/24

# Hàm tính thời gian chạy
def format_duration(seconds):
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

# Tạo panel cho từng tài khoản
def create_account_panel(acc_id):
    stats = job_stats[acc_id]
    thread_status = "[green]●[/green]" if stats['thread_active'] else "[red]■[/red]"
    content = (
        f"[cyan]ID: {acc_id}[/cyan]\n"
        f"[green]Jobs: {stats['count']}[/green]\n"
        f"[yellow]Xu: {stats['total_coins']}[/yellow]\n"
        f"[magenta]{stats['last_status']}[/magenta]\n"
        f"[white]{stats['last_update']}[/white]\n"
        f"[white]Luồng: {thread_status}[/white]"
    )
    panel_width = min(console.width // 3, 28) if console.width >= 80 else console.width
    return Panel(content, title=f"TK {acc_id}", border_style="blue", padding=(0, 1), width=panel_width, height=8)

# Tạo panel tổng quan
def create_summary_panel():
    elapsed_time = format_duration(time.time() - start_time)
    mode = "24/24" if run_24_7 else "Bình thường"
    content = (
        f"[yellow]Tổng Xu: {tong_xu_all}[/yellow]\n"
        f"[white]Thời gian: {time.strftime('%H:%M:%S')}[/white]\n"
        f"[cyan]Đã chạy: {elapsed_time}[/cyan]\n"
        f"[cyan]Chế độ: {mode}[/cyan]"
    )
    panel_width = min(console.width // 3, 28) if console.width >= 80 else console.width
    return Panel(content, title="Tổng Quan", border_style="cyan", padding=(0, 1), width=panel_width, height=8)

# Tạo panel log
def create_log_panel():
    log_limit = 5 if console.width < 80 else 10  # Giảm số dòng trên màn hình nhỏ
    log_content = "\n".join(log_lines[-log_limit:])
    return Panel(log_content or "[white]Nhật ký...[/white]", title="Log", border_style="green", height=log_limit + 2)

# Tạo layout động
def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1)
    )
    layout["header"].update(Panel("[bold cyan]Tự Động Hóa GoLike[/bold cyan]", border_style="cyan"))

    if console.width >= 80:
        # Bố cục lưới 2x3 cho terminal rộng
        layout["main"].split_column(
            Layout(name="grid", ratio=1),
            Layout(name="log", ratio=1)
        )
        layout["grid"].split_column(
            Layout(name="row1"),
            Layout(name="row2")
        )
        layout["row1"].split_row(
            Layout(create_account_panel(account_ids[0]), name="acc1"),
            Layout(create_account_panel(account_ids[1]), name="acc2"),
            Layout(create_account_panel(account_ids[2]), name="acc3")
        )
        layout["row2"].split_row(
            Layout(create_account_panel(account_ids[3]), name="acc4"),
            Layout(create_account_panel(account_ids[4]), name="acc5"),
            Layout(create_summary_panel(), name="summary")
        )
        layout["log"].update(create_log_panel())
    else:
        # Bố cục dọc cho terminal hẹp (điện thoại)
        layout["main"].split_column(
            *[Layout(create_account_panel(acc_id), name=f"acc{acc_id}") for acc_id in account_ids],
            Layout(create_summary_panel(), name="summary"),
            Layout(create_log_panel(), name="log")
        )
    return layout

# Thêm dòng log
def add_log(line):
    with lock:
        log_lines.append(line)
        log_limit = 5 if console.width < 80 else 10
        if len(log_lines) > log_limit:
            log_lines.pop(0)

# Cập nhật trạng thái
def update_status(account_id, status, count, total_coins, thread_active):
    with lock:
        job_stats[account_id]['last_status'] = status
        job_stats[account_id]['count'] = count
        job_stats[account_id]['total_coins'] = total_coins
        job_stats[account_id]['last_update'] = time.strftime("%H:%M:%S")
        job_stats[account_id]['thread_active'] = thread_active

# Kiểm tra xem tất cả tài khoản có dừng không
def all_accounts_stopped():
    with lock:
        return all(not stats['thread_active'] for stats in job_stats.values())

def job(account_id):
    global tong_xu_all
    stt = tong = 0

    # Đánh dấu luồng đang hoạt động
    update_status(account_id, "Khởi động", stt, tong, True)
    add_log(f"[cyan][{account_id}] Luồng khởi động...[/cyan]")
    
    while True:
        try:
            # Kiểm tra chế độ 24/24 và reset job sau 24 giờ
            if run_24_7 and (time.time() - job_stats[account_id]['start_time']) >= 86400:
                stt = 0
                job_stats[account_id]['start_time'] = time.time()
                update_status(account_id, "Reset 24h", stt, tong, True)
                add_log(f"[cyan][{account_id}] Reset job sau 24 giờ, tiếp tục chạy.[/cyan]")

            # Kiểm tra nếu đạt 100 job (không áp dụng cho chế độ 24/24)
            if not run_24_7 and stt >= 100:
                update_status(account_id, "Đủ 100 Job", stt, tong, False)
                add_log(f"[blue][{account_id}] Đã hoàn thành 100 job, dừng lại.[/blue]")
                break

            # Cập nhật trạng thái lấy công việc
            update_status(account_id, "Lấy Job", stt, tong, True)
            
            # Lấy công việc
            params = {'account_id': account_id}
            get_job = requests.get(
                'https://gateway.golike.net/api/advertising/publishers/threads/jobs',
                params=params, headers=headers, impersonate="chrome101"
            ).json()

            # Nếu không có công việc, chờ và cập nhật trạng thái
            if "lock" not in get_job:
                update_status(account_id, "Không Có Job", stt, tong, True)
                add_log(f"[yellow][{account_id}] Không có job, chờ...[/yellow]")
                time.sleep(20)
                continue

            # Chuẩn bị dữ liệu hoàn thành công việc
            json_data = {
                'account_id': get_job['lock']['account_id'],
                'ads_id': get_job['lock']['ads_id'],
            }

            # Hoàn thành công việc
            response = requests.post(
                'https://gateway.golike.net/api/advertising/publishers/threads/complete-jobs',
                headers=headers,
                json=json_data,
                impersonate="chrome101",
            ).json()

            # Nếu công việc không thành công, bỏ qua
            if not response.get("success", False):
                json_data = {
                    'account_id': get_job['lock']['account_id'],
                    'ads_id': get_job['lock']['ads_id'],
                    'object_id': get_job['lock']['object_id'],
                }
                skip = requests.post(
                    'https://gateway.golike.net/api/advertising/publishers/threads/skip-jobs',
                    headers=headers,
                    json=json_data,
                    impersonate="chrome101",
                ).json()
                update_status(account_id, "Bỏ Qua Job", stt, tong, True)
                add_log(f"[red][{account_id}] Bỏ qua job: {skip['message'][:15]}...[/red]")
                continue

            # Cập nhật thống kê
            stt += 1
            tong += response['data']['prices']
            
            with lock:
                tong_xu_all += response['data']['prices']
            
            update_status(account_id, "Hoàn Thành", stt, tong, True)
            add_log(
                f"[green][{account_id}] {stt} | {response['data']['uid']} | "
                f"{response['data']['type'].lower()} | {response['data']['prices']} | "
                f"Tổng TK: {tong} | Tổng: {tong_xu_all}[/green]"
            )

            time.sleep(60)  # Chờ 1 phút
        except Exception as e:
            update_status(account_id, f"Lỗi", stt, tong, False)
            add_log(f"[red][{account_id}] Lỗi: {str(e)[:15]}... Dừng lại.[/red]")
            break
        finally:
            # Đảm bảo trạng thái luồng được cập nhật
            update_status(account_id, job_stats[account_id]['last_status'], stt, tong, job_stats[account_id]['thread_active'])

# Hàm chính với layout cập nhật trực tiếp
def main():
    global run_24_7
    console.print(Panel("[bold cyan]Bắt Đầu Tự Động Hóa GoLike[/bold cyan]", border_style="cyan"))
    
    # Hỏi người dùng về chế độ treo 24/24
    response = input("Bạn có muốn treo 24/24 không? (y/n): ").strip().lower()
    run_24_7 = response == 'y'
    
    # Khởi động luồng cho mỗi tài khoản
    threads = []
    for acc_id in account_ids:
        t = threading.Thread(target=job, args=(acc_id,), daemon=True)
        t.start()
        threads.append(t)

    # Cập nhật layout trực tiếp
    with Live(create_layout(), refresh_per_second=1, console=console) as live:
        try:
            while True:
                live.update(create_layout())
                if not run_24_7 and all_accounts_stopped():
                    console.print(Panel("[yellow]Tất cả tài khoản đã dừng. Thoát tool.[/yellow]", border_style="yellow"))
                    live.update(create_layout())
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            for acc_id in account_ids:
                update_status(acc_id, job_stats[acc_id]['last_status'], job_stats[acc_id]['count'], job_stats[acc_id]['total_coins'], False)
            console.print(Panel("[yellow]Đã dừng chương trình. Trạng thái cuối:[/yellow]", border_style="yellow"))
            console.print(create_layout())

if __name__ == "__main__":
    main()