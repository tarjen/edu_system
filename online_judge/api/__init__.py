class User:
    def __init__(self, claims):
        self.id = int(claims.get('aud'))    # 用户编号(字符串类型)
        self.power = int(claims.get('power'))  # 权限等级
        self.name = claims.get('username')  # 权限等级


from .contest import *
from .problem import *
from .submission import *

