import time
import requests
import os
import random
from rich.console import Console
from rich.prompt import Prompt
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()
TOOL_API_URL = "https://buf-view-tiktok-ayacte.vercel.app/tiktokview"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    console.print("""
[bold cyan]
  _   _ __  __     _____                       
 | | | |  \/  |   |_   _|   _ _   _  ___ _ __  
 | |_| | |\/| |_____| || | | | | | |/ _ \ '_ \ 
 |  _  | |  | |_____| || |_| | |_| |  __/ | | |
 |_| |_|_|  |_|     |_| \__,_|\__, |\___|_| |_|
                              |___/            
[/bold cyan]
""")
    console.print("[bold blue]-" * 70 + "[/bold blue]")
    console.print("[green][+] Suộc Tờ rộm của Hoàng Thanh Tùng[/green]")
    console.print("[green][+] Tool By Minh Tuyên - TuyenNzo[/green]")
    console.print("[green][+] Zalo: 0379956051[/green]")
    console.print("[green][+] Youtube: https://www.youtube.com/@xxxxxxxx[/green]")
    console.print("[bold blue]-" * 70 + "[/bold blue]")

def buff_view_threaded(tiktok_url, num_threads):
    console.print(f"[cyan]=> Đang gửi {num_threads} request cho link:[/] [blue]{tiktok_url}[/]")

    success_count = 0
    error_count = 0
    start_time = time.time()

    def send_request(i):
        nonlocal success_count, error_count
        try:
            response = requests.get(TOOL_API_URL, params={'video': tiktok_url}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('sent_success', 0) > 0:
                    success_count += 1
                    return "[bold green]✓ View đã gửi thành công[/bold green]"
            error_count += 1
            return "[yellow]➜ Gửi request nhưng không rõ kết quả[/yellow]"
        except Exception as e:
            error_count += 1
            return f"[red]✗ Lỗi gửi request:[/] {e}"

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(send_request, i + 1))
            delay = random.uniform(0.05, 0.2)
            time.sleep(delay)

        for idx, future in enumerate(as_completed(futures), 1):
            console.print(future.result())
            if idx % 50 == 0:
                console.print(f"[cyan]=> Đã xử lý {idx}/{num_threads} requests[/]")

    elapsed_time = time.time() - start_time
    console.print(f"\n[bold blue]📊 Kết quả cho link:[/] {tiktok_url}")
    console.print(f"[green]✓ Thành công:[/] {success_count}")
    console.print(f"[red]✗ Lỗi:[/] {error_count}")
    console.print(f"[yellow]⏱️ Thời gian chạy:[/] {elapsed_time:.2f} giây\n")

def load_links():
    links = []
    while True:
        link = input("=> Nhập Link TikTok (Enter để dừng): ")
        if not link.strip():
            break
        if link.startswith("http"):
            links.append(link.strip())
        else:
            console.print("❌ Link không hợp lệ, phải bắt đầu bằng http hoặc https")
    return links

def main():
    clear()
    banner()
    links = load_links()

    if not links:
        console.print("[red]⛔ Không có link nào được nhập.[/red]")
        return

    threads_input = Prompt.ask("=> Nhập số luồng bạn muốn chạy cho mỗi link", default="500")
    try:
        num_threads = int(threads_input)
    except ValueError:
        num_threads = 500

    for i, link in enumerate(links, 1):
        console.print(f"[yellow]=> Đang xử lý link {i}/{len(links)}:[/] {link}")
        buff_view_threaded(link, num_threads)

    console.print("\n[bold cyan]✅ Đã hoàn tất toàn bộ tiến trình.[/bold cyan]")
    time.sleep(2)
    exit()

if __name__ == "__main__":
    main()
