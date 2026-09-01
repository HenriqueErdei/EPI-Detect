# Implantação

## Forma suportada: demo local

```bash
python server.py --source demo/demo.mp4 --port 5000
python server.py --source webcam --port 5000
python server.py --source 'rtsp://usuario:senha@host:8554/camera'
```

Host padrão: `127.0.0.1`. Acesse só em http://localhost:5000.

Não use `--host 0.0.0.0` sem os controles abaixo. O Flask embutido não oferece autenticação, HTTPS, limite de requisição nem isolamento da câmera.

## Loop de demo

`demo/*.mp4` está no `.gitignore`. No servidor, aponte o processo para `demo/demo.mp4`.

## systemd (exemplo)

Unit de referência em [`deploy/epi-detect.service`](../deploy/epi-detect.service). Ajuste caminhos, usuário e porta. O processo deve escutar só em `127.0.0.1`.

```bash
sudo cp deploy/epi-detect.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now epi-detect
```

Na frente, use um proxy (Nginx) com HTTPS se a demo for pública. Não exponha o Flask direto na internet.

## Stream RTSP

- Prefira aspas no comando para o shell não quebrar o URL.
- A captura usa FFmpeg com `rtsp_transport=tcp` e lê sempre o frame mais recente.
- Se o stream cair, o modo `LIVE` tenta reabrir.
- Firewall e VPN da rede da câmera precisam permitir a porta RTSP (em geral 554 ou 8554).
- Não grave o URL com senha em script versionado, issue ou README.

## O que falta antes de rede interna

1. Autenticação e autorização.
2. Proxy reverso com HTTPS.
3. Restrição de quem pode ver o MJPEG.
4. Política de retenção e privacidade das imagens.
5. Processo sem privilégio de administrador.
6. Logs sem dado pessoal e sem senha de câmera.
7. Monitoramento de `/health`.
8. Validação do modelo no ambiente real (iluminação, distância, tipo de colete).
9. Revisão de licenças dos pesos YOLO e das dependências.

## Desempenho em CPU

Captura, inferência e encoder já são independentes. Se o painel engasgar, ajuste nesta ordem:

1. `INPUT_SIZE`
2. `DETECTION_INTERVAL`
3. resolução da webcam (`WEBCAM_WIDTH` / `WEBCAM_HEIGHT`)
4. `TORCH_THREADS`

Meça `fps` e `det_fps` em `/stats`. Para produção futura, compare PyTorch com ONNX/OpenVINO.
