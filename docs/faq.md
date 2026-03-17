# ❓ FAQ e Troubleshooting

## Geral

### O projeto é gratuito?

Sim. O download de transcrições e o enriquecimento com Groq, Gemini ou Ollama são 100% gratuitos. Apenas o Claude (Anthropic) requer créditos pagos.

### Funciona com qualquer curso?

Funciona com cursos **que você comprou** e que tenham **legendas/captions** habilitadas pelo instrutor. Cursos sem legendas não terão transcrição disponível.

### Por que tem aulas faltando na numeração?

O `object_index` (001, 002, 015...) é a numeração interna da Udemy que conta **todos** os itens do curso. O script pula itens sem legenda: quizzes, exercícios práticos, artigos e aulas em vídeo sem caption.

---

## Erros de download

### Erro 403 / "Just a moment..."

Isso é a proteção **Cloudflare**. Causas:

1. **Cookies expirados** — copie novos do navegador (DevTools → Network → Cookie header)
2. **Curso não comprado** — verifique se você tem acesso ao curso
3. **Cookies incompletos** — copie o header Cookie **inteiro**, não apenas o access_token

```bash
# Sempre rode com --debug para ver detalhes
python -m udemy_transcripter --url "..." --list-langs --debug
```

### Erro 401

Token inválido ou expirado. Gere novos cookies no navegador.

### O download não pega nenhuma aula

O curso provavelmente não tem legendas/captions. Use `--list-langs` para verificar. Se retornar "Nenhuma legenda disponível", não é possível extrair transcrição.

---

## Erros de enriquecimento

### Groq: "Rate limit exceeded"

Os limites do tier gratuito resetam **diariamente**. Não precisa pagar. Espere até o dia seguinte e rode o mesmo comando — os arquivos já processados serão pulados.

Para minimizar rate limits:
- Use `--delay 5` (ou mais)
- Use `--model llama-3.1-8b-instant` (limites mais altos)
- Combine Groq + Gemini para processar mais por dia

### Claude: "Your credit balance is too low"

A conta da Anthropic não tem créditos. Opções:
- Compre créditos em [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) (mínimo $5)
- Ou use **Groq** ou **Gemini** gratuitamente

### Gemini: "429 Too Many Requests"

Mesmo comportamento do Groq — limites diários. Espere o dia seguinte. O enricher tenta automaticamente esperar e retomar.

### Ollama: "Connection refused"

O serviço Ollama não está rodando:

```bash
# Inicie o Ollama
ollama serve

# Verifique se está rodando
curl http://localhost:11434/api/tags
```

### "unrecognized arguments" com espaços no caminho

Coloque o caminho entre aspas:

```bash
# ❌ Errado
--enrich ./udemy_transcripts/Docker Zero a Profissional

# ✅ Correto
--enrich "./udemy_transcripts/Docker Zero a Profissional"
```

---

## Enriquecimento

### Posso misturar providers?

Sim. Rode metade com Groq, metade com Gemini. O marcador `<!-- enriched-by: -->` impede reprocessamento. Se quiser re-enriquecer com outro provider, delete a linha do marcador no final do arquivo.

### A qualidade do Groq é boa?

Groq roda os mesmos modelos open source (Llama 3.3 70B, DeepSeek R1) que rodariam no Ollama — só em 3-5s em vez de 30-60s. A qualidade é do modelo, não do provider.

### Como re-enriquecer uma aula?

Delete o marcador do final do arquivo `.md`:

```
<!-- enriched-by: groq/llama-3.3-70b-versatile -->
```

Remova essa linha e rode `--enrich` novamente.

### O enricher alterou meu frontmatter!

O system prompt instrui a LLM a preservar o frontmatter, mas modelos menores podem falhar. O código verifica e reconstrói o frontmatter original se necessário. Se persistir, use um modelo maior (70B+).

---

## Obsidian

### Como importar as notas no Obsidian?

Copie a pasta do curso para dentro do seu vault:

```bash
python -m udemy_transcripter \
  --url "..." --format obsidian \
  --output ~/Obsidian/MeuVault/Cursos
```

Ou mova a pasta depois:

```bash
mv ./udemy_transcripts/MeuCurso ~/Obsidian/MeuVault/Cursos/
```

### As tags não aparecem no Obsidian

Verifique se o frontmatter está correto (bloco `---` no início). O Obsidian lê tags do campo `tags:` no YAML. Reinicie o Obsidian se necessário.

### Plugins recomendados

- **Dataview** — queries no frontmatter (listar aulas, filtrar por seção)
- **Templater** — templates para anotações
- **Outline** — navegação pelos headings com emojis