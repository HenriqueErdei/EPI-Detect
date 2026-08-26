# Changelog

## [1.2.0] — 2026-08-26

### Adicionado
- Fontes RTSP/HTTP ao vivo (`--source rtsp://...`), com TCP e reconexão
- Rótulo da câmera no painel sem expor senha
- Botão Fonte no painel (URL RTSP/HTTP ou upload de MP4)
- Documentação reorganizada (README, arquitetura, API, implantação, model card)

### Removido
- Modo `demo` e o pré-render `render_demo.py`

### Alterado
- Painel em tela cheia, visual de sala de controle, sem scroll da página
- Tema azul-marinho; azul para colete e laranja para ausência de EPI
- Captura de stream de rede usa o frame mais recente (mesmo padrão da webcam)

## [1.1.0] — 2026-08-21

### Alterado
- Pipeline assíncrono para separar captura, inferência e stream
- Evidência bilateral para rejeitar colete em apenas um braço
- Estabilização temporal por pessoa
- Ajustes de desempenho para CPU e stream de 20 FPS
- Cor de ausência/uso incorreto corrigida para vermelho em BGR
- Documentação e higienização de dados para publicação
- Estados explícitos de carregamento e erro no dashboard
- Endpoint de saúde e contrato formal da API
- Testes automatizados, Ruff e CI com GitHub Actions
- Licença MIT e documentação de limitações do modelo

## [1.0.0] — 2026-08-21

### Adicionado
- Detecção de pessoas com YOLOv8n Pose em tempo real
- Análise HSV para coletes laranja e amarelo high-vis
- Overlay com bounding boxes, labels e barra de status
- Suporte a webcam e vídeo via argparse
- Captura em thread (sem I/O bloqueante no loop principal)
- Exportação de vídeo processado com `--save`
