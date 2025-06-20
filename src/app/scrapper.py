from .dataclasses import Disciplina, Unidade, Curso
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
            unidades_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "comboUnidade"))
            )
            unidades_dropdown.click()

            # Wait for options to load (adjust delay as needed)
            time.sleep(0.5)  # Quick fix; prefer WebDriverWait in production

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
                    break
                if text := option.text.strip():
                    nome, sigla = text.split(" - ( ", 1)
                    sigla = sigla.rstrip(" )")
                    unidades_dict[sigla] = Unidade(nome=nome, sigla=sigla)
                    count += 1

            # Now fetch courses for each unit
            for sigla, unidade in unidades_dict.items():
                # Select the unit in the dropdown
                unidade_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "comboUnidade"))
                )
                unidade_dropdown.send_keys(unidade.nome)

                # Wait for the course dropdown to populate
                time.sleep(0.5)  # Quick fix; prefer WebDriverWait in production

                # Parse the course dropdown
                curso_dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "comboCurso"))
                )
                curso_dropdown.click()
                time.sleep(0.5)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                course_options = soup.find("select", id="comboCurso")

                if not course_options:
                    raise ValueError("Dropdown para Cursos não foi encontrado")
                for course_option in course_options.find_all("option"):
                    if course_text := course_option.text.strip():
                        nome, periodo = course_text.split(" - ", 1)
                        unidade.cursos[nome] = Curso(nome=nome, periodo=periodo)
            return unidades_dict
