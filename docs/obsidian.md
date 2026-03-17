# 📝 Formato Obsidian

## Saída do download (`--format obsidian`)

O formatter Obsidian gera notas `.md` otimizadas para estudo:

- **Frontmatter YAML** — funciona com Dataview (`course`, `section`, `tags`, `date`)
- **Tags automáticas** — `#udemy`, `#curso/nome-do-curso`, `#secao/nome-da-secao`
- **Navegação** — wikilinks `⬅ [[anterior]] | [[próxima]] ➡`
- **MOC (Map of Content)** — `_MOC.md` com links para todas as notas
- **Índice por seção** — `_index.md` com lista numerada de aulas
- **Área de anotações** — espaço reservado para notas pessoais

---

## Estrutura de saída

```
udemy_transcripts/
└── Docker Zero a Profissional/
    ├── _MOC.md                     # Map of Content (links para tudo)
    ├── _CURSO_COMPLETO.md          # (com --merge)
    ├── _metadata.json
    ├── 01 - Primeiros Passos/
    │   ├── _index.md               # Índice da seção
    │   ├── 014 - Instalando o Docker.md
    │   └── 015 - O que sao Containers.md
    └── 02 - Construindo Imagens/
        ├── _index.md
        ├── 027 - Entendendo Layers.md
        └── 028 - Criando seu primeiro Dockerfile.md
```

---

## Estilo após enriquecimento

Após rodar `--enrich`, as notas são transformadas em material didático visual:

### Elementos visuais

| Elemento | Descrição |
|----------|-----------|
| `# 📚 Visão Geral da Aula` | Resumo do tema em 1-2 parágrafos |
| `# 🎯 Objetivos` | O que o aluno vai aprender |
| `# 🧠 Conceitos` | Conteúdo principal organizado por tópicos |
| `# 👨‍🏫 Sobre o Instrutor` | Se a aula apresentar alguém |
| `# 🧾 Resumo da Aula` | 3-5 bullet points com lições principais |
| `# 🔁 Perguntas para Revisão` | 3-5 perguntas para fixação |
| `# ✍️ Anotações` | Espaço vazio para o aluno |

### Callouts do Obsidian

```markdown
> [!tip] Dica prática
> Use Docker Compose para orquestrar múltiplos containers.

> [!warning] Atenção
> Não esqueça do .dockerignore para evitar enviar node_modules.

> [!info] Importante
> Containers compartilham o kernel do host, diferente de VMs.

> [!example] Exemplo
> Uma aplicação com backend, banco e cache como 3 serviços no Compose.
```

### Separadores e escaneabilidade

- `---` entre todas as seções principais
- Blocos curtos de 5-8 linhas (sem paredes de texto)
- Um conceito por subseção `###`
- Bullet points curtos com termos em **negrito**
- ✅/❌ para indicar foco vs fora do escopo

---

## Exemplo: antes e depois

### Antes (transcrição bruta)

```markdown
## Transcrição

Muito bem vindo ao curso de Docker de zero a profissional para
desenvolvimento web. Este curso é o curso que te vai levar
definitivamente ao conhecimento do uso desta tecnologia enquanto
programador, mas obviamente contém muitos conteúdos que te poderão
preparar para um outro tipo de funções, como é o caso de DevOps...
```

### Depois (enriquecido)

```markdown
---

# 📚 Visão Geral da Aula

Esta aula apresenta o **objetivo do curso**, o **perfil do instrutor**
e explica **o que será aprendido ao longo do treinamento**.

O foco do curso é ensinar **Docker para desenvolvedores web**,
principalmente para criar **ambientes de desenvolvimento local**.

---

# 🎯 Objetivos do Curso

Ao final do curso você será capaz de:

- Entender **o que é Docker e suas vantagens**
- Instalar Docker em Windows, Mac e Linux
- Trabalhar com **comandos básicos da CLI**
- Criar e utilizar **Dockerfiles**
- Gerenciar Images, Containers, Volumes e Networks
- Orquestrar ambientes com **Docker Compose**

---

# ⚙️ Foco do Curso

✅ Uso do Docker **no ambiente local**
✅ **Desenvolvimento web**
✅ **Aprendizado prático**

❌ Deploy em cloud
❌ Infraestrutura em AWS/Azure

---

# 🧾 Resumo da Aula

- Docker será ensinado **do zero ao nível profissional**
- O foco é **desenvolvimento web**
- O curso é **prático e conceitual**
- Pode servir de base para evoluir para **DevOps**

---

# 🔁 Perguntas para Revisão

1. Qual é o principal objetivo do curso?
2. O que são **Docker Images**?
3. Para que serve o **Docker Compose**?

---

# ✍️ Anotações

> [!note] Espaço para suas anotações
>
> -
> -
> -
```

---

## Dicas para o Obsidian

### Plugins recomendados

- **Dataview** — para queries no frontmatter (`course`, `tags`, `section`)
- **Templater** — para templates de anotações
- **Outline** — para navegar pelos headings com emojis

### Query Dataview de exemplo

```dataview
TABLE section, lecture
FROM #curso/docker-zero-a-profissional
SORT lecture ASC
```