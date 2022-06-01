from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.uix.modalview import ModalView
import requests
import json
from functools import partial
from datetime import datetime
from requests_futures import sessions
from bs4 import BeautifulSoup
from kivy.config import Config
import threading
from kivy.clock import Clock


Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '320')


class Windows(BoxLayout):
    label = main_label = ObjectProperty()
    progress = ObjectProperty()

    def send(self, msg, dt):
        self.label.text += msg

    def smallWin(self):
        view = ModalView(size_hint=(None, None), size=(250, 100))
        view.open()

    def block_btn(self, dt):
        self.ids.updatebutton.disabled = False

    def prBar(self, value, all, dt):
        self.progress.value = (value/all) * 100

    def upd_data(self):
        threading.Thread(target=self.load).start()

    def load(self, *args) -> bool:
        """ Парсинг инфы о танках с оф. сайта """
        msg = f'== СТАРТ загрузки данных\n'
        # self.send(msg, dt=0)
        Clock.schedule_once(partial(self.send, msg))
        self.ids.updatebutton.disabled = True
        count_time = datetime.now()
        URL = []
        encyclopedia = {"status": "ok", "meta": {"count": 0}, "data": {}}

        var = requests.get('https://console.worldoftanks.com/ru/encyclopedia/vehicles/')
        soup = BeautifulSoup(var.text, 'html.parser')
        id = 0
        msg = f"== ПОИСК ссылок на танки\n"
        Clock.schedule_once(partial(self.send, msg))
        for link in soup.find_all('a', href=True):
            if '/ru/encyclopedia/vehicles/' in link['href']:
                if '?' not in link['href']:
                    if len(link['href'].split('/')) == 6:
                        id = id + 1
                        URL.append(f"https://console.worldoftanks.com{link['href']}")
                        msg += f"#{id} - https://console.worldoftanks.com{link['href']}\n"

        msg = f"== ПАРСИНГ данных с Танкопедии\n"
        Clock.schedule_once(partial(self.send, msg))
        num = 0
        for i in URL:
            link = sessions.FuturesSession()
            site = link.get(i)

            var = site.result().text[site.result().text.find('var json_data'):].split('var ')
            json_data = var[1].strip()[12:-1].replace('{Passive}', '')

            data = json.loads(json_data)
            id = data['vehicle']['info']['id']
            type = data['vehicle']['info']['type_slug']
            name = data['vehicle']['info']['user_string']
            if data['vehicle']['info']['level'] is not None:
                tier = data['vehicle']['info']['level']
                era = ""
            else:
                tier = 0
                era = data['vehicle']['info']['era']
            tag = str(data['vehicle']['info']['url']).split('/')[-2]

            ex_data = {"name": name, "short_name": name, "tag": tag, "era": era, "tier": tier, "type": type}
            encyclopedia['data'][str(id)] = ex_data
            num = num + 1
            msg = f"Танк: {name}\n"
            Clock.schedule_once(partial(self.send, msg))
            self.progress.value = (num/len(URL)) * 100

        # TODO: Для парсинга данных в JSON файл
        # encyclopedia['meta']['count'] = len(URL)
        # with open('data.json', 'w') as f:
        #     json.dump(encyclopedia, f)

        msg = f"Танков: {len(URL)}, время: {str(datetime.now() - count_time)}"
        Clock.schedule_once(partial(self.send, msg))
        Clock.schedule_once(partial(self.block_btn))
        return True
    pass


class MainApp(App):
    def build(self):
        return Windows()


if __name__ == "__main__":
    MainApp().run()
