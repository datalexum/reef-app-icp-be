import re
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from session.session_provider import AbstractSessionProvider
import models.APIModels

class AbstractScrapper(ABC):
    def __init__(self, session_provider: AbstractSessionProvider):
        self.session_provider = session_provider

    @staticmethod
    @abstractmethod
    def get_tanks(session):
        pass

    @staticmethod
    @abstractmethod
    def list_analysis(session, tank_id):
        pass

    @abstractmethod
    def get_analysis(self, session, tank_id, analysis_id):
        pass


class FaunaMarinScraper(AbstractScrapper):

    @staticmethod
    def get_tanks(session):
        tanks_url = 'https://lab.faunamarin.de/de/home/aquarium'
        tanks_page_response = session.get(tanks_url)
        soup = BeautifulSoup(tanks_page_response.content, 'html.parser')

        url_pattern = re.compile(r'https://lab\.faunamarin\.de/de/home/aquarium/(\d+)/edit')

        tanks = []
        ids = set()
        for link in soup.find_all('a', href=True):
            match = url_pattern.match(link['href'])
            if match:
                tank_id = match.group(1)
                if tank_id not in ids:
                    tank_name = link.text.split(" (" + tank_id + ")")[0].lstrip()
                    ids.add(tank_id)
                    tanks.append(models.APIModels.ReefTank(id=int(tank_id), name=str(tank_name)))

        return tanks

    @staticmethod
    def list_analysis(session, tank_id):
        tank_analysis_url = f'https://lab.faunamarin.de/de/home/analysis/single/aquarium/{tank_id}'

        analysis_url_pattern = re.compile(r'https://lab\.faunamarin\.de/de/home/analysis/(\d+)')

        response = session.get(tank_analysis_url, verify=False)

        soup = BeautifulSoup(response.content, 'html.parser')

        analysis_rows = soup.find_all('div', class_='row striped')
        tank_analyses = []
        for row in analysis_rows:
            link = row.find('a', href=True)
            match = analysis_url_pattern.match(link['href'])
            if match:
                analysis_id = match.group(1)
                date_product_list = row.find('div', class_='col-sm-4').get_text(strip=True).split("Analyse "+analysis_id)[1].lstrip().replace("(", "").replace(")", "").split(",")
                date = row.find('div', class_='col-sm-4').get_text(strip=True).split("Analyse "+analysis_id)[1].lstrip().replace("(", "").replace(")", "").split(",")[0]
                product = "normal" if len(date_product_list) == 1 else "extended"
                analysis_type = row.find('div', class_='col-sm-3').get_text(strip=True)
                vendor = row.find('div', class_='col-sm-2').get_text(strip=True)
                if vendor == 'Fauna Marin Analyse':
                    tank_analyses.append({'id': analysis_id, 'type': analysis_type, 'date': date, 'product': product})

        return tank_analyses

    def get_analysis(self, session, tank_id, analysis_id):
        analysis = {'id': analysis_id}
        analysis_url = f'https://lab.faunamarin.de/de/home/analysis/{analysis_id}'
        response = session.get(analysis_url)
        soup = BeautifulSoup(response.content, 'lxml')

        # Optimized date extraction
        card_header = soup.find('div', class_='card-header')
        if card_header:
            date_added = re.search(r'\d{2}\.\d{2}\.\d{4}', card_header.text)
            if date_added:
                analysis['date'] = date_added.group()

        values = []
        for row in soup.find_all('div', class_='row striped'):
            element, value, unit = self.parse_row(row)
            if element:
                values.append({'element': element, 'value': value, 'unit': unit})
        analysis['values'] = values
        return analysis

    @staticmethod
    def parse_row(row):
        h2 = row.find('h2')
        if h2:
            text = h2.get_text(strip=True)
            if 'Nicht nachweisbar' in text:
                return text.split("Nicht nachweisbar")[0], 0.0, ''

        gauge_div = row.find('div', class_='gauge_text')
        if gauge_div:
            text = gauge_div.get_text(strip=True)
            parts = text.split(':')
            if len(parts) == 2:
                element = parts[0].strip()
                if "/" in element:
                    return None, None, None
                value_unit = parts[1].split()
                value = value_unit[0].replace(',', '.')
                unit = " ".join(value_unit[1:]) if len(value_unit) > 1 else ""
                return element, float(value), unit
        return None, None, None
