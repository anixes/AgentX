@echo off
SET PYTHON_PATH="D:\ANACONDA py\python.exe"
if "%1"=="api_bridge" (
    %PYTHON_PATH% scripts/api_bridge.py
) else (
    %PYTHON_PATH% agentx.py %*
)
