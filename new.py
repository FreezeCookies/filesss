import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView

class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Z-Matrix Main")
        self.setGeometry(100, 100, 800, 600)

        # Tạo QTabWidget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Shop
        self.shop_browser = QWebEngineView()
        self.shop_browser.setUrl(QUrl("https://zmatrixtool.x10.mx/shop"))
        self.tabs.addTab(self.shop_browser, "Shop")

        # Tab 2: Get Key Free
        self.key_browser = QWebEngineView()
        self.key_browser.setUrl(QUrl("https://zmatrixtool.x10.mx/getkey"))
        self.tabs.addTab(self.key_browser, "Get Key Free")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebBrowser()
    window.show()
    sys.exit(app.exec_())