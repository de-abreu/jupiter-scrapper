# jupiter-scrapper

Um web scrapper para buscar ou listar informações sobre cursos oferecidos pela
Universidade de São Paulo (USP) por meio do sistema online
[Jupiter](https://uspdigital.usp.br/jupiterweb/jupCarreira.jsp?codmnu=8275)

# Executando o Script

## Intalando Dependências

- beautifulsoup4 (>=4.13.4,<5.0.0)
- selenium (>=4.33.0,<5.0.0)
- types-beautifulsoup4 (>=4.12.0.20250516,<5.0.0.0)
- tabulate (>=0.9.0,<0.10.0)

Você pode instalar as dependencias usando o arquivo `requirements.txt` ou usando Poetry:

### requirements.txt

```bash
pip install -r requirements.txt
```

### Poetry

Certifique se que você tem o Poetry instalado

```bash
pip install -u poetry
```

Instale as dependencias usando o comando `poetry`

```bash
poetry install
```

## Instruções de Uso

Para usar o scrapper você deve executar o script em `src/main.py` sem nenhum argumento ou com no máximo 1 argumento numérico inteiro. O argumento passado definirá a quantidade de unidades da USP serão tratadas pelo script, se não houver nenhum argumento, todas as unidades serão tratadas.

```bash
python src/main.py [arg]
```

Ou, se estiver usando poetry:

```bash
poetry run python src/main.py [arg]
```
