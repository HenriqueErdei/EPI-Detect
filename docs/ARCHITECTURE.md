# Arquitetura

O objetivo é manter o painel fluido em CPU: a câmera não espera o YOLO, e o JPEG não espera a inferência.

## Pipeline

```text
fonte (webcam / arquivo / RTSP)
        │
        ▼
  captura          → raw_frame (sempre o mais recente, em LIVE)
        │
        ▼
  detecção         → YOLO Pose + HSV no torso + voto temporal
        │
        ▼
  encode           → overlay OpenCV + JPEG a STREAM_FPS
        │
        ▼
  Flask            → página, MJPEG, /stats, /health
```

`server.py` guarda o estado em um dicionário protegido por lock.

| Thread | Função |
|---|---|
| `_capture_loop` | abre a fonte, atualiza `raw_frame`, reconecta em LIVE |
| `_detect_loop` | analisa só o frame mais recente |
| `_encode_loop` | desenha overlays e gera o JPEG |
| Flask | entrega HTML, stream e métricas |

Não execute inferência dentro do loop de renderização. Isso trava o vídeo.

Arquivos de vídeo (`FILE`) são lidos em sequência e reiniciam no fim. Webcam e RTSP usam uma thread extra para descartar frames atrasados (buffer da câmera/rede). RTSP prefere transporte TCP via FFmpeg. A origem pode ser trocada em runtime por `POST /source`.

## Mapa de arquivos

| Caminho | Papel |
|---|---|
| `server.py` | Flask, concorrência, rotas |
| `detect.py` | janela OpenCV, opcional `--save` |
| `config.py` | modelo, HSV, desempenho, cores |
| `core/capture.py` | `VideoCapture`, `parse_source`, URLs de rede |
| `core/detector.py` | YOLO Pose e regra do colete |
| `core/display.py` | bounding box, esqueleto, labels |
| `templates/index.html` | painel (HTML/CSS/JS, sem bundler) |
| `dataset_epi/raw/` | imagens locais, ignoradas pelo Git |
| `models/` | pesos opcionais, ignorados pelo Git |

## Como a classificação funciona

1. `yolov8n-pose.pt` encontra pessoas e keypoints.
2. O recorte do torso vai do pescoço (`TORSO_TOP`) ao quadril (`TORSO_BOTTOM`).
3. Máscaras HSV procuram laranja e amarelo-limão.
4. `has_vest=True` só se a cobertura total e os dois lados passam dos limiares, e a maioria das últimas análises da mesma pessoa concorda (IoU).

Isso reduz falso positivo de faixa num braço só. Não reconhece o formato do colete. Cobertura HSV não deve ser exibida como “confiança”.

## Contrato do front-end

Flask renderiza `templates/index.html`. Não há etapa de build.

| Rota | Uso no painel |
|---|---|
| `GET /` | HTML; recebe `mode` e `source_label` (nome da câmera, sem senha) |
| `GET /video_feed` | MJPEG |
| `GET /stats` | JSON a cada 500 ms (`mode`, `source_label`) |
| `GET /health` | overlay de carregamento / erro |
| `POST /source` | troca stream, webcam ou arquivo |

Ao alterar a interface:

- preserve os IDs do JavaScript ou atualize o script junto
- mantenha `object-fit: contain` no `#stream` (boxes alinhados ao vídeo)
- azul = EPI ok; laranja = ausência / uso incorreto
- o layout deve caber em `100dvh` sem scroll da página
- mostre estado enquanto o modelo carrega

OpenCV usa BGR. Azul de conformidade `#4f8cff` é `(255, 140, 79)`. Laranja de alerta `#f08c2a` é `(42, 140, 240)`.

## Desempenho de referência

Em uma máquina de desenvolvimento com quatro processadores lógicos:

- webcam 960×540
- entrada YOLO 416
- stream ~18–20 FPS
- detecção ~3–5 análises/s
- PyTorch com 2 threads

São referência, não garantia. Depois de mudar `config.py`, compare `/stats`.

## Fora do escopo desta versão

Autenticação, banco de eventos, várias câmeras simultâneas, notificações externas e qualquer decisão legal automática.
