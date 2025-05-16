@echo off
echo === 运行测试用例 ===
python -m pytest online_judge/test/test_gen_homework.py -v --capture=no --log-cli-level=INFO 