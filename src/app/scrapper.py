import time
from shutil import which

from bs4 import BeautifulSoup
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
    TABLE_STYLE: str = "rounded_outline"
    URL: str = "https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275"
    init_success: bool = False
    disciplinas_dict: dict[str, Disciplina]
    driver: Chrome
    unidades_dict: dict[str, Unidade]

    def __init__(self, max: int) -> None:
        service = Service(executable_path=which("chromedriver"))

        print(
            "Espere enquanto coletamos as informações, isso pode levar alguns minutos..."
        )
        with Chrome(service=service) as driver:
            try:
                driver.get(self.URL)
                self.driver = driver
            except Exception:
                print(
                    "Erro: Conexão à internet indisponível. Conecte-se e tente novamente."
                )
                return

            while True:
                try:
                    _ = WebDriverWait(self.driver, 30).until(
                        lambda d: bool(
                            d.execute_script("return document.readyState") == "complete"
                        )
                    )
                    self.unidades_dict = self._init_unidades(max)
                    break
                except TimeoutException:
                    if not self._retry():
                        return

            self.disciplinas_dict = {}
            for unidade in self.unidades_dict.values():
                unidade.cursos, cancelled = self._fetch_cursos(unidade.nome)
                if cancelled:
                    return
            self.init_success = True

    @staticmethod
    def _retry() -> bool:
        match (
            input(
                "Falha de conexão ao sistema Jupiter, deseja tentar conectar novamente? [s]im/[n]ão: "
            )
            .strip()
            .upper()
        ):
            case "S" | "SIM":
                return True
            case _:
                print("Pesquisa cancelada.")
                return False

    def _wait_overlay(self) -> None:
        _ = WebDriverWait(self.driver, 30).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "div.blockUI.blockOverlay")
            )
        )

    def _init_unidades(self, max: int) -> dict[str, Unidade]:
        # Wait for the dropdown to be clickable and click it
        unidades_dropdown = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.ID, "comboUnidade"))
        )
        unidades_dropdown.click()

        # Wait for at least one option to be present and visible in the dropdown
        _ = WebDriverWait(self.driver, 30).until(
            lambda d: bool(
                len(d.find_elements(By.CSS_SELECTOR, "select#comboUnidade option")) > 1
            )
        )

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        unidades_options = soup.find("select", id="comboUnidade")
        if not unidades_options:
            raise ValueError("Dropdown para Unidades não foi encontrado")
        count = 0
        unidades_dict: dict[str, Unidade] = {}

        for option in unidades_options.find_all("option"):
            if count == max:
                return unidades_dict
            if text := option.text.strip():
                nome, sigla = text.split(" - ( ", 1)
                sigla = sigla.rstrip(" )")
                unidades_dict[sigla] = Unidade(nome=nome, sigla=sigla)
                count += 1

        return unidades_dict

    def _fetch_cursos(self, unidade_nome: str) -> tuple[dict[str, Curso], bool]:
        cursos_dict: dict[str, Curso] = {}
        while True:
            try:
                # Select the unit in the dropdown
                unidade_dropdown = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "comboUnidade"))
                )
                unidade_dropdown.send_keys(unidade_nome)

                # Click on the comboCurso dropdown
                curso_dropdown = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.ID, "comboCurso"))
                )
                curso_dropdown.click()

                # Wait for options to be present and visible
                _ = WebDriverWait(self.driver, 30).until(
                    lambda d: bool(
                        len(
                            d.find_elements(By.CSS_SELECTOR, "select#comboCurso option")
                        )
                        > 1
                    )
                )
                break
            except TimeoutException:
                if not self._retry():
                    return cursos_dict, True

        time.sleep(0.05)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        curso_options = soup.find("select", id="comboCurso")
        if not curso_options:
            raise ValueError("Dropdown para Cursos não foi encontrado")

        for option in curso_options.find_all("option"):
            if text := option.text.strip():
                nome, periodo = text.rsplit(" - ", 1)
                cursos_dict[nome] = Curso(nome=nome, periodo=periodo)
        for curso in cursos_dict.values():
            if cancelled := self._populate_curso(curso):
                return cursos_dict, True
        return cursos_dict, False

    def _populate_curso(self, curso: Curso) -> bool:
        while True:
            try:
                # Select the course in the dropdown
                curso_dropdown = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "comboCurso"))
                )
                curso_dropdown.send_keys(curso.nome)

                # Click the "Buscar" button
                buscar_button = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "enviar"))
                )
                buscar_button.click()
                self._wait_overlay()
                break
            except TimeoutException:
                if not self._retry():
                    return True

        # Now click the "Grade Curricular" tab
        while True:
            try:
                grade_tab = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step4-tab"))
                )
                grade_tab.click()
                break
            except TimeoutException:
                if not self._retry():
                    return True
            except Exception as _:
                # If "Grade Curricular" tab is unavailable
                try:
                    close_button = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.ui-dialog-buttonset")
                        )
                    )
                    close_button.click()
                    return False
                except TimeoutException:
                    if not self._retry():
                        return True

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
        # If the "Grade Curricular" tab is available, but its page contains no tables
        except TimeoutException:
            pass

        # Click the "Buscar" tab to reset the page
        while True:
            try:
                self._wait_overlay()
                buscar_button = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step1-tab"))
                )
                buscar_button.click()
                break
            except TimeoutException:
                if not self._retry():
                    return True
        return False

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
        print("\n" + tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

        print("\nDisciplinas obrigatórias:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.obrigatorias.values():
            nome_normalizado = disciplina.nome.replace(
                "–", "-"
            )  # Replace en dash with hyphen
            table.append([nome_normalizado, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

        print("\nDisciplinas optativas livres:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.optativas_livres.values():
            table.append([disciplina.nome, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

        print("\nDisciplinas optativas eletivas:")

        table = [["Nome da Disciplina", "Código"]]
        for disciplina in curso.optativas_eletivas.values():
            table.append([disciplina.nome, disciplina.codigo])
        print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

    def _listar_cursos_unidade(self, unidade: Unidade) -> None:
        counter = 0
        table = [
            ["Número", "Nome do Curso", "Período"],
            ["0", "Listar Dados de Todos os Cursos", " -- "],
        ]
        for curso in unidade.cursos.values():
            counter += 1
            table.append([str(counter), curso.nome, curso.periodo])

        while True:
            print(f"\nCursos disponíveis na unidade {unidade.nome} ({unidade.sigla}):")
            print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

            prompt = "Digite o número do curso para listar as informações ou 'sair' para voltar ao menu:"
            print("\n" + prompt)

            escolha = input("> ").strip().upper()
            if escolha == "SAIR":
                return
            else:
                escolha_numero = int(escolha)
                if 1 <= escolha_numero <= counter:
                    curso = list(unidade.cursos.values())[escolha_numero - 1]
                    print(f"\n{escolha_numero}:")
                    self._listar_dados_curso(curso)
                elif escolha_numero == 0:
                    counter = 1
                    for curso in unidade.cursos.values():
                        print(f"\n{counter}:")
                        self._listar_dados_curso(curso)
                        counter += 1
                else:
                    print("Número inválido, tente novamente.")

    def _listar_unidades(self) -> None:
        print("\nUnidades disponíveis:")
        table = [["Sigla", "Nome"]]
        for unidade in self.unidades_dict.values():
            table.append([unidade.sigla, unidade.nome])

        prompt = "Para buscar cursos de unidade específica, digite a sigla da unidade. Digite 'sair' para voltar ao menu:"

        while True:
            print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))
            print("\n" + prompt)

            sigla = input("> ").strip().upper()
            if sigla == "SAIR":
                return
            if sigla in self.unidades_dict:
                _unidade = self.unidades_dict[sigla]
                self._listar_cursos_unidade(_unidade)
            else:
                print("Sigla inválida, tente novamente.")

    def _listar_todos_cursos(self) -> None:
        print("\nDados de todos os cursos disponíveis:")
        for unidade in self.unidades_dict.values():
            print(f"\nUnidade: {unidade.nome} ({unidade.sigla})")
            counter = 1
            for curso in unidade.cursos.values():
                print(f"\n{unidade.sigla} - {counter}:")
                self._listar_dados_curso(curso)
                counter += 1

        prompt = "Digite 'sair' para voltar ao menu:"

        while True:
            print("\n" + prompt)

            escolha = input("> ").strip().upper()
            if escolha == "SAIR":
                return
            else:
                print("Opção inválida, tente novamente.")

    def _listar_disciplina(self) -> None:
        prompt = "\nDigite o código da disciplina para listar as informações ou 'sair' para voltar ao menu:"

        while True:
            print(prompt)
            codigo = input("> ").strip().upper()
            if codigo == "SAIR":
                return
            if codigo in self.disciplinas_dict:
                disciplina = self.disciplinas_dict[codigo]
                table = [
                    ["Nome", "Código", "Créditos Aula", "Créditos Trabalho"],
                    [
                        disciplina.nome,
                        disciplina.codigo,
                        disciplina.creditos_aula,
                        disciplina.creditos_trabalho,
                    ],
                ]
                print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

                table = [
                    ["Carga Horária", f"{disciplina.carga_horaria} horas"],
                    ["Horas de Estágio", f"{disciplina.horas_estagio} horas"],
                    ["Horas de PCC", f"{disciplina.horas_pcc} horas"],
                    ["Atividades TPA", f"{disciplina.atividades_tpa} horas"],
                ]
                print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

                table = [["Curso"]]
                for curso in disciplina.cursos:
                    table.append([curso])

                print("\nCursos que oferecem essa disciplina:")
                print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))
            else:
                print("Código inválido, tente novamente.")

    def _listar_disciplinas_comuns(self) -> None:
        table = [["Nome da Disciplina", "Código", "Qtd Cursos"]]
        for disciplina in self.disciplinas_dict.values():
            qtd_cursos = len(disciplina.cursos)
            if qtd_cursos > 1:
                table.append([disciplina.nome, disciplina.codigo, str(qtd_cursos)])

        print("\nDisciplinas comuns a mais de um curso:")
        print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))

    def menu(self) -> None:
        prompt = "Busque informações no sistema Jupiter, ou digite 'sair' para fechar o programa:"

        table = [
            ["Opção", "Descrição"],
            ["1", "Listar unidades disponíveis"],
            ["2", "Listar dados de todos os cursos disponíveis"],
            ["3", "Listar dados de uma disciplina específica"],
            ["4", "Buscar disciplinas comuns a mais de um curso"],
        ]
        while self.init_success:
            print("\n" + prompt)
            print(tabulate(table, headers="firstrow", tablefmt=self.TABLE_STYLE))
            match input("> ").strip().upper():
                case "1":
                    self._listar_unidades()
                case "2":
                    self._listar_todos_cursos()
                case "3":
                    self._listar_disciplina()
                case "4":
                    self._listar_disciplinas_comuns()
                case "SAIR":
                    return
                case _:
                    raise ValueError("Valor inválido, tente novamente.")
