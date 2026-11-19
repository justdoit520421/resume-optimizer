# 统一响应体与业务码
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """统一响应包装：{ code, message, data }"""
    code: int = 0
    message: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "Response":
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 1000, message: str = "error") -> "Response":
        return cls(code=code, message=message, data=None)


# 常用业务码
class BizCode:
    SUCCESS = 0
    PARAM_ERROR = 1001       # 参数校验失败
    NOT_FOUND = 1002         # 资源不存在
    FILE_ERROR = 1003        # 文件解析失败
    LLM_ERROR = 1004         # 大模型调用失败
    INTERNAL_ERROR = 9999    # 未知错误
