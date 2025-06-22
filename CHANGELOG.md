# Changelog

Todas as alterações notáveis a este projeto encontram-se listadas à seguir, em
ordem cronológica reversa:

## [1.0.0]

### Novas Funcionalidades

- **Scrapper**:
  - Implementa a todas as funcionalidades previstas para consulta no menu
    principal(`8885d0a`).
  - Acrescenta capacidade para lidar com cursos os quais não possuem descrição
    de sua grade curricular ou uma tabela que descreva as disciplinas que o
    compõem (`68ab10b`).
  - Acrescenta capacidade de circunvir overlays que impedem a seleção de objetos
    na página(`91fa7e4`).
  - Acrescenta menu e opção de listagem de unidades (`4a34da1`).
  - Acrescenta capacidade de popular a cada Curso com informações específicas
    sobre as disciplinas deste, inicializando objetos `Disciplina` (`25465dd`).
  - Acrescenta a capacidade de popular a cada Curso com informações gerais
    (`0820e1f`).
  - Acrescenta a capacidade de popular o dicionário de cursos de cada unidade
    com objetos `Curso` inicializados com as descrições de nome e período
    (`18537181`).
  - Acrescenta a capacidade de limitar o número de unidades a serem
    pesquisadas(`5c84144`).
  - Acrescenta a capacidade para acessar o sistema Júpiter e popular dicionário
    de unidades (`5c84144`).
  - Acrescenta _dataclasses_ para descrever unidades, cursos e disciplinas
    (`5c84144`).
  - Acrescenta os arquivos `flake.nix` e `requirements.txt`, que descrevem o
    ambiente de desenvolvimento (`ff0e802`).

### Documentação

- **README**:
  - Atualizado com instruções de uso e referência ao presente _changelog_
    (`8a93fac`, `580d1c0`).
  - Criado (`19e20d7`).
