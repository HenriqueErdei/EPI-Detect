# API HTTP

Contrato do Flask usado pelo painel. Não há versionamento (`/v1`). Mudança incompatível deve atualizar este arquivo e `templates/index.html` no mesmo pull request.

O servidor escuta `127.0.0.1:5000` por padrão. Não há autenticação, CORS configurado nem HTTPS.

## Estados do pipeline

| `status` | Significado |
|---|---|
| `starting` | processo subindo |
| `waiting_camera` | a fonte ainda não entregou frame |
| `loading_model` | câmera ok, YOLO carregando |
| `running` | câmera e modelo operacionais |
| `error` | falha; veja `error` em `/stats` |

Os contadores de pessoas refletem a **última inferência**, não cada frame exibido.

## `GET /`

Dashboard HTML. `200 text/html`.

O template recebe:

- `mode`: `LIVE` ou `FILE`
- `source_label`: rótulo curto da fonte (`Webcam`, nome do arquivo, último segmento do RTSP), sem credenciais

## `GET /video_feed`

Stream MJPEG, `Content-Type: multipart/x-mixed-replace; boundary=frame`. A conexão permanece aberta. O primeiro JPEG pode atrasar até a câmera e o encoder ficarem prontos.

```html
<img src="/video_feed" alt="Câmera monitorada">
```

## `GET /stats`

`200 application/json`:

```json
{
  "with_vest": 1,
  "without_vest": 0,
  "total": 1,
  "fps": 20,
  "det_fps": 5,
  "alert": false,
  "status": "running",
  "error": null,
  "mode": "LIVE",
  "source_label": "orion-05-cam-01"
}
```

| Campo | Significado |
|---|---|
| `with_vest` | pessoas com evidência de colete |
| `without_vest` | pessoas sem evidência suficiente (inclui uso incorreto) |
| `total` | pessoas na última inferência |
| `fps` | JPEGs gerados no último segundo (transmissão) |
| `det_fps` | inferências concluídas no último segundo |
| `alert` | `true` quando `without_vest > 0` |
| `status` | estado da tabela acima |
| `error` | mensagem operacional ou `null` |
| `mode` | `LIVE` (câmera/stream) ou `FILE` (arquivo) |
| `source_label` | nome curto da fonte, sem senha |

## `POST /source`

Troca a origem do vídeo sem reiniciar o processo.

JSON:

```json
{ "url": "rtsp://usuario:senha@host:8554/camera" }
```

Também aceita `{ "source": "webcam" }`.

Multipart: campo `file` com vídeo (`.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`), até 500 MB. O arquivo é gravado em `uploads/`.

Resposta `200`:

```json
{ "ok": true, "mode": "LIVE", "source_label": "camera" }
```

`400` se a URL/arquivo for inválido. `413` se o upload passar de 500 MB.

## `GET /health`

Indica se a câmera e o modelo estão no ar. Não mede precisão.

Saudável ou ainda inicializando (`200`):

```json
{
  "ok": true,
  "status": "loading_model",
  "camera_ready": true,
  "model_ready": false
}
```

`503` quando `status` é `error`.

## Segurança

Não exponha esta API na internet. URLs RTSP com senha nunca devem aparecer em JSON, logs ou HTML — o código oculta a senha em mensagens de fonte; não reintroduza o URL completo no front-end.
