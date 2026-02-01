
import tkinter as tk
from tkinter import ttk
import json
import socketio
import threading
import time

# Dữ liệu JSON tĩnh (fallback nếu WebSocket fail)
fallback_data = {
    "status": 200,
    "success": True,
    "current_coin": 13332,
    "facebook": {
        "pending_coin": 1399,
        "hold_coin": 0,
        "time": 1102,
        "lasted": "10-09-2025 20:06:12"
    },
    "cron": {
        "updated_at": "2025-09-10 20:24:34"
    }
}

class FacebookCoinTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Coin Tracker")
        self.root.geometry("400x300")
        self.root.configure(bg="#f0f0f0")

        # Biến lưu dữ liệu
        self.current_data = fallback_data
        self.sio = socketio.Client()

        # Khởi tạo giao diện trước
        self.setup_ui()
        # Thiết lập WebSocket sau khi giao diện đã sẵn sàng
        self.setup_websocket()

    def setup_ui(self):
        """Khởi tạo giao diện"""
        tk.Label(self.root, text="Facebook Coin Tracker", font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#1e90ff").pack(pady=10)
        
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.balance_label = tk.Label(self.main_frame, text=f"Current Balance: {self.current_data['current_coin']} coins", 
                                     font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.balance_label.pack(anchor="w")
        
        self.pending_label = tk.Label(self.main_frame, text=f"Pending Coins: {self.current_data['facebook']['pending_coin']}", 
                                     font=("Arial", 10), bg="#f0f0f0", fg="#32cd32")
        self.pending_label.pack(anchor="w")
        
        self.hold_label = tk.Label(self.main_frame, text=f"Hold Coins: {self.current_data['facebook']['hold_coin']}", 
                                  font=("Arial", 10), bg="#f0f0f0", fg="#ff4500")
        self.hold_label.pack(anchor="w")
        
        self.last_activity_label = tk.Label(self.main_frame, text=f"Last Activity: {self.current_data['facebook']['lasted']}", 
                                          font=("Arial", 10), bg="#f0f0f0")
        self.last_activity_label.pack(anchor="w")
        
        self.time_label = tk.Label(self.main_frame, text=f"Time: {self.current_data['facebook']['time']}", 
                                  font=("Arial", 10), bg="#f0f0f0")
        self.time_label.pack(anchor="w")
        
        self.updated_label = tk.Label(self.main_frame, text=f"Last Updated: {self.current_data['cron']['updated_at']}", 
                                     font=("Arial", 10), bg="#f0f0f0")
        self.updated_label.pack(anchor="w")
        
        self.status_label = tk.Label(self.main_frame, text="Status: Initializing...", 
                                    font=("Arial", 9), bg="#f0f0f0", fg="#ffa500")
        self.status_label.pack(anchor="w", pady=5)

        # Nút refresh thủ công
        tk.Button(self.main_frame, text="Refresh Data", command=self.update_data, bg="#1e90ff", fg="white", font=("Arial", 10)).pack(pady=10)

    def setup_websocket(self):
        """Thiết lập kết nối WebSocket"""
        @self.sio.event
        def connect():
            self.status_label.config(text="Status: WebSocket Connected!", fg="green")
            print("WebSocket connected")

        @self.sio.event
        def disconnect():
            self.status_label.config(text="Status: WebSocket Disconnected, using fallback", fg="red")
            print("WebSocket disconnected")

        @self.sio.event
        def message(data):
            """Xử lý dữ liệu từ WebSocket"""
            try:
                self.current_data = json.loads(data) if isinstance(data, str) else data
                self.update_display()
                self.status_label.config(text="Status: Updated from WebSocket!", fg="green")
            except Exception as e:
                print(f"WebSocket data error: {e}")
                self.status_label.config(text=f"Status: WebSocket Data Error ({str(e)[:30]}...)", fg="red")

        def connect_with_retry():
            retries = 0
            max_retries = 5
            while retries < max_retries:
                try:
                    self.sio.connect(
                        "wss://ws.golike.net/socket.io/?EIO=3&transport=websocket",
                        headers={
                            # Thay YOUR_TOKEN_HERE bằng token thật
                            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9nYXRld2F5LmdvbGlrZS5uZXRcL2FwaVwvbG9naW4iLCJpYXQiOjE3NTczNDU0MTMsImV4cCI6MTc4ODg4MTQxMywibmJmIjoxNzU3MzQ1NDEzLCJqdGkiOiIzMDFvamVqeERyaW9VbXhmIiwic3ViIjozMDQ3MTczLCJwcnYiOiJiOTEyNzk5NzhmMTFhYTdiYzU2NzA0ODdmZmYwMWUyMjgyNTNmZTQ4In0.8fOzuv5mMR4dEf_5y_9pcV11lI-r60GJuCxCyMVEj-g",
                            "Cookie": "cf_clearance=E6wyD_EuATVopz1qQoiwns00VvGyFUtq49mlxhjTqSc-1757509624-1.2.1.1-006RN.ZFhnyiOZwkNtyMy_HyC2J.7tw9avwTd5NZd1uxG.vllv307CEAuS23Q7r3nv..acx0rX1qlAszRO0kjufWTi_PjlLfg6R4pvQ0reEFxEfiIzHRdNyeaBJhoOuqox3Ba_vPagsekaPcdMQaUsBzpJwJc9KsBiga2agXuXEc3qFaYQ4AA_VyduZEo.Y7i51tDQYcQQtPbV7.yBxUQDkEQfmu47p5yBKZcERhlJc",
                        },
                        wait_timeout=10
                    )
                    break
                except Exception as e:
                    retries += 1
                    print(f"WebSocket connection error (attempt {retries}/{max_retries}): {e}")
                    self.status_label.config(text=f"Status: WebSocket Error ({str(e)[:30]}...), retrying", fg="red")
                    if retries == max_retries:
                        self.status_label.config(text="Status: WebSocket Failed, using fallback", fg="red")
                        break
                    time.sleep(5)  # Chờ 5 giây trước khi thử lại

        # Chạy kết nối trong thread riêng
        threading.Thread(target=connect_with_retry, daemon=True).start()

    def update_data(self):
        """Cập nhật dữ liệu (giả lập hoặc từ WebSocket)"""
        # Nếu WebSocket không kết nối, có thể thêm logic gọi API tại đây
        self.update_display()

    def update_display(self):
        """Cập nhật giao diện"""
        fb = self.current_data.get('facebook', {})
        self.balance_label.config(text=f"Current Balance: {self.current_data.get('current_coin', 0)} coins")
        self.pending_label.config(text=f"Pending Coins: {fb.get('pending_coin', 0)}")
        self.hold_label.config(text=f"Hold Coins: {fb.get('hold_coin', 0)}")
        self.last_activity_label.config(text=f"Last Activity: {fb.get('lasted', 'N/A')}")
        self.time_label.config(text=f"Time: {fb.get('time', 0)}")
        self.updated_label.config(text=f"Last Updated: {self.current_data['cron'].get('updated_at', 'N/A')}")

    def on_closing(self):
        """Xử lý khi đóng cửa sổ"""
        self.sio.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookCoinTracker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
