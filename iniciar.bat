@echo off
chcp 65001 > nul 2>&1
title EPI Detect

:menu
cls
color 09
echo.
echo  +--------------------------------------------------+
echo  ^|                   EPI DETECT                      ^|
echo  ^|   Deteccao de Colete de Seguranca em Tempo Real  ^|
echo  ^|              Criado por Henrique Erdei            ^|
echo  +--------------------------------------------------+
echo.
echo    [1]  Painel web  (fonte no navegador)
echo    [2]  Webcam desktop
echo    [Q]  Sair
echo.
echo  --------------------------------------------------
echo.
set /p opcao=  Escolha:

if /i "%opcao%"=="1" goto painel
if /i "%opcao%"=="2" goto desktop
if /i "%opcao%"=="q" exit
echo  Opcao invalida.
timeout /t 2 > nul
goto menu

:matar_servidor
echo  Encerrando instancia anterior (se houver)...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F > nul 2>&1
)
taskkill /IM python.exe /F > nul 2>&1
timeout /t 1 > nul
goto :eof

:painel
cls
echo.
echo  Iniciando painel em http://localhost:5000
echo  Escolha a fonte no navegador: stream ou arquivo MP4.
echo  Pressione CTRL+C para encerrar.
echo.
call :matar_servidor
cd /d "%~dp0"
python server.py --source webcam
goto volta

:desktop
cls
echo.
echo  Webcam desktop. Q para sair.
echo.
call :matar_servidor
cd /d "%~dp0"
python detect.py --source webcam
goto volta

:volta
echo.
echo  Pressione qualquer tecla para voltar ao menu.
pause > nul
goto menu
