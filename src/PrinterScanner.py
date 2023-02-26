import logging
import re
from html.parser import HTMLParser

import requests
from homie_helpers import Homie, Node, IntProperty, State


class PrinterScanner:
    def __init__(self, config, mqtt_settings):
        device_id = config['id']
        self.url = config['url']

        self.homie = Homie(mqtt_settings, device_id, "HP PhotoSmart B209a-m", nodes=[
            Node("status", properties=[
                IntProperty("pages", name="Printed pages"),
                IntProperty("ink-cyan", unit="%", min_value=0, max_value=100),
                IntProperty("ink-magenta", unit="%", min_value=0, max_value=100),
                IntProperty("ink-yellow", unit="%", min_value=0, max_value=100),
                IntProperty("ink-black", unit="%", min_value=0, max_value=100),
            ])
        ])

    def refresh(self):
        try:
            response = get_printer_info(self.url)
            self.homie['ink-cyan'] = int(response.c)
            self.homie['ink-magenta'] = int(response.m)
            self.homie['ink-yellow'] = int(response.y)
            self.homie['ink-black'] = int(response.k)
            self.homie['pages'] = int(response.pages)
            self.homie.state = State.READY
        except Exception as e:
            logging.getLogger('HPPrinterScanner').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT


class PrinterInfo:
    def __init__(self, c, m, y, k, pages):
        self.c = c
        self.m = m
        self.y = y
        self.k = k
        self.pages = pages


def get_printer_info(printer_address):
    response = requests.get('http://%s/index.htm?cat=info&page=printerInfo' % printer_address)
    response.raise_for_status()
    result = response.text

    class InkInfoParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.black = None
            self.cyan = None
            self.yellow = None
            self.magenta = None

        def handle_data(self, data: str) -> None:
            data = data.strip()
            if 'add in specific javascript functions here' in data:
                self.black = self.__extract(r'var blackink=(\d+)', data, self.black)
                self.cyan = self.__extract(r'var cyanink=(\d+)', data, self.cyan)
                self.yellow = self.__extract(r'var yellowink=(\d+)', data, self.yellow)
                self.magenta = self.__extract(r'var magentaink=(\d+)', data, self.magenta)

        def __extract(self, regex, data, previous):
            m = re.search(regex, data)
            return m.group(1) if m else previous

        def debug(self):
            print("C=%s M=%s Y=%s K=%s" % (self.cyan, self.magenta, self.yellow, self.black))

    class PagesInfoParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.__read_value = False
            self.__next_td = False
            self.pages = None

        def handle_starttag(self, tag: str, attrs: list) -> None:
            if tag == 'td' and self.__next_td:
                self.__read_value = True
                self.__next_td = False

        def handle_endtag(self, tag: str) -> None:
            if tag == 'td':
                self.__read_value = False

        def handle_data(self, data: str) -> None:
            data = data.strip().lower()
            if 'total page count' in data:
                self.__next_td = True
            if self.__read_value:
                self.pages = data

    # from lxml import etree

    parser = InkInfoParser()
    parser.feed(result)
    c = parser.cyan
    m = parser.magenta
    y = parser.yellow
    k = parser.black

    parser = PagesInfoParser()
    parser.feed(result)
    pages = parser.pages

    return PrinterInfo(c, m, y, k, pages)
