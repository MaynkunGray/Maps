import os
import math
import sys
import requests
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QCheckBox, QLineEdit, QPushButton


width = 600
height = 450
tile_size = 256
for_finding_z = [(0.0004023313522338867, 0.00016980905591168494), (0.0008046627044677734, 0.00033961811182336987),
                 (0.0016093254089355469, 0.0006792362236325289), (0.0032186508178710938, 0.001358472447300585),
                 (0.0064373016357421875, 0.0027169448948285435), (0.012874603271484375, 0.005433889791419233),
                 (0.02574920654296875, 0.010867779596985372), (0.0514984130859375, 0.02173555930714599),
                 (0.102996826171875, 0.04347111951959448), (0.20599365234375, 0.08694224628165159),
                 (0.4119873046875, 0.17388455050288343), (0.823974609375, 0.3477695645174208),
                 (1.64794921875, 0.6955428369666947), (3.2958984375, 1.3911153322228529),
                 (6.591796875, 2.7824677654778824), (13.18359375, 5.566827051651323),
                 (26.3671875, 11.148617264642724), (52.734375, 22.411559410911394),
                 (105.46875, 45.570219490338815), (210.9375, 92.70401327222598),
                 (421.87499999999994, 154.5763237708369), (843.75, 178.37247810249727)]


def find_lon_lat(pixel_x, pixel_y, center_lon, center_lat, z):
    radians_lat = math.radians(center_lat)
    k_tiles = 2 ** z
    center_tile_x = (center_lon + 180) / 360 * k_tiles
    center_tile_y = (1 - math.asinh(math.tan(radians_lat)) / math.pi) / 2 * k_tiles

    pixel_move_x = pixel_x - width / 2
    pixel_move_y = pixel_y - height / 2

    tile_move_x = pixel_move_x / tile_size
    tile_move_y = pixel_move_y / tile_size

    target_tile_x = (center_tile_x + tile_move_x) % k_tiles
    target_tile_y = (center_tile_y + tile_move_y) % k_tiles

    lon = target_tile_x / k_tiles * 360 - 180
    radians_lat = math.atan(math.sinh(math.pi * (1 - 2 * target_tile_y / k_tiles)))
    lat = math.degrees(radians_lat)

    return [lon, lat]


def find_scale(l_corner, u_corner):
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


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b

    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    distance = math.sqrt(dx * dx + dy * dy)

    return distance


