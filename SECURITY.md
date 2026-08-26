# Segurança

## Escopo

Relate em privado falhas que possam expor câmeras, arquivos locais, dados pessoais, credenciais (incluindo senha de RTSP) ou permitir acesso não autorizado ao servidor.

## Como relatar

No GitHub, use **Private vulnerability reporting** na aba Security. Não abra issue pública com PoC explorável.

Inclua versão, ambiente, passos de reprodução, impacto e, se possível, uma correção. Não anexe imagens pessoais nem senhas reais.

## Implantação

O Flask desta versão é só para execução local. Não há autenticação, HTTPS nem endurecimento para internet. Detalhes em [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
