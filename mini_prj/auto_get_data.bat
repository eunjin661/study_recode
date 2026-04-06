@echo off
chcp 65001

call C:\Users\Playdata\AppData\Local\miniconda3\condabin\conda.bat activate new_01

python C:\git_test\mini_prj\get_api_data.py >> log.txt 2>&1

pause