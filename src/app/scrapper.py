from .dataclasses import Disciplina, Unidade
from shutil import which
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class Scrapper:
    unidades_dict: dict[str, Unidade]
    # disciplinas_dict: dict[str, Disciplina]

    def __init__(self, max: int) -> None:
        self.unidades_dict = self._fetch_units(max)

    def _fetch_units(self, max: int) -> dict[str, Unidade]:
        """
        Fetch all unit options by clicking the dropdown and waiting for dynamic content.
        """
        service = Service(executable_path=which("chromedriver"))

        with webdriver.Chrome(service=service) as driver:
            driver.get(
                "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
            )

            # Wait for the dropdown to be clickable and click it
            dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "comboUnidade"))
            )
            dropdown.click()

            # Wait for options to load (adjust delay as needed)
            time.sleep(1)  # Quick fix; prefer WebDriverWait in production

            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract options
            dropdown = soup.find("select", id="comboUnidade")
            if not dropdown:
                raise ValueError("Dropdown not found!")

            unidades_dict: dict[str, Unidade] = {}
            count = 0
            for option in dropdown.find_all("option"):
                if count == max:
                    break
                if text := option.text.strip():
                    nome, sigla = text.split(" - ( ", 1)
                    sigla = sigla.rstrip(" )")
                    unidades_dict[sigla] = Unidade(nome=nome, sigla=sigla)
                    count += 1

            return unidades_dict
