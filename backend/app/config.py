# 应用配置：从环境变量读取，支持 .env
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，优先从环境变量读取"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 数据库
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/resume_optimizer?charset=utf8mb4"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM
    # provider 可选：mock / openai / deepseek / qwen / glm / kimi / doubao / ernie
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""  # 留空则使用各厂商默认地址
    LLM_MODEL: str = ""     # 留空则使用各厂商默认模型
    LLM_MAX_TOKENS: int = 0  # 单次输出上限，0 表示用厂商默认（deepseek 建议设 8192 防截断）

    # 文件上传
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
