# 自定义业务异常
from app.response import BizCode


class BizException(Exception):
    """业务异常，会被全局异常处理器捕获并返回统一响应"""

    def __init__(self, code: int = BizCode.INTERNAL_ERROR, message: str = "业务异常"):
        self.code = code
        self.message = message
        super().__init__(message)
