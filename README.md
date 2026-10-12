# cdc-rag

Assistente para tirar dúvidas sobre o Código de Defesa do Consumidor (Lei 8.078/1990).
Responde em português, cita os artigos usados e permite abrir o texto de cada um.
Tudo roda na sua máquina: os modelos são servidos pelo [Ollama](https://ollama.com) e
nenhuma pergunta sai do computador.

Funciona pelo terminal ou por uma interface web em `http://127.0.0.1:8000`.

## Como funciona

1. **Extração.** A lei é baixada do site do Planalto e guardada em `data/cdc.htm`. O HTML
   é limpo (texto revogado, títulos de capítulo, assinaturas) e dividido em artigos.
   Artigos vetados são ignorados, e artigos entre aspas são tratados como citação de outra
   lei, não como artigo do CDC.
2. **Indexação.** Cada artigo vira um vetor com o modelo `bge-m3`. Os vetores ficam
   normalizados em `data/vectors.npy` e o texto em `data/articles.json`.
3. **Busca.** Termos populares como "venda casada" ou "nome no Serasa" não aparecem no
   texto da lei. Por isso o `qwen3:8b` primeiro reescreve a pergunta em linguagem jurídica.
   A pergunta original e a reescrita são combinadas, viram um vetor, e os 5 artigos mais
   próximos (similaridade de cosseno) são selecionados.
4. **Resposta.** Os artigos encontrados vão para o modelo junto com a pergunta e a
   instrução de responder só com base neles. A resposta chega aos poucos (streaming).
5. **Histórico.** Quando a resposta termina, pergunta, resposta e artigos consultados são
   gravados em `data/rag.db`. Respostas interrompidas no meio não são gravadas.

## Requisitos

- Python 3.9 ou mais novo
- [Ollama](https://ollama.com) com os modelos `bge-m3` e `qwen3:8b`
- Node.js 22.7 ou mais novo, só para rodar o teste do front-end
- Acesso à internet na primeira indexação, para baixar a lei

## Instalação

Baixe os modelos e deixe o Ollama rodando:

```
ollama pull bge-m3
ollama pull qwen3:8b
ollama serve
```

### Com pyenv

O repositório já tem um `.python-version` apontando para o virtualenv `cdc-rag`. Basta
criá-lo (precisa do plugin [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)):

```
pyenv install 3.9.7
pyenv virtualenv 3.9.7 cdc-rag
pip install --upgrade pip
pip install -e ".[dev]"
```

Ao entrar na pasta do projeto, o pyenv ativa o virtualenv sozinho.

### Sem pyenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

O pip precisa ser 21.3 ou mais novo para instalar em modo editável a partir do
`pyproject.toml`, por isso o `--upgrade pip`. O extra `dev` instala o `httpx`, usado só
pelos testes da API.

## Uso

```
cdc-rag index                        baixa o CDC e gera o índice
cdc-rag "posso devolver um produto?" responde uma pergunta
cdc-rag                              chat no terminal (Ctrl+D para sair)
cdc-rag web                          interface web em http://127.0.0.1:8000
cdc-rag historico                    mostra as últimas 10 perguntas
cdc-rag caso "pergunta" "Art. 26"    cadastra um caso de teste da busca
```

Não é preciso rodar `index` antes do primeiro uso: se o índice não existir, ele é gerado
automaticamente na primeira pergunta.

### Interface web

- Sugestões de perguntas na tela inicial
- Resposta em tempo real, com os artigos citados destacados no texto
- Clique em qualquer artigo citado para ler o texto da lei, com as notas de redação
  em destaque
- Histórico das últimas 20 perguntas na barra lateral (no celular, no botão "Histórico")

O front-end é HTML, CSS e JavaScript puros, sem etapa de build. O texto vindo do modelo é
sempre escapado antes de virar HTML, e uma citação só vira link se o artigo existir no
índice.

## Configuração

Os valores ficam em `src/config.py`:

| Nome          | Padrão                   | Para que serve                                                          |
| ------------- | ------------------------ | ----------------------------------------------------------------------- |
| `CDC_URL`     | página do CDC no Planalto | de onde a lei é baixada                                                |
| `OLLAMA_URL`  | `http://localhost:11434` | endereço do Ollama                                                      |
| `EMBED_MODEL` | `bge-m3`                 | modelo que gera os vetores                                              |
| `CHAT_MODEL`  | `qwen3:8b`               | modelo que reescreve a pergunta e escreve a resposta                    |
| `THINK`       | `False`                  | `True` faz o qwen3 raciocinar antes de responder: melhor, bem mais lento |
| `NUM_CTX`     | `8192`                   | contexto do modelo; artigos longos (39, 51) não cabem nos 4096 padrão   |
| `TOP_K`       | `5`                      | quantos artigos são enviados ao modelo                                  |
| `DATA_DIR`    | `data/`                  | onde ficam o cache da lei, o índice e o banco                           |

Trocar `EMBED_MODEL` exige rodar `cdc-rag index` de novo, porque os vetores antigos não
são compatíveis com o novo modelo.

## Dados

Tudo em `data/`, criado na primeira execução:

| Arquivo         | Conteúdo                                                   |
| --------------- | ---------------------------------------------------------- |
| `cdc.htm`       | cópia da página do Planalto                                |
| `articles.json` | artigos extraídos (`id` e `text`)                          |
| `vectors.npy`   | um vetor normalizado por artigo, na mesma ordem do JSON    |
| `rag.db`        | SQLite com o histórico (`questions`) e os casos de teste (`test_cases`) |

`cdc-rag index` refaz `articles.json` e `vectors.npy` a partir do `cdc.htm` e não mexe no
`rag.db`. Para baixar a lei de novo (por exemplo, depois de uma alteração legislativa),
apague `data/cdc.htm` antes de indexar.

## API HTTP

Disponível com `cdc-rag web`. A documentação interativa gerada pelo FastAPI fica em
`http://127.0.0.1:8000/docs`.

| Método | Rota            | Retorno                                            |
| ------ | --------------- | -------------------------------------------------- |
| GET    | `/`             | interface web                                      |
| GET    | `/api/articles` | todos os artigos: `[{"id": "Art. 49", "text": "..."}]` |
| GET    | `/api/history`  | as 20 perguntas mais recentes                      |
| POST   | `/api/ask`      | resposta em streaming (NDJSON)                     |

`POST /api/ask` recebe `{"question": "..."}`, com 1 a 1000 caracteres, e devolve uma linha
JSON por evento:

```
{"sources": ["Art. 49", "Art. 35", "Art. 41", "Art. 54-F", "Art. 54-G"]}
{"chunk": "Sim. Pelo art. 49 do CDC, "}
{"chunk": "você pode desistir da compra..."}
```

A primeira linha traz os artigos consultados, e as seguintes trazem os pedaços da
resposta. Se o Ollama cair no meio, a última linha é `{"error": "..."}`. Se ele já estiver
fora do ar no início, a resposta é `503`. Pergunta vazia ou longa demais retorna `422`.

## Estrutura

```
src/
├── cli.py               comandos do terminal; único lugar que monta as dependências
├── config.py            URLs, modelos e caminhos
├── domain/
│   ├── models.py        Article e ServiceError
│   ├── interfaces.py    contratos (Protocol) que o domínio usa
│   └── rag.py           indexação, busca e resposta
├── repositories/
│   ├── numpy_store.py   artigos em JSON, vetores em .npy, busca por cosseno
│   └── sqlite_db.py     histórico de perguntas e casos de teste
├── infra/
│   ├── ollama.py        embeddings e chat pela API HTTP do Ollama
│   └── planalto.py      download e extração dos artigos
└── web/
    ├── api.py           rotas FastAPI
    └── static/          index.html, style.css, app.js, api.js, format.js
tests/
data/
```

`domain/` não importa nada de fora dele. `repositories/` e `infra/` implementam as
interfaces de `domain/interfaces.py`, e `cli.py` liga as peças. Assim o domínio é testado
com implementações falsas (`tests/fakes.py`), sem Ollama, sem disco e sem rede.

## Testes

Rode a partir da raiz do projeto, com o ambiente ativado:

```
python -m tests.test_rag
python -m tests.test_api
python -m tests.test_sqlite
python -m tests.test_planalto
node --test tests/test_format.mjs
```

Esses não precisam do Ollama. O teste de busca precisa:

```
python -m tests.test_retrieval
```

Ele usa os casos cadastrados em `data/rag.db` e verifica se, para cada pergunta, o artigo
esperado aparece entre os 5 encontrados. Para cadastrar um caso:

```
cdc-rag caso "comprei pela internet, posso desistir?" "Art. 49"
```

Cadastrar a mesma pergunta de novo substitui o artigo esperado. O artigo segue o formato
`Art. 26` ou `Art. 54-A`.

## Problemas comuns

**`Ollama não está rodando. Inicie com: ollama serve`**
O Ollama não respondeu em `OLLAMA_URL`. Rode `ollama serve` em outro terminal.

**`Erro do Ollama: ... Baixou o modelo? ollama pull qwen3:8b`**
O modelo não foi baixado. Rode o `ollama pull` indicado na mensagem.

**`Não consegui baixar a lei do Planalto`**
Sem internet ou site fora do ar. Tente de novo mais tarde. Depois do primeiro download, a
cópia em `data/cdc.htm` é usada e a internet não é mais necessária.

**`Só N artigos extraídos; o layout da fonte mudou?`**
A página do Planalto mudou de formato e a extração encontrou menos de 100 artigos. O
índice antigo não é sobrescrito. O ajuste é em `src/infra/planalto.py`.

**`cdc-rag: command not found`**
O ambiente virtual não está ativo. No VS Code, escolha o interpretador do projeto em
"Python: Select Interpreter" e abra um terminal novo.

**Resposta muito lenta**
A primeira pergunta carrega o modelo na memória e demora mais. Se `THINK` estiver `True`,
o modelo raciocina antes de responder; volte para `False` para respostas mais rápidas.

## Limitações

- As respostas vêm de um modelo de linguagem local e podem conter erros. Confira sempre
  o artigo citado antes de tomar qualquer decisão. Isso não substitui orientação jurídica.
- Só o CDC está indexado. Leis complementares, decretos e jurisprudência ficam de fora.
- O modelo recebe apenas os 5 artigos mais próximos da pergunta. Se o artigo certo não
  estiver entre eles, a resposta tende a dizer que não encontrou base no CDC.
- O servidor web foi feito para uso local por uma pessoa: escuta só em `127.0.0.1` e usa
  uma única conexão SQLite.
# cdc-rag
