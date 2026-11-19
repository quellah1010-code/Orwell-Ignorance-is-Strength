@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
pushd "%~dp0" || exit /b 1
echo 请选择含有 Ignorance_Data 的原版游戏目录，或选择 Ignorance_Data 本身。
set "gameRoot="
for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.ShowNewFolderButton=$false; $d.Description='选择原版游戏目录'; if($d.ShowDialog() -eq 'OK'){[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); [Console]::WriteLine($d.SelectedPath)}"`) do set "gameRoot=%%D"
if not defined gameRoot exit /b 0
if exist "%gameRoot%\resources.assets" for %%D in ("%gameRoot%\..") do set "gameRoot=%%~fD"
for %%F in (resources.assets level1 level4 Managed\Assembly-CSharp.dll) do if not exist "%gameRoot%\Ignorance_Data\%%F" goto :missing
if exist ".venv\Scripts\python.exe" goto :install
py -3.12 -m venv .venv || goto :python
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :failed
set "outputDir=build\layout-%RANDOM%-%RANDOM%"
".venv\Scripts\python.exe" tools\build_menu.py --game-dir "%gameRoot%" --output "%outputDir%" || goto :failed
explorer.exe /select,"%CD%\%outputDir%\orwell-zh-menu-0.3.zip"
exit /b 0
:missing
echo 所选目录缺少原版文件。请选择含完整 Ignorance_Data 目录的原版游戏或备份。
goto :failed
:python
echo 请安装 Python 3.12 和 Python Launcher，再双击此文件。
:failed
pause
exit /b 1
