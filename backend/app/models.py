# ORM 数据模型
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.database import Base


class Resume(Base):
    """简历主表：存储原始文件路径与解析后的结构化内容"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1, comment="用户ID（暂默认1）")
    file_name = Column(String(255), comment="原始文件名")
    file_type = Column(String(20), comment="pdf/docx")
    file_url = Column(String(500), comment="文件存储路径")
    raw_text = Column(Text, comment="简历纯文本")
    parsed_content = Column(JSON, comment="结构化解析结果")
    created_at = Column(DateTime, server_default=func.now())


class ScoreRecord(Base):
    """评分记录：各维度得分与理由"""
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, nullable=False, index=True)
    total_score = Column(Integer, comment="总分 0-100")
    dimensions = Column(JSON, comment="各维度：[{name, score, max, reason}]")
    summary = Column(Text, comment="整体评价")
    created_at = Column(DateTime, server_default=func.now())


class OptimizationRecord(Base):
    """优化记录：逐条建议与是否接受"""
    __tablename__ = "optimization_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, nullable=False, index=True)
    job_type = Column(String(50), comment="岗位类型：tech/product/operation/design")
    suggestions = Column(JSON, comment="建议列表：[{original, improved, reason, type, accepted}]")
    optimized_text = Column(Text, comment="优化后全文")
    created_at = Column(DateTime, server_default=func.now())


class JobMatchRecord(Base):
    """岗位匹配记录"""
    __tablename__ = "job_match_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, nullable=False, index=True)
    jd_text = Column(Text, comment="岗位描述原文")
    match_score = Column(Integer, comment="匹配度 0-100")
    matched = Column(JSON, comment="已匹配的能力点")
    missing = Column(JSON, comment="缺失的能力点")
    suggestions = Column(JSON, comment="改进建议")
    created_at = Column(DateTime, server_default=func.now())
