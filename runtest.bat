@echo off
REM 设置 Python 解释器路径
set PYTHON=.\venv\bin\python.exe

REM 运行所有测试文件
@REM %PYTHON% -m pytest online_judge/test/test_JWTtoken.py
@REM %PYTHON% -m pytest online_judge/test/test_contestAPI.py
@REM %PYTHON% -m pytest online_judge/test/test_submit.py
%PYTHON% -m pytest online_judge/test/test_problemAPI.py
@REM %PYTHON% -m pytest online_judge/test/test_problem_selection.py
@REM %PYTHON% -m pytest online_judge/test/test_create_problem.py
@REM %PYTHON% -m pytest online_judge/test/test_incontest.py
@REM %PYTHON% -m pytest online_judge/test/test_submit.py > output.txt 2>&1
@REM %PYTHON% -m pytest online_judge/test/test_questions_API.py  
@REM %PYTHON% -m pytest online_judge/test/test_homework_API.py  
@REM %PYTHON% -m pytest online_judge/test/test_gen_homework.py

REM 或者直接运行所有测试
REM %PYTHON% -m pytest online_judge/test/