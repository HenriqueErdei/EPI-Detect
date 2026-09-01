# Contexto técnico (handoff)

Para quem for alterar o código — incluindo agentes. Documentação humana: [README.md](README.md) e [docs/](docs/README.md).

## Estado

Protótipo de portfólio/demo. Detecta pessoas e sinaliza colete por HSV no torso. Não há dataset validado em escala, métricas de campo nem certificação de SST.

Fluxo: `yolov8n-pose.pt` → recorte de torso em `core/detector.py` → limiares `VEST_THRESH` / `VEST_SIDE_THRESH` / `VEST_SPAN_THRESH` → voto temporal por IoU.

O painel público só troca a fonte para RTSP. O loop de demo (`demo/demo.mp4`) sobe pelo CLI ou systemd.

O próximo salto de qualidade é um classificador leve treinado em recortes reais de torso. HSV fica como apoio.

## Não quebre

- Captura, detecção e encode em threads distintas (`server.py`). Inferência fora do loop de JPEG.
- LIVE (webcam/RTSP) usa frame mais recente; arquivo FILE lê em sequência e dá loop.
- Front em `templates/index.html`, sem bundler. IDs do JS e `object-fit: contain` no `#stream`.
- Azul = colete; laranja = sem colete. Cobertura HSV não é confiança.
- `POST /source` recusa upload, webcam e HTTP.
- Layout em `100dvh`, sem scroll da página.
- OpenCV = BGR. Azul `#4f8cff` → `(255, 140, 79)`. Laranja `#f08c2a` → `(42, 140, 240)`.
- Nada de nomes, e-mails, empresas, caminhos de usuário, credenciais ou URL RTSP com senha no Git.
- `dataset_epi/raw/` e `uploads/` permanecem fora do versionamento.

Detalhes do pipeline: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Contrato HTTP: [docs/API.md](docs/API.md).

## Validação mínima

1. `python -m py_compile server.py detect.py config.py core/*.py`
2. `python server.py --source demo/demo.mp4` (ou webcam / RTSP)
3. `/video_feed` abre enquanto o modelo ainda carrega
4. `/stats` responde durante a operação
5. Colete correto, sem colete, colete em um braço só
6. `POST /source` com arquivo ou webcam devolve `400`
7. RTSP: senha não aparece no HTML nem no stdout

## Roadmap

1. Dataset autorizado e separado por pessoa/sessão.
2. Recortes de torso a partir dos keypoints.
3. Treino `com_epi` / `sem_epi` / `uso_incorreto`.
4. HSV como fallback.
5. ONNX/OpenVINO e medição de latência.
6. Testes com vídeos fixos e taxas de FP/FN.

Fora de escopo: autenticação, banco, alertas externos, decisão legal automática.
