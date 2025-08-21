@echo off
setlocal

:: Garante que o script seja executado a partir do seu prÃ³prio diretÃ³rio
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Define o nome e o caminho para o atalho na Ã¡rea de trabalho
set "SHORTCUT_NAME=CrediGestor.lnk"
set "DESKTOP_PATH=%USERPROFILE%\Desktop"
set "SHORTCUT_PATH=%DESKTOP_PATH%\%SHORTCUT_NAME%"

:: --- ConfiguraÃ§Ã£o do Atalho (feito silenciosamente) ---
set "TARGET_PATH=%SCRIPT_DIR%run.bat"
set "ICON_PATH=%SCRIPT_DIR%assets\icon.ico"

:: Cria ou atualiza o atalho na Ã¡rea de trabalho.
:: O comando PowerShell garante que o atalho tenha o Ã­cone e o diretÃ³rio de trabalho corretos.
:: A saÃ­da Ã© redirecionada para >nul para uma execuÃ§Ã£o limpa.
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_PATH%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; if (Test-Path '%ICON_PATH%') { $s.IconLocation = '%ICON_PATH%' }; $s.Save()" >nul 2>&1

:: --- InicializaÃ§Ã£o da AplicaÃ§Ã£o ---
echo Iniciando CrediGestor...
echo (Aguarde, verificando e instalando dependÃªncias se necessÃ¡rio...)

:: O comando 'start' lanÃ§a o processo e permite que este script .bat termine.
:: Usamos 'pyw -3' (equivalente a pythonw.exe) para executar o script da aplicaÃ§Ã£o grÃ¡fica
:: sem abrir uma janela de console (prompt de comando).
start "CrediGestor" pyw -3 start.py

endlocal
exit /b