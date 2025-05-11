import os
import sys
import requests

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QCheckBox, QLineEdit, QPushButton


def find_scale(json_res):
    geoobj_toponym = json_res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    l_corner = [float(i) for i in geoobj_toponym['boundedBy']['Envelope']['lowerCorner'].split()]
    u_corner = [float(i) for i in geoobj_toponym['boundedBy']['Envelope']['upperCorner'].split()]
    if l_corner[0] > 180:
        l_corner[0] -= 360
    elif l_corner[0] < -180:
        l_corner[0] += 360
    elif l_corner[0] == 180:
        l_corner[0] = 179.9999999
    if u_corner[0] > 180:
        u_corner[0] -= 360
    elif u_corner[0] < -180:
        u_corner[0] += 360
    elif u_corner[0] == 180:
        u_corner[0] = 179.9999999
    if l_corner[0] > u_corner[0]:
        return 360 - l_corner[0] + u_corner[0], u_corner[1] - l_corner[1]
    else:
        return u_corner[0] - l_corner[0], u_corner[1] - l_corner[1]


class BigMaps(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(500, 100, 620, 580)
        self.setWindowTitle('Maps')

        self.theme = QCheckBox(self)
        self.theme.setText('Темная тема')
        self.theme.move(10, 460)

        self.mail_index = QCheckBox(self)
        self.mail_index.setText('Почтовый индекс')
        self.mail_index.resize(140, 30)
        self.mail_index.move(140, 460)

        self.index = ''

        self.search_data = QLineEdit(self)
        self.search_data.resize(305, 20)
        self.search_data.move(10, 500)
        self.search_data.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.search_button = QPushButton(self)
        self.search_button.setText('Искать')
        self.search_button.resize(75, 20)
        self.search_button.move(325, 500)

        self.clear_button = QPushButton(self)
        self.clear_button.setText('Сброс поискового результата')
        self.clear_button.resize(200, 20)
        self.clear_button.move(410, 500)

        self.adress = QLabel(self)
        self.adress.setText('Адресс: ')
        self.adress.setWordWrap(True)
        self.adress.resize(600, 40)
        self.adress.move(10, 530)

        self.lon, self.latt = 37.620431, 55.753789
        self.spn = [0.0014, 0.0014]
        self.pt = ''
        self.map_api_server = 'https://static-maps.yandex.ru/v1?'
        self.geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        self.map_file = "map.png"

        self.picture = QLabel(self)
        self.picture.resize(620, 460)
        self.picture.move(10, 0)

        self.show_map()

        self.theme.clicked.connect(self.show_map)
        self.mail_index.clicked.connect(self.edit_adress)
        self.search_button.clicked.connect(self.search)
        self.search_data.returnPressed.connect(self.search)
        self.clear_button.clicked.connect(self.clear_search_data)

    def show_map(self):
        map_params = {
            "ll": f'{self.lon},{self.latt}',
            "spn": f'{self.spn[0]},{self.spn[1]}',
            "apikey": "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13",
            'theme': 'dark' if self.theme.isChecked() else 'light',
            'pt': self.pt
        }

        response = requests.get(self.map_api_server, params=map_params)
        with open(self.map_file, "wb") as file:
            file.write(response.content)

        self.picture.setPixmap(QPixmap(self.map_file))

    def edit_adress(self):
        if self.mail_index.isChecked():
            if self.index:
                self.adress.setText(f'{self.adress.text()}{self.index}')
        elif self.index:
            self.adress.setText(','.join(self.adress.text().split(',')[:-1]))

    def search(self):
        toponym_to_find = self.search_data.text()

        geocoder_params = {
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "geocode": toponym_to_find,
            "format": "json"}

        response = requests.get(self.geocoder_api_server, params=geocoder_params)

        if response and response.json()["response"]["GeoObjectCollection"]["featureMember"]:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            adress = toponym['metaDataProperty']['GeocoderMetaData']['text']
            try:
                self.index = ', ' + toponym['metaDataProperty']['GeocoderMetaData']['AddressDetails']['Country'][
                    'AdministrativeArea']['Locality']['Thoroughfare']['Premise']['PostalCode']['PostalCodeNumber']
            except Exception:
                self.index = ''
            toponym_coodrinates = toponym["Point"]["pos"]
            toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
            self.lon = float(toponym_longitude)
            self.latt = float(toponym_lattitude)

            self.spn = list(find_scale(json_response))
            self.pt = f'{self.lon},{self.latt}'
            if self.mail_index.isChecked() and self.index:
                self.adress.setText(f'Адресс: {adress}{self.index}')
            else:
                self.adress.setText(f'Адресс: {adress}')
            self.show_map()
        else:
            self.clear_search_data()

        self.search_data.clearFocus()

    def clear_search_data(self):
        self.search_data.clear()
        self.search_data.clearFocus()
        self.adress.setText('Адресс: ')
        self.pt = ''
        self.index = ''
        self.show_map()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_PageUp:
            if self.spn[0] * 2 <= 45:
                self.spn[0] *= 2
                self.spn[1] *= 2
            self.show_map()
        elif event.key() == Qt.Key.Key_PageDown:
            if self.spn[0] / 2 >= 0.0007 and self.spn[1] / 2 >= 0.0007:
                self.spn[0] /= 2
                self.spn[1] /= 2
            else:
                self.spn[0] = 0.0007
                self.spn[1] = 0.0007
            self.show_map()
        elif event.key() == Qt.Key.Key_Left:
            self.lon -= self.spn[0] / 2
            if self.lon < -180:
                self.lon += 360
            self.show_map()
        elif event.key() == Qt.Key.Key_Right:
            self.lon += self.spn[0] / 2
            if self.lon > 180:
                self.lon -= 360
            self.show_map()
        elif event.key() == Qt.Key.Key_Up:
            if self.latt + self.spn[1] / 2 <= 84:
                self.latt += self.spn[1] / 2
            self.show_map()
        elif event.key() == Qt.Key.Key_Down:
            if self.latt - self.spn[1] / 2 >= -84:
                self.latt -= self.spn[1] / 2
            self.show_map()

    def mousePressEvent(self, event):
        self.search_data.clearFocus()

    def closeEvent(self, event):
        os.remove(self.map_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('QWidget { background-color: #333333; color: #ffffff; }')
    ex = BigMaps()
    ex.show()
    sys.exit(app.exec())
