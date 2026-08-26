# Model card

## Uso pretendido

Demonstrar um pipeline de visão em tempo real que **sinaliza** possível uso de colete de segurança em webcam, arquivo ou CFTV.

Não é um sistema certificado de SST, não substitui inspeção humana e não deve punir trabalhadores de forma automática.

## O que o sistema faz

- Localiza pessoas e keypoints com YOLO Pose pré-treinado (`yolov8n-pose.pt`).
- Estima o retângulo do torso.
- Procura cores fluorescentes configuradas em HSV (laranja e amarelo-limão).
- Exige evidência nos dois lados do torso.
- Aplica maioria temporal na mesma pessoa (associação por IoU).

Nesta versão **não** existe um classificador treinado no formato do colete nem na forma correta de vestí-lo.

## Classes operacionais

| Classe | Como aparece hoje |
|---|---|
| `com_epi` | evidência HSV bilateral suficiente → `with_vest` |
| `sem_epi` | evidência insuficiente → `without_vest` |
| `uso_incorreto` | entra no mesmo contador `without_vest` |
| `falso_positivo` | ainda não há dataset publicado para medir |

## Limitações

- Roupa, cone, fita ou fundo fluorescente podem gerar falso positivo.
- Oclusão, contraluz, pessoa de lado e baixa resolução geram falso negativo.
- A regra bilateral pode rejeitar quem é visto bem de perfil.
- A estabilização temporal atrasa um pouco a mudança de estado.
- Limiares foram calibrados em poucos exemplos.
- Não há métricas representativas de campo.

## Métricas

Ainda não publicadas. Não declare acurácia, precisão ou recall sem conjunto de teste separado por pessoa, sessão e ambiente.

O conjunto futuro deve medir pelo menos precisão/recall por classe, matriz de confusão, falso negativo de ausência de colete, falso positivo por objeto fluorescente, latência e FPS por hardware.

## Dados

Imagens locais ficam em `dataset_epi/raw/` (ignorado pelo Git). Use só material autorizado. Separe treino, validação e teste por pessoa ou sessão.

## Uso inadequado

- Punição ou trava automática de acesso.
- Substituição de ronda ou inspeção.
- Alegação de conformidade legal (NR, ISO, etc.).
- Vigilância sem base legal e consentimento.
- Operação crítica sem validação independente no local.

## Próximo passo técnico

Treinar um classificador leve de recorte de torso (`com_epi`, `sem_epi`, `uso_incorreto`), manter HSV como apoio, exportar ONNX/OpenVINO e comparar num conjunto de teste congelado.
