class User:
    def __init__(self, claims):
        try:
            self.id = int(claims.get('aud', 0))    # 用户编号，默认为0
            self.power = int(claims.get('power', '0'))  # 权限等级，默认为0
            self.name = claims.get('username', '')  # 用户名，默认为空字符串
        except (ValueError, TypeError) as e:
            raise ValueError(f"JWT claims格式错误: {str(e)}")


from .contest import *
from .problem import *
from .submission import *
from .homework import *
from .questions import *

