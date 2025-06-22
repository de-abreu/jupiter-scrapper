import sys
from app.scrapper import Scrapper


def main():
    s: Scrapper
    qtd: int

    if len(sys.argv) == 1:
        qtd = -1
    elif len(sys.argv) == 2:
        qtd = int(sys.argv[1])
    else:
        raise ValueError(
            f"Foram encontrados no comando os seguintes argumentos estranhos, remova-os e tente novamente: {sys.argv[2:]}"
        )

    s = Scrapper(qtd)
    s.menu()


if __name__ == "__main__":
    main()
