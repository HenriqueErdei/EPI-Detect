# EPI Detect

Monitoramento em tempo real do uso de **colete de segurança**. O sistema localiza pessoas na cena, analisa o torso e mostra o resultado em um painel web: quem está com EPI, quem não está, taxa de conformidade e eventos.

**Criado por Henrique Erdei.**

> **Protótipo.** A classificação atual combina YOLO Pose com regras de cor em HSV. Serve como apoio operacional, não como decisão automática de segurança do trabalho.

## O que faz

1. Lê webcam, arquivo de vídeo ou stream RTSP/HTTP.
2. Detecta pessoas com YOLO Pose.
3. Recorta o torso e procura laranja/amarelo fluorescente (HSV), nos dois lados.
4. Estabiliza o resultado no tempo para reduzir oscilação.
5. Exibe o vídeo e os indicadores em `http://localhost:5000`.

Captura, inferência e transmissão rodam em threads separadas. O painel continua fluindo mesmo quando a detecção é mais lenta.

## Requisitos

- Python 3.10 ou superior
- CPU suficiente (GPU não é obrigatória)
- Webcam, arquivo `.mp4` ou URL RTSP/HTTP
- Windows, Linux ou macOS com OpenCV

## Instalação

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Na primeira execução a Ultralytics baixa `yolov8n-pose.pt`. Pesos `.pt` não entram no Git.

## Como executar

Dashboard (abre o navegador em `http://localhost:5000`):

```bash
python server.py --source webcam
python server.py --source videos-teste/exemplo.mp4
python server.py --source 'rtsp://usuario:senha@host:8554/camera'
```

No painel, o botão **Fonte** troca a origem sem reiniciar: cole o link da stream ou escolha um MP4 do computador.

Opções úteis: `--port 5000`, `--host 127.0.0.1`, `--no-browser`.

Modo desktop (janela OpenCV, sem Flask):

```bash
python detect.py --source webcam
python detect.py --source videos-teste/exemplo.mp4 --save resultado.mp4
```

No Windows, `iniciar.bat` sobe o painel. A fonte (stream ou arquivo) é escolhida no navegador.

Coloque URLs entre aspas no shell. Não commite usuário, senha ou endereço interno de câmera.

### Fontes aceitas

| Origem | Modo | Comportamento |
|---|---|---|
| `webcam` ou `0` | LIVE | câmera local, frame mais recente |
| `1`, `2`, … | LIVE | outro índice de câmera |
| `rtsp://` / `http://` | LIVE | stream de rede, TCP, reconexão se cair |
| arquivo MP4 (CLI ou upload) | FILE | vídeo em loop |

Uploads do painel vão para `uploads/` (ignorado pelo Git). Não versione vídeos com pessoas ou ambientes privados.

## Painel

O dashboard ocupa a tela inteira. O vídeo fica no centro; à direita (ou abaixo, em telas estreitas) aparecem:

- pessoas com colete, sem colete e total
- taxa de conformidade
- eventos com horário
- FPS de transmissão (TX) e de detecção (DET)

Azul = colete detectado. Laranja = ausência ou uso insuficiente. A cobertura HSV **não** é confiança percentual do modelo.

## Configuração

Ajustes em [`config.py`](config.py):

| Parâmetro | Função |
|---|---|
| `INPUT_SIZE` | resolução enviada ao YOLO |
| `DETECTION_INTERVAL` | intervalo entre inferências |
| `STREAM_FPS` | FPS alvo do JPEG no painel |
| `TORCH_THREADS` | threads do PyTorch |
| `VEST_THRESH` | cobertura fluorescente mínima no torso |
| `VEST_SIDE_THRESH` | cobertura mínima em cada lado |
| `ORANGE_*` / `YELLOW_*` | faixas HSV do colete |

## Estrutura

```text
EPI-Detect/
├── server.py             # Flask, pipeline e rotas
├── detect.py             # modo desktop
├── config.py             # parâmetros
├── core/                 # captura, detector, overlay
├── templates/index.html  # painel (sem build step)
├── tests/                # pytest
├── uploads/              # MP4 enviados pelo painel (ignorado)
└── docs/                 # documentação técnica
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | pipeline, arquivos e contrato do front |
| [docs/API.md](docs/API.md) | `GET /`, `/video_feed`, `/stats`, `/health`, `POST /source` |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | execução local e o que falta para rede |
| [docs/MODEL_CARD.md](docs/MODEL_CARD.md) | o que o modelo faz e o que não faz |
| [CONTRIBUTING.md](CONTRIBUTING.md) | como contribuir |
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | handoff técnico para quem for alterar o código |

## Testes

```bash
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest
```

Confira também, com o servidor no ar:

- http://localhost:5000
- http://localhost:5000/video_feed
- http://localhost:5000/stats
- http://localhost:5000/health

## Limitações

- Iluminação, distância, compressão de CFTV e roupas fluorescentes alteram o resultado.
- Não há métricas de campo nem modelo treinado no formato do colete.
- O Flask desta versão é local: sem autenticação, HTTPS ou histórico persistente.

## Privacidade

Não versione imagens de pessoas, `.env`, tokens, vídeos privados ou URLs com senha. Confirme autorização antes de apontar uma câmera real. Detalhe em [SECURITY.md](SECURITY.md).

## Autoria e licença

Criado por **Henrique Erdei**.

MIT. Copyright © 2026 Henrique Erdei. Veja [LICENSE](LICENSE).
