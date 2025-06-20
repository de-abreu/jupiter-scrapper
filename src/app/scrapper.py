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
    driver: Chrome
    unidades_dict: dict[str, Unidade]
    disciplinas_dict: dict[str, Disciplina]

    def __init__(self, max: int) -> None:
        service = Service(executable_path=which("chromedriver"))

        with Chrome(service=service) as driver:
            driver.get(self.URL)
            self.driver = driver
            self.unidades_dict = self._init_unidades(max)
            self.disciplinas_dict = {}
            for unidade in self.unidades_dict.values():
                unidade.cursos = self._fetch_cursos(unidade.nome)

    def _init_unidades(self, max: int) -> dict[str, Unidade]:
        # Wait for the dropdown to be clickable and click it
        unidades_dropdown = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "comboUnidade"))
        )
        unidades_dropdown.click()

        # Wait for the options to be present in the dropdown
        _ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select#comboUnidade option")
            )
        )

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

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

    def _fetch_cursos(self, unidade_nome: str) -> dict[str, Curso]:
        # Select the unit in the dropdown
        unidade_dropdown = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "comboUnidade"))
        )
        unidade_dropdown.send_keys(unidade_nome)

        # Wait for the course dropdown options to be present
        _ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select#comboCurso option")
            )
        )

        # Parse the course dropdown
        curso_dropdown = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "comboCurso"))
        )
        curso_dropdown.click()
        time.sleep(0.05)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        curso_options = soup.find("select", id="comboCurso")

        cursos_dict: dict[str, Curso] = {}
        if not curso_options:
            raise ValueError("Dropdown para Cursos não foi encontrado")
        for option in curso_options.find_all("option"):
            if text := option.text.strip():
                nome, periodo = text.split(" - ", 1)
                cursos_dict[nome] = Curso(nome=nome, periodo=periodo)
        for curso in cursos_dict.values():
            self._populate_curso(curso)
        return cursos_dict

    def _populate_curso(self, curso: Curso) -> None:
        # Select the course in the dropdown
        curso_dropdown = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "comboCurso"))
        )
        curso_dropdown.send_keys(curso.nome)

        # Click the "Buscar" button
        buscar_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "enviar"))
        )
        buscar_button.click()

        # Wait for "Grade Curricular" tab to be selectable and click it
        grade_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step4-tab"))
        )
        grade_tab.click()

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        duracao_ideal_span = soup.find("span", class_="duridlhab")
        if duracao_ideal_span:
            curso.duracao_ideal = int(duracao_ideal_span.text.strip())
        else:
            raise ValueError("Span 'duridlhab' não encontrado")
        duracao_max_span = soup.find("span", class_="durmaxhab")
        if duracao_max_span:
            curso.duracao_max = int(duracao_max_span.text.strip())
        else:
            raise ValueError("Span 'durmaxhab' não encontrado")

        # Click the "Buscar" button again to reset the page
        buscar_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step1-tab"))
        )
        buscar_button.click()
