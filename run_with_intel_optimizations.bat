@echo off
echo Setting up Intel oneAPI environment...
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" > nul
echo Intel oneAPI environment set up successfully.
echo.
echo Running WhatsApp Unified Tool with Intel optimizations...
echo.
python %*
