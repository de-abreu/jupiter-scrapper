from .dataclasses import Disciplina, Unidade, Curso
from shutil import which
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class Scrapper:
    URL: str = "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
    unidades_dict: dict[str, Unidade]
    # disciplinas_dict: dict[str, Disciplina]

    def __init__(self, max: int) -> None:
        service = Service(executable_path=which("chromedriver"))

        with Chrome(service=service) as driver:
            driver.get(self.URL)
            self.unidades_dict = self._init_unidades(max, driver)
            for unidade in self.unidades_dict.values():
                unidade.cursos = self._fetch_cursos(unidade.nome, driver)

    @staticmethod
    def _init_unidades(max: int, driver: Chrome) -> dict[str, Unidade]:
        # Wait for the dropdown to be clickable and click it
        unidades_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "comboUnidade"))
        )
        unidades_dropdown.click()

        # Wait for the options to be present in the dropdown
        _ = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select#comboUnidade option")
            )
        )

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract options
        unidades_options = soup.find("select", id="comboUnidade")
        if not unidades_options:
            raise ValueError("Dropdown para Unidades não foi encontrado")

        unidades_dict: dict[str, Unidade] = {}
        count = 0
        for option in unidades_options.find_all("option"):
            if count == max:
                return unidades_dict
            if text := option.text.strip():
                nome, sigla = text.split(" - ( ", 1)
                sigla = sigla.rstrip(" )")
                unidades_dict[sigla] = Unidade(nome=nome, sigla=sigla)
                count += 1
        return unidades_dict

    @staticmethod
    def _fetch_cursos(unidade_nome: str, driver: Chrome) -> dict[str, Curso]:
        # Select the unit in the dropdown
        unidade_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "comboUnidade"))
        )
        unidade_dropdown.send_keys(unidade_nome)

        # Wait for the course dropdown options to be present
        _ = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select#comboCurso option")
            )
        )

        # Parse the course dropdown
        curso_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "comboCurso"))
        )
        curso_dropdown.click()
        time.sleep(0.05)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        curso_options = soup.find("select", id="comboCurso")

        cursos_dict: dict[str, Curso] = {}
        if not curso_options:
            raise ValueError("Dropdown para Cursos não foi encontrado")
        for option in curso_options.find_all("option"):
            if text := option.text.strip():
                nome, periodo = text.split(" - ", 1)
                cursos_dict[nome] = Curso(nome=nome, periodo=periodo)
        return cursos_dict