class BigMaps(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(500, 100, 620, 630)
        self.setWindowTitle('Maps')

        self.theme = QCheckBox(self)
        self.theme.setText('Темная тема')
        self.theme.move(10, 460)
        self.theme.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.mail_index = QCheckBox(self)
        self.mail_index.setText('Почтовый индекс')
        self.mail_index.resize(140, 30)
        self.mail_index.move(140, 460)
        self.mail_index.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.index = ''

        self.search_data = QLineEdit(self)
        self.search_data.resize(305, 20)
        self.search_data.move(10, 500)
        self.search_data.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.search_button = QPushButton(self)
        self.search_button.setText('Искать')
        self.search_button.resize(75, 20)
        self.search_button.move(325, 500)
        self.search_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.clear_button = QPushButton(self)
        self.clear_button.setText('Сброс поискового результата')
        self.clear_button.resize(200, 20)
        self.clear_button.move(410, 500)
        self.clear_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.adress = QLabel(self)
        self.adress.setText('Адресс: ')
        self.adress.setWordWrap(True)
        self.adress.resize(600, 40)
        self.adress.move(10, 530)

        self.organization = QLabel(self)
        self.organization.setText('Организация: ')
        self.organization.setWordWrap(True)
        self.organization.resize(600, 40)
        self.organization.move(10, 580)

        self.lon, self.latt = 37.620431, 55.753789
        self.z = 17
        self.pt = ''
        down_left = find_lon_lat(0, 450, self.lon, self.latt, self.z)
        up_right = find_lon_lat(600, 0, self.lon, self.latt, self.z)
        self.lon_move, self.latt_move = [abs(i / 3) for i in find_scale(down_left, up_right)]
        self.map_api_server = 'https://static-maps.yandex.ru/v1?'
        self.geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        self.search_api_server = "https://search-maps.yandex.ru/v1/"
        self.map_file = "map.png"

        self.picture = QLabel(self)
        self.picture.resize(600, 450)
        self.picture.move(10, 5)

        self.show_map()

        self.theme.clicked.connect(self.show_map)
        self.mail_index.clicked.connect(self.edit_adress)
        self.search_button.clicked.connect(self.search)
        self.search_data.returnPressed.connect(self.search)
        self.clear_button.clicked.connect(self.clear_search_data)

    def show_map(self):
        map_params = {
            "ll": f'{self.lon},{self.latt}',
            "z": f'{self.z}',
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
        self.organization.setText('Организация: ')

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
            self.pt = f'{self.lon},{self.latt}'
            l_c = [float(i) for i in toponym['boundedBy']['Envelope']['lowerCorner'].split()]
            u_c = [float(i) for i in toponym['boundedBy']['Envelope']['upperCorner'].split()]
            lon_width, lat_width = find_scale(l_c, u_c)
            for i in range(len(for_finding_z)):
                if for_finding_z[i][0] >= lon_width and for_finding_z[i][1] >= lat_width:
                    self.z = 21 - i
                    break
            down_left = find_lon_lat(0, 450, self.lon, self.latt, self.z)
            up_right = find_lon_lat(600, 0, self.lon, self.latt, self.z)
            self.lon_move, self.latt_move = [abs(i / 3) for i in find_scale(down_left, up_right)]
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
        self.organization.setText('Организация: ')
        self.pt = ''
        self.index = ''
        self.show_map()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_PageUp:
            if self.z > 0:
                self.z -= 1
            down_left = find_lon_lat(0, 450, self.lon, self.latt, self.z)
            up_right = find_lon_lat(600, 0, self.lon, self.latt, self.z)
            self.lon_move, self.latt_move = [abs(i / 3) for i in find_scale(down_left, up_right)]
            self.show_map()
        elif event.key() == Qt.Key.Key_PageDown:
            if self.z < 21:
                self.z += 1
            down_left = find_lon_lat(0, 450, self.lon, self.latt, self.z)
            up_right = find_lon_lat(600, 0, self.lon, self.latt, self.z)
            self.lon_move, self.latt_move = [abs(i / 3) for i in find_scale(down_left, up_right)]
            self.show_map()
        elif event.key() == Qt.Key.Key_Left:
            self.lon -= self.lon_move
            if self.lon < -180:
                self.lon += 360
            self.show_map()
        elif event.key() == Qt.Key.Key_Right:
            self.lon += self.lon_move
            if self.lon > 180:
                self.lon -= 360
            self.show_map()
        elif event.key() == Qt.Key.Key_Up:
            if self.latt + self.latt_move <= 84:
                self.latt += self.latt_move
            self.show_map()
        elif event.key() == Qt.Key.Key_Down:
            if self.latt - self.latt_move >= -84:
                self.latt -= self.latt_move
            self.show_map()

    def mousePressEvent(self, event):
        self.search_data.clearFocus()
        button = event.button()
        if button in [Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton]:
            x = event.pos().x() - 10
            y = event.pos().y() - 5
            if 0 <= x <= 600 and 0 <= y <= 450:
                lon, lat = find_lon_lat(x, y, self.lon, self.latt, self.z)
                self.pt = f'{lon},{lat}'
                if button == Qt.MouseButton.LeftButton:
                    self.find_place()
                else:
                    self.find_organization()

    def find_place(self):
        self.organization.setText('Организация: ')

        toponym_to_find = self.pt

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
            if self.mail_index.isChecked() and self.index:
                self.adress.setText(f'Адресс: {adress}{self.index}')
            else:
                self.adress.setText(f'Адресс: {adress}')
            self.show_map()
        else:
            self.clear_search_data()

        self.search_data.clearFocus()

    def find_organization(self):
        toponym_to_find = self.pt
        self.index = ''

        geocoder_params = {
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "geocode": toponym_to_find,
            "format": "json"}

        response = requests.get(self.geocoder_api_server, params=geocoder_params)

        if response and response.json()["response"]["GeoObjectCollection"]["featureMember"]:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            adress = toponym['metaDataProperty']['GeocoderMetaData']['text']
            search_params = {
                "apikey": "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3",
                "text": adress,
                "lang": "ru_RU",
                "type": "biz"
            }

            response = requests.get(self.search_api_server, params=search_params)
            if response:
                json_response = response.json()
                searching_coord = [float(i) for i in self.pt.split(',')]
                hl = []
                for i in json_response['features']:
                    curr_coords = i['geometry']['coordinates']
                    if lonlat_distance(searching_coord, curr_coords) <= 50:
                        hl.append((','.join([str(i) for i in curr_coords]),
                                   f'Адресс: {i["properties"]["CompanyMetaData"]["address"]}',
                                   f'Организация: {i["properties"]["CompanyMetaData"]["name"]}',
                                   lonlat_distance(searching_coord, curr_coords)))
                if hl:
                    hl.sort(key=lambda x: x[-1])
                    self.pt = hl[0][0]
                    self.adress.setText(hl[0][1])
                    self.organization.setText(hl[0][2])
                    self.show_map()
                else:
                    self.clear_search_data()
            else:
                self.clear_search_data()

        self.search_data.clearFocus()

    def closeEvent(self, event):
        os.remove(self.map_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('QWidget { background-color: #333333; color: #ffffff; }')
    ex = BigMaps()
    ex.show()
    sys.exit(app.exec())
