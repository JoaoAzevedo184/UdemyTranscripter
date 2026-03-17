# ⚙️ Configuração

O projeto usa um arquivo `.env` na raiz para armazenar credenciais.

```bash
# Setup interativo (recomendado)
python -m udemy_transcripter --setup

# Ou copie o template e preencha manualmente
cp .env.example .env
```

## Cookies da Udemy (obrigatório para download)

Os cookies autenticam suas requisições à API da Udemy.

**Como obter:**

1. Acesse [udemy.com](https://udemy.com) e faça login
2. Abra o **DevTools** (`F12`) → aba **Network**
3. Recarregue a página de qualquer curso
4. Clique em alguma requisição para `www.udemy.com`
5. Em **Request Headers**, copie o valor completo do header **`Cookie`**

**No `.env`:**

```env
UDEMY_COOKIES='access_token=xxx; cf_clearance=yyy; client_id=zzz; ...'
```

> ⚠️ Nunca compartilhe seus cookies. Eles dão acesso à sua conta.
> Cookies expiram periodicamente — se der erro 403, gere novos.

---

## Groq (recomendado — gratuito, ultra-rápido)

**Como obter:**

1. Acesse [console.groq.com](https://console.groq.com)
2. Crie conta (pode ser com Google, sem cartão de crédito)
3. Vá em **API Keys** → **Create API Key**
4. Copie a chave (começa com `gsk_`)

**No `.env`:**

```env
GROQ_API_KEY=gsk_sua_chave_aqui
```

**Modelos disponíveis:**

| Modelo | Tokens/min | Tokens/dia | Uso |
|--------|:---:|:---:|---|
| `llama-3.3-70b-versatile` | ~6.000 | ~500.000 | Melhor qualidade |
| `llama-3.1-8b-instant` | ~30.000 | maior | Mais rápido |
| `deepseek-r1-distill-llama-70b` | ~6.000 | ~500.000 | Raciocínio/código |

**Rate limits:** Os limites resetam diariamente. Se atingir, espere o dia seguinte e rode novamente — os arquivos já processados são pulados. O enricher tenta automaticamente esperar quando recebe erro 429.

**Dicas para 127+ aulas:**

- Use `--delay 5` para espaçar chamadas
- Use `--model llama-3.1-8b-instant` para limites mais altos
- Pode levar 2-3 dias no tier gratuito com o modelo 70B

---

## Google Gemini (gratuito, alternativa)

**Como obter:**

1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Faça login com conta Google
3. Clique em **Get API Key** → **Create API Key**
4. Copie a chave (começa com `AIzaSy`)

**No `.env`:**

```env
GEMINI_API_KEY=AIzaSy_sua_chave_aqui
```

**Modelos disponíveis:**

| Modelo | RPM | RPD | Uso |
|--------|:---:|:---:|---|
| `gemini-2.5-flash` (padrão) | 10 | 500 | Equilíbrio |
| `gemini-2.5-pro` | 5 | 100 | Máxima qualidade |
| `gemini-2.5-flash-lite` | 15 | 1.000 | Volume alto |

**Rate limits:** Resetam à meia-noite (horário do Pacífico). Mesma lógica do Groq.

---

## Ollama (gratuito, local)

Roda no seu próprio hardware. Sem limites, sem internet, sem custos.

```bash
# Instalar modelo (uma vez)
ollama pull llama3.1          # 8B, ~5GB
ollama pull qwen3.5:9b        # 9B, ~6.6GB (recomendado)
ollama pull qwen2.5-coder:7b  # 7B, melhor pra código
```

Não precisa de API key. O enricher se conecta automaticamente em `http://localhost:11434`.

**Requisitos de hardware:**

| Modelo | RAM mínima |
|--------|:---:|
| Llama 3.1 8B (Q4) | ~8 GB |
| Qwen 3.5 9B (Q4) | ~10 GB |
| Qwen 2.5 14B (Q4) | ~12 GB |

**Ollama em outra máquina da rede:**

```bash
--provider ollama --ollama-url http://192.168.1.100:11434
```

---

## Claude / Anthropic (pago)

Necessário somente se quiser a máxima qualidade. Requer créditos pagos.

**Como obter:**

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Crie uma conta ou faça login
3. Vá em **Settings** → **API Keys** → **Create Key**
4. Copie a chave (começa com `sk-ant-`)
5. Adicione créditos em **Plans & Billing** (mínimo $5)

**No `.env`:**

```env
ANTHROPIC_API_KEY=sk-ant-api03-sua-chave-aqui
```

**Modelos:**

| Modelo | Custo (input/output) | Uso |
|--------|---|---|
| `claude-sonnet-4-20250514` (padrão) | ~$3/$15 por MTok | Equilíbrio |
| `claude-haiku-4-5-20251001` | ~$1/$5 por MTok | Econômico |
| `claude-opus-4-6` | ~$5/$25 por MTok | Máxima qualidade |

Custo estimado para ~100 aulas: **$0.50–$2.00** com Sonnet.

**Ordem de resolução da API key:**

1. Flag `--api-key` na CLI
2. Variável no `.env`
3. Variável de ambiente do sistema

---

## Resumo

| Provider | Custo | Velocidade | Qualidade | API Key |
|----------|:---:|:---:|:---:|---|
| **Groq** | Gratuito | Ultra-rápido | Alta | `GROQ_API_KEY` |
| **Gemini** | Gratuito | Rápido | Alta | `GEMINI_API_KEY` |
| **Ollama** | Gratuito | Lento (local) | Boa | Não precisa |
| **Claude** | Pago | Rápido | Excelente | `ANTHROPIC_API_KEY` |