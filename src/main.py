import sys
from app.scrapper import Scrapper


def main():
    prompt = "Espere enquanto nós coletamos as informações, isso pode levar alguns minutos..."
    s: Scrapper
    if len(sys.argv) == 1:
        print(prompt)
        s = Scrapper(-1)
    elif len(sys.argv) == 2:
        print(prompt)
        s = Scrapper(int(sys.argv[1]))
    else:
        raise ValueError(
            f"Foram encontrados no comando os seguintes argumentos estranhos, remova-os e tente novamente: {sys.argv[2:]}"
        )

    # print(s.unidades_dict)
    s.menu()


if __name__ == "__main__":
    main()
