@echo off
echo Starting Sushi Bot...
choice /C YN /M "Run with Docker? (Y/N)"
if errorlevel 2 goto :run_python
if errorlevel 1 goto :run_docker

:run_docker
echo Checking for existing container...
docker ps -a -q -f name=sushi-bot-container > nul
if %errorlevel% equ 0 (
    echo Stopping and removing existing container...
    docker stop sushi-bot-container
    docker rm sushi-bot-container
)
echo Building Docker image...
docker build -t sushi-bot .
echo Running Docker container...
docker run -d --name sushi-bot-container sushi-bot
echo Container started. View logs with: docker logs sushi-bot-container
pause
goto :eof

:run_python
echo Running with Python...
python bot.py
pause
goto :eof