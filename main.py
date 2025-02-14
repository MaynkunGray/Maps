import sys
import requests

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel


class MyPillow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(250, 50, 620, 500)
        self.setWindowTitle('Maps')

        self.l_x, self.l_y = 37.620431, 55.753789
        self.z = 17
        self.server_address_map = 'https://static-maps.yandex.ru/v1?'
        self.api_key_map = 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13'
        self.map_request = f"{self.server_address_map}ll={self.l_x},{self.l_y}&apikey={self.api_key_map}&z={self.z}"

        response = requests.get(self.map_request)
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)

        self.picture = QLabel(self)
        self.picture.resize(620, 500)
        self.picture.move(10, 0)
        self.picture.setPixmap(QPixmap(map_file))

    def show_map(self):
        map_request = f"{self.server_address_map}ll={self.l_x},{self.l_y}&apikey={self.api_key_map}&z={self.z}"

        response = requests.get(map_request)
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)

        self.picture.setPixmap(QPixmap(map_file))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            if self.z < 21:
                self.z += 1
        elif event.key() == Qt.Key.Key_Down:
            if self.z > 1:
                self.z -= 1
        self.show_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('QWidget { background-color: #333333; color: #ffffff; }')
    ex = MyPillow()
    ex.show()
    sys.exit(app.exec())
