from bs4.element import Tag
from .dataclasses import Disciplina, Unidade, Curso
from shutil import which
from bs4 import BeautifulSoup
from tabulate import tabulate
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

        # Wait for the overlay to disappear
        _ = WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "div.blockUI.blockOverlay")
            )
        )
        # Now click the "Grade Curricular" tab
        grade_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step4-tab"))
        )
        grade_tab.click()

        _ = WebDriverWait(self.driver, 10).until(
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
            curso.optativas_livres = self._populate_disciplinas(curso.nome, tables[1])
            curso.optativas_eletivas = self._populate_disciplinas(curso.nome, tables[2])
        except IndexError:
            pass

        # Click the "Buscar" button again to reset the page
        buscar_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#step1-tab"))
        )
        buscar_button.click()

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
        print(f"Curso: {curso.nome} ({curso.periodo})")
        print(f"Duração ideal: {curso.duracao_ideal} semestres")
        print(f"Duração máxima: {curso.duracao_max} semestres")
        print("\nDisciplinas obrigatórias:")
        for disciplina in curso.obrigatorias.values():
            print(f"- {disciplina.nome} ({disciplina.codigo})")

        print("\nDisciplinas optativas livres:")
        for disciplina in curso.optativas_livres.values():
            print(f"- {disciplina.nome} ({disciplina.codigo})")

        print("\nDisciplinas optativas eletivas:")
        for disciplina in curso.optativas_eletivas.values():
            print(f"- {disciplina.nome} ({disciplina.codigo})")
        

    def _listar_cursos_unidade(self, unidade: Unidade) -> None:
        print(f"\nCursos disponíveis na unidade {unidade.nome} ({unidade.sigla}):")
        counter = 0
        table = [["Número", "Nome do Curso", "Período"]]
        for curso in unidade.cursos.values():
            counter += 1
            table.append([str(counter), curso.nome, curso.periodo])
        
        print(tabulate(table, headers="firstrow", tablefmt="grid"))

        while True:
            prompt = "\nDigite o número do curso para listar as informações ou 'sair' para voltar ao menu: "
            escolha = input(prompt).strip().upper()
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
         
        print(tabulate(table, headers="firstrow", tablefmt="grid"))

        prompt = "\nPara buscar cursos de unidade específica, digite a sigla da unidade. Digite 'sair' para voltar ao menu: "

        while True:
            sigla = input(prompt).strip().upper()
            if sigla == "SAIR":
                return
            if sigla in self.unidades_dict:
                _unidade = self.unidades_dict[sigla]
                self._listar_cursos_unidade(_unidade)
            else:
                print("Sigla inválida, tente novamente.")

    def menu(self) -> None:
        prompt = """
        Busque informações no sistema Jupiter. Opções:
        1. Listar unidades disponíveis
        2. Listar cursos disponíveis
        3. Buscar disciplina
        4. Buscar disciplinas comuns a mais de um curso
        5. Sair
        Selecione [1-5]:
        """
        while True:
            print(prompt)
            match int(input()):
                case 1:
                    self._listar_unidades()
                case 2:
                    self._listar_cursos()
                case 3:
                    self._buscar_disciplina()
                case 4:
                    self._listar_disciplinas_comuns()
                case 5:
                    return
                case _:
                    raise ValueError("Somente valores de 1 à 5 são aceitos")
