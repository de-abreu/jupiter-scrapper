import sys
from app.scrapper import Scrapper


def main():
    s: Scrapper
    if len(sys.argv) == 1:
        s = Scrapper(-1)
    elif len(sys.argv) == 2:
        s = Scrapper(int(sys.argv[1]))
    else:
        raise ValueError(
            f"Argumentos estranhos, remova-os e tente novamente: {sys.argv[2:]}"
        )

    print(s.unidades_dict)

    # while True:
    #     menu = """
    #     Busque informações no sistema Jupiter. Opções:
    #     1. Listar unidades disponíveis
    #     2. Listar cursos disponíveis
    #     3. Buscar curso
    #     4. Buscar disciplina
    #     5. Buscar disciplinas comuns a mais de um curso
    #     6. Sair
    #     Selecione [1-5]:
    #     """
    #     print(menu)
    #     match int(input()):
    #         case 1:
    #         case 2:
    #         case 3:
    #         case 4:
    #         case 5:
    #             break
    #         case _:
    #             raise ValueError("Somente valores de 1 à 4 são aceitos")


if __name__ == "__main__":
    main()
