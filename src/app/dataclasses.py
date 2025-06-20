from dataclasses import dataclass, field
from enum import Enum

Periodo = Enum("Período", ["matutino", "vespertino", "noturno", "integral"])


@dataclass
class Disciplina:
    nome: str
    codigo: str
    cursos: list[str]
    creditos_aula: int = 0
    creditos_trabalho: int = 0
    carga_horaria: int = 0
    horas_estagio: int = 0
    horas_pcc: int = 0
    atividades_tpa: int = 0


@dataclass
class Curso:
    nome: str
    periodo: Periodo
    duracao_ideal: int | None = None  # Dada em semestres
    duracao_max: int | None = None  # Dada em semestres
    obrigatorias: dict[str, Disciplina] = field(default_factory=dict)
    optativas_livres: dict[str, Disciplina] = field(default_factory=dict)
    optativas_eletivas: dict[str, Disciplina] = field(default_factory=dict)


@dataclass
class Unidade:
    nome: str
    sigla: str
    cursos: dict[str, Curso] = field(default_factory=dict)
