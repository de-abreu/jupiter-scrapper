import time
from logging import raiseExceptions
from shutil import which
from sys import exception
from typing import Any

from bs4 import BeautifulSoup, NavigableString, ResultSet
from bs4.element import Tag
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tabulate import tabulate

from .dataclasses import Curso, Disciplina, Unidade


class Scrapper:
    URL: str = "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
    driver: Chrome
    unidades_dict: dict[str, Unidade]
    disciplinas_dict: dict[str, Disciplina]
    table_style: str = "rounded_outline"

    def __init__(self, max: int) -> None:
        service = Service(executable_path=which("chromedriver"))

        with Chrome(service=service) as driver:
            driver.get(self.URL)
            try:
                _ = WebDriverWait(driver, 30).until(
                    lambda d: bool(
                        d.execute_script("return document.readyState") == "complete"
                    )
                )
            except TimeoutException:
                raise Exception("Pagina demorou muito tempo para carregar.")

            self.driver = driver
            self.unidades_dict = self._init_unidades(max)
            self.disciplinas_dict = {}
            for unidade in self.unidades_dict.values():
                unidade.cursos = self._fetch_cursos(unidade.nome)
                print(unidade.nome)

    def _wait_overlay(self) -> None:
        try:
            _ = WebDriverWait(self.driver, 30).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, "div.blockUI.blockOverlay")
                )
            )
        except TimeoutException:
            raise Exception("Overlay demorou muito tempo para desaparecer.")

    def _init_unidades(self, max: int) -> dict[str, Unidade]:
        unidades_dict: dict[str, Unidade] = {}
        try:
            # Wait for the dropdown to be clickable and click it
            unidades_dropdown = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.ID, "comboUnidade"))
            )
            unidades_dropdown.click()
        except TimeoutException:
            raise Exception("Erro: Tempo excedido ao carregar dropdown de Unidades.")

        try:
            # Wait for at least one option to be present and visible in the dropdown
            _ = WebDriverWait(self.driver, 30).until(
                lambda d: bool(
                    len(d.find_elements(By.CSS_SELECTOR, "select#comboUnidade option"))
                    > 1
                )
            )
        except TimeoutException:
            raise Exception("Erro: Tempo excedido ao carregar dropdown de Unidades.")

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        unidades_options = soup.find("select", id="comboUnidade")
        if not unidades_options:
            raise ValueError("Dropdown para Unidades não foi encontrado")

        count = 0
        for option in unidades_options.find_all("option"):  # type: ignore
            if count == max:
                return unidades_dict
            if text := option.text.strip():
                nome, sigla = text.split(" - ( ", 1)
                sigla = sigla.rstrip(" )")
                unidades_dict[sigla] = Unidade(nome=nome, sigla=sigla)
                count += 1

        return unidades_dict

    def _fetch_cursos(self, unidade_nome: str) -> dict[str, Curso]:
        try:
            # Select the unit in the dropdown
            unidade_dropdown = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.ID, "comboUnidade"))
            )
            unidade_dropdown.send_keys(unidade_nome)
        except TimeoutException:
            raise Exception(
                f"Erro: Tempo excedido ao selecionar a unidade {unidade_nome}."
            )

        try:
            # Parse the course dropdown
            curso_dropdown = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "comboCurso"))
            )
            curso_dropdown.click()
        except TimeoutException:
            raise Exception(
                f"Erro: Tempo excedido ao clicar no dropdown de Cursos para a unidade {unidade_nome}."
            )

        try:
            # Wait for the course dropdown options to be present and visible
            _ = WebDriverWait(self.driver, 30).until(
                lambda d: bool(
                    len(d.find_elements(By.CSS_SELECTOR, "select#comboCurso option"))
                    > 1
                )
            )
        except TimeoutException:
            raise Exception(
                f"Erro: Tempo excedido ao carregar dropdown de Cursos para a unidade {unidade_nome}."
            )

        time.sleep(0.05)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        curso_options = soup.find("select", id="comboCurso")

        cursos_dict: dict[str, Curso] = {}

        if not curso_options:
            raise ValueError("Dropdown para Cursos não foi encontrado")
        for option in curso_options.find_all("option"):
            if text := option.text.strip():
                nome, periodo = text.rsplit(" - ", 1)
                cursos_dict[nome] = Curso(nome=nome, periodo=periodo)
        for curso in cursos_dict.values():
            print(curso.nome)
            self._populate_curso(curso)

        return cursos_dict

    def _populate_curso(self, curso: Curso) -> None:
        try:
            # Select the course in the dropdown
            curso_dropdown = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.ID, "comboCurso"))
            )
            curso_dropdown.send_keys(curso.nome)
        except TimeoutException:
            raise Exception("Erro: Tempo excedido ao selecionar o curso.")

        try:
            # Click the "Buscar" button
            buscar_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.ID, "enviar"))
            )
            buscar_button.click()
        except TimeoutException:
            raise Exception("Erro: Tempo excedido ao clicar no botão 'Buscar'.")

        self._wait_overlay()

        # Now click the "Grade Curricular" tab
        try:
            grade_tab = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step4-tab"))
            )
            grade_tab.click()
        except TimeoutException:
            raise Exception(
                f"Erro: Tempo excedido ao clicar na aba 'Grade Curricular' para o curso {curso.nome}."
            )
        except Exception as _:
            # If "Grade Curricular" tab is unavailable
            print("Hey!")
            try:
                close_button = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.ui-dialog-buttonset")
                    )
                )
                close_button.click()
            except TimeoutException:
                raise Exception("Erro: Tempo excedido ao fechar o diálogo.")
            return

        # If the tab is available, but contains no tables
        try:
            _ = WebDriverWait(self.driver, 0.1).until(
                EC.visibility_of_element_located((By.ID, "gradeCurricular"))
            )

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

            grade_curricular_div = soup.find("div", id="gradeCurricular")
            tables = grade_curricular_div.find_all("table")

            try:
                curso.obrigatorias = self._populate_disciplinas(curso.nome, tables[0])
                curso.optativas_livres = self._populate_disciplinas(
                    curso.nome, tables[1]
                )
                curso.optativas_eletivas = self._populate_disciplinas(
                    curso.nome, tables[2]
                )
            except IndexError:
                pass
        except TimeoutException as _:
            raise Exception(
                f"Erro: Tempo excedido ao buscar a grade curricular do curso {curso.nome}."
            )

        # Click the "Buscar" tab to reset the page
        self._wait_overlay()
        try:
            buscar_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step1-tab"))
            )
            buscar_button.click()
        except TimeoutException:
            raise Exception(
                f"Erro: Tempo excedido ao clicar na aba 'Buscar' para o curso {curso.nome}."
            )

    def _populate_disciplinas(
        self, curso_nome: str, table: Tag
    ) -> dict[str, Disciplina]:
        local_disciplinas_dict: dict[str, Disciplina] = {}

        def fetch_cell(cells: Tag, index: int) -> int:
            value = cells[index].text.strip()
            return int(value) if value else 0

        for tr in table.find_all("tr"):
            if tr.get("style") != "height: 20px;":
                continue

            tds = tr.find_all("td")
            if not tds:
                continue

            codigo = tds[0].text.strip()
            if not codigo:
                continue

            # Check if Disciplina exists in disciplinas_dict
            disciplina = self.disciplinas_dict.get(codigo)
            if disciplina:
                disciplina.cursos.add(curso_nome)
            else:
                self.disciplinas_dict[codigo] = disciplina = Disciplina(
                    codigo=codigo,
                    nome=tds[1].text.strip() if len(tds) > 1 else "",
                    creditos_aula=fetch_cell(tds, 2),
                    creditos_trabalho=fetch_cell(tds, 3),
                    carga_horaria=fetch_cell(tds, 4),
                    horas_estagio=fetch_cell(tds, 5),
                    horas_pcc=fetch_cell(tds, 6),
                    atividades_tpa=fetch_cell(tds, 7),
                    cursos={curso_nome},
                )
            local_disciplinas_dict[codigo] = disciplina
        return local_disciplinas_dict

    def _listar_dados_curso(self, curso: Curso) -> None:
        table = [
            ["Nome", "Período", "Duração Ideal", "Duração Máxima"],
            [
                curso.nome,
                curso.periodo,
                f"{curso.duracao_ideal} semestres",
                f"{curso.duracao_max} semestres",
            ],
        ]
        print("\n" + tabulate(table, headers="firstrow", tablefmt=self.table_style))

        print("\nDisciplinas obrigatórias:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.obrigatorias.values():
            table.append([disciplina.nome, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.table_style))

        print("\nDisciplinas optativas livres:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.optativas_livres.values():
            table.append([disciplina.nome, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.table_style))

        print("\nDisciplinas optativas eletivas:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.optativas_eletivas.values():
            table.append([disciplina.nome, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.table_style))

    def _listar_cursos_unidade(self, unidade: Unidade) -> None:
        counter = 0
        table = [["Número", "Nome do Curso", "Período"]]
        for curso in unidade.cursos.values():
            counter += 1
            table.append([str(counter), curso.nome, curso.periodo])

        while True:
            print(f"\nCursos disponíveis na unidade {unidade.nome} ({unidade.sigla}):")
            print(tabulate(table, headers="firstrow", tablefmt=self.table_style))

            prompt = "Digite o número do curso para listar as informações ou 'sair' para voltar ao menu:"
            print("\n" + prompt)

            escolha = input("> ").strip().upper()
            if escolha == "SAIR":
                return
            else:
                escolha_numero = int(escolha)
                if 1 <= escolha_numero <= counter:
                    curso = list(unidade.cursos.values())[escolha_numero - 1]
                    self._listar_dados_curso(curso)
                else:
                    print("Número inválido, tente novamente.")

    def _listar_unidades(self) -> None:
        print("\nUnidades disponíveis:")
        table = [["Sigla", "Nome"]]
        for unidade in self.unidades_dict.values():
            table.append([unidade.sigla, unidade.nome])

        prompt = "Para buscar cursos de unidade específica, digite a sigla da unidade. Digite 'sair' para voltar ao menu:"

        while True:
            print(tabulate(table, headers="firstrow", tablefmt=self.table_style))
            print("\n" + prompt)

            sigla = input("> ").strip().upper()
            if sigla == "SAIR":
                return
            if sigla in self.unidades_dict:
                _unidade = self.unidades_dict[sigla]
                self._listar_cursos_unidade(_unidade)
            else:
                print("Sigla inválida, tente novamente.")

    def menu(self) -> None:
        prompt = "Busque informações no sistema Jupiter, ou digite 'sair' para fechar o programa:"

        table = [
            ["Opção", "Descrição"],
            ["1", "Listar unidades disponíveis"],
            ["2", "Listar cursos disponíveis"],
            ["3", "Buscar disciplina específica"],
            ["4", "Buscar disciplinas comuns a mais de um curso"],
        ]
        while True:
            print("\n" + prompt)
            print(tabulate(table, headers="firstrow", tablefmt=self.table_style))
            match input("> ").strip().upper():
                case "1":
                    self._listar_unidades()
                case "2":
                    self._listar_cursos()
                case "3":
                    self._buscar_disciplina()
                case "4":
                    self._listar_disciplinas_comuns()
                case "SAIR":
                    return
                case _:
                    raise ValueError("Valor inválido, tente novamente.")
