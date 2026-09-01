# Contribuindo

Código, testes, UX e visão computacional são bem-vindos. Leia o [README](README.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) antes de alterar o pipeline.

## Antes de começar

1. Procure uma issue existente.
2. Mudança grande: descreva a proposta primeiro.
3. Não publique imagens de pessoas, credenciais, URLs de câmera com senha ou dados de ambiente privado.

## Ambiente

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python server.py --source demo/demo.mp4
```

## Onde ajudar

- classificador treinado (`com_epi` / `sem_epi` / `uso_incorreto`)
- testes com vídeos fixos e métricas de erro
- exportação ONNX/OpenVINO
- várias câmeras
- acessibilidade do painel
- telemetria local sem dado pessoal

## Regras de implementação

- Mantenha captura, inferência e encoder em threads separadas.
- Não bloqueie o stream aguardando o modelo.
- OpenCV usa BGR, não RGB.
- Contratos de `/video_feed`, `/stats` e `/health` mudam só com atualização de [docs/API.md](docs/API.md) e do front.
- Parâmetros ajustáveis ficam em `config.py`.
- Não mostre cobertura HSV como confiança.
- O painel deve continuar cabendo na viewport (`100dvh`).
- Logs e HTML não podem vazar senha de RTSP.

## Validação

```bash
ruff check .
ruff format --check .
pytest
```

Mudança no detector: teste colete correto, pessoa sem colete, colete só em um braço, objeto fluorescente, movimento, baixa luz e oclusão.

Mudança de desempenho: informe FPS de stream, inferências/s, hardware e resolução.

## Pull request

Inclua problema, abordagem, testes rodados, impacto em precisão/desempenho e documentação atualizada. Evidências visuais devem estar anonimizadas.

## Dataset

`dataset_epi/raw/` é ignorado pelo Git. Não remova essa proteção.

## Licença

O projeto foi criado por Henrique Erdei e está sob licença MIT. Ao contribuir, o material enviado precisa poder ser redistribuído nessa licença.
