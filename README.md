# PDF Coordinates Mapper

Aplicativo desktop em Python/PySide6 para abrir PDFs, clicar em pontos visuais e salvar coordenadas nomeadas em JSON estruturado.

## Recursos

- Abrir um PDF e navegar entre páginas.
- Aplicar zoom na visualização.
- Comparar lado a lado a visualização **Real** com o **Preview** sincronizado.
- Clicar no PDF para criar pontos nomeados.
- Salvar coordenadas reais do PDF em pontos PyMuPDF.
- Reabrir projetos existentes a partir do JSON.
- Preservar pontos existentes e criar backups ao sobrescrever projetos.
- Exportar um resumo dos pontos mapeados.
- No WSL, abrir o seletor nativo de arquivos do Windows para evitar bugs do diálogo Qt/Linux.

## Instalação

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
```

Linux, macOS ou WSL:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

Windows:

```bash
python main.py
```

Linux:

```bash
python3 main.py
```

## Uso

1. Clique em `Selecionar PDF`.
2. Informe o nome do projeto.
3. Escolha onde salvar o JSON.
4. Clique em `Iniciar mapeamento`.
5. Clique em uma posição do PDF.
6. Digite o nome do ponto e salve.

O painel **Real** é o único que aceita cliques e mostra as marcações de coordenadas.
O painel **Preview** mostra, para os pontos da página atual, como um `X` vermelho em
Arial 12 pontos ficaria no PDF. Ele acompanha o mesmo zoom e a mesma rolagem do painel
Real. O preview é apenas visual: não altera o PDF nem adiciona configurações ao JSON.

Para abrir um projeto existente, clique em `Abrir projeto existente` e selecione o JSON. Se o PDF original não for encontrado, o app solicita um PDF substituto.

## Formato do JSON

```json
{
  "project_name": "exemplo",
  "pdf_path": "caminho/original.pdf",
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:05:00",
  "coordinate_system": "PyMuPDF PDF points",
  "page_index_base": 0,
  "points": {
    "campo_nome": {
      "page": 0,
      "page_label": 1,
      "x": 123.45,
      "y": 678.9
    }
  },
  "pdf_metadata": {
    "page_count": 1,
    "page_sizes": [
      {
        "page": 0,
        "width": 595.0,
        "height": 842.0
      }
    ]
  }
}
```

## Coordenadas

O PDF é renderizado com PyMuPDF usando zoom. Quando o usuário clica na imagem renderizada, o app converte a posição para coordenadas reais do PDF:

```text
pdf_x = screen_x / zoom
pdf_y = screen_y / zoom
```

As páginas usam índice baseado em zero, o mesmo padrão do PyMuPDF.

## Testes

```bash
python -m compileall main.py app tests
pytest
```

## Estrutura

```text
app/
  gui/       Interface PySide6
  models/    Dataclasses do projeto
  services/  Renderização, coordenadas e persistência
  utils/     Utilidades pequenas
tests/       Testes unitários
main.py      Entrada da aplicação
```
