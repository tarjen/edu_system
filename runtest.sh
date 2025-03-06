# 添加当前目录到 PYTHONPATH
# PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/test_JWTtoken.py
# PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/test_contestAPI.py
# PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/test_submit.py
# PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/test_problemAPI.py 
# PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/test_submit.py > output.txt 2>&1
PYTHONPATH=$PYTHONPATH:. coverage run -m pytest online_judge/test/
coverage html
