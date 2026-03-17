# 🚀 Uso

## Download de transcrições

```bash
# Listar idiomas disponíveis
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" --list-langs

# Baixar como texto simples
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/"

# Baixar como Markdown para Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" --format obsidian

# Obsidian + timestamps + arquivo mesclado + idioma
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --timestamps --merge --lang pt

# Salvar direto no vault do Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --output ~/Obsidian/Vault/Cursos
```

---

## Enriquecimento com IA

Transforma as transcrições brutas em notas de estudo visuais e didáticas: headings com emojis, seções escaneáveis, blocos de código, callouts e perguntas de revisão.

```bash
# Groq (gratuito, recomendado)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider groq

# Groq com modelo mais rápido (limites mais altos)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider groq --model llama-3.1-8b-instant

# Groq com delay maior para não bater rate limit
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider groq --delay 5

# Gemini (gratuito, modelos Google)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider gemini

# Gemini com modelo mais capaz (limite menor: 100 RPD)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider gemini --model gemini-2.5-pro --delay 10

# Ollama (local, gratuito, mais lento)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider ollama

# Claude (pago, melhor qualidade)
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider claude

# Preview sem alterar nenhum arquivo
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/MeuCurso" \
  --provider groq --dry-run
```

### Comportamento do enricher

- Arquivos já enriquecidos são **pulados automaticamente** (idempotente)
- Se receber rate limit (429), **espera automaticamente** e retenta
- Se o limite diário for atingido, rode no dia seguinte — continua de onde parou
- Arquivos especiais (`_MOC.md`, `_index.md`) são ignorados
- Cada arquivo recebe marcador `<!-- enriched-by: provider/model -->`

### Re-enriquecer uma aula

Se quiser rodar novamente com outro provider ou após atualizar o prompt, delete o marcador do final do arquivo:

```
<!-- enriched-by: groq/llama-3.3-70b-versatile -->
```

Remova essa linha e rode o enrich novamente.

---

## Pipeline completo (exemplo real)

```bash
# 1. Configurar cookies (uma vez)
python -m udemy_transcripter --setup

# 2. Baixar e formatar para Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/docker-zero-a-profissional/" \
  --format obsidian --merge --lang pt

# 3. Enriquecer com IA
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/Docker Zero a Profissional" \
  --provider groq --delay 5

# 4. Abrir no Obsidian e estudar 🎉
```

Para 127 aulas com Groq gratuito (70B), pode levar 2-3 dias. Dicas:

- Use `--delay 5` para evitar rate limit por minuto
- Combine providers: metade com Groq, metade com Gemini
- Ou use `--model llama-3.1-8b-instant` (limites mais altos, qualidade um pouco menor)