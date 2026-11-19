# 简历相关 API 路由
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Resume, ScoreRecord, OptimizationRecord, JobMatchRecord
from app.schemas import (
    OptimizeRequest, OptimizeResponse,
    MatchRequest, MatchResponse,
    ApplySuggestionsRequest,
)
from app.services import parse_service, score_service, optimize_service, match_service
from app.response import Response
from app.exceptions import BizException
from app.response import BizCode
from app.config import settings

router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "doc"}


@router.post("/upload")
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传简历文件，保存并返回 resume_id"""
    # 校验文件类型
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise BizException(BizCode.FILE_ERROR, "仅支持 PDF / Word 格式")

    # 读取文件内容
    file_bytes = file.file.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE:
        raise BizException(BizCode.FILE_ERROR, "文件大小超过 10MB")

    # 保存文件
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # 入库
    resume = Resume(
        file_name=file.filename,
        file_type=ext,
        file_url=saved_path,
        raw_text=None,
        parsed_content=None,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return Response.ok({"resume_id": resume.id, "file_name": file.filename})


@router.post("/{resume_id}/parse")
def parse_resume(resume_id: int, db: Session = Depends(get_db)):
    """解析简历为结构化 JSON"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise BizException(BizCode.NOT_FOUND, "简历不存在")

    with open(resume.file_url, "rb") as f:
        file_bytes = f.read()

    result = parse_service.parse_resume(file_bytes, resume.file_type)
    resume.raw_text = result["raw_text"]
    resume.parsed_content = result["parsed"]
    db.commit()

    return Response.ok({
        "resume_id": resume.id,
        "raw_text": result["raw_text"],
        "parsed": result["parsed"],
    })


@router.post("/{resume_id}/score")
def score_resume(resume_id: int, target_job: str = "", db: Session = Depends(get_db)):
    """智能评分：返回各维度得分"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or not resume.raw_text:
        raise BizException(BizCode.NOT_FOUND, "请先解析简历")

    result = score_service.score_resume(resume.raw_text, target_job)
    record = ScoreRecord(
        resume_id=resume.id,
        total_score=result.get("total", 0),
        dimensions=result.get("dimensions", []),
        summary=result.get("summary", ""),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return Response.ok({
        "record_id": record.id,
        "total_score": record.total_score,
        "dimensions": record.dimensions,
        "summary": record.summary,
    })


@router.post("/{resume_id}/optimize")
def optimize_resume(resume_id: int, body: OptimizeRequest, db: Session = Depends(get_db)):
    """一键优化：按岗位生成逐条建议"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or not resume.raw_text:
        raise BizException(BizCode.NOT_FOUND, "请先解析简历")

    result = optimize_service.optimize_resume(resume.raw_text, body.job_type)
    record = OptimizationRecord(
        resume_id=resume.id,
        job_type=body.job_type,
        suggestions=result["items"],
        optimized_text="",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return Response.ok({
        "record_id": record.id,
        "job_type": record.job_type,
        "suggestions": record.suggestions,
    })


@router.post("/{resume_id}/match")
def match_job(resume_id: int, body: MatchRequest, db: Session = Depends(get_db)):
    """岗位匹配：分析简历与 JD 的匹配度"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or not resume.raw_text:
        raise BizException(BizCode.NOT_FOUND, "请先解析简历")

    result = match_service.match_job(resume.raw_text, body.jd_text)
    record = JobMatchRecord(
        resume_id=resume.id,
        jd_text=body.jd_text,
        match_score=result.get("match_score", 0),
        matched=result.get("matched", []),
        missing=result.get("missing", []),
        suggestions=result.get("suggestions", []),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return Response.ok({
        "record_id": record.id,
        "match_score": record.match_score,
        "matched": record.matched,
        "missing": record.missing,
        "suggestions": record.suggestions,
    })


@router.post("/{resume_id}/apply-suggestions")
def apply_suggestions(resume_id: int, body: ApplySuggestionsRequest, db: Session = Depends(get_db)):
    """应用建议：根据用户接受的下标，合并生成优化后全文"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or not resume.raw_text:
        raise BizException(BizCode.NOT_FOUND, "请先解析简历")

    # 取最近一次优化记录
    record = (
        db.query(OptimizationRecord)
        .filter(OptimizationRecord.resume_id == resume_id)
        .order_by(OptimizationRecord.id.desc())
        .first()
    )
    if not record:
        raise BizException(BizCode.NOT_FOUND, "请先执行优化")

    suggestions = record.suggestions or []
    accepted_set = set(body.accepted_indices)
    optimized_text = resume.raw_text

    for idx, item in enumerate(suggestions):
        item["accepted"] = idx in accepted_set
        if item["accepted"]:
            optimized_text = optimized_text.replace(item["original"], item["improved"])

    record.suggestions = suggestions
    record.optimized_text = optimized_text
    db.commit()

    return Response.ok({
        "record_id": record.id,
        "optimized_text": optimized_text,
        "accepted_count": len(accepted_set),
    })


@router.get("/{resume_id}/export")
def export_resume_file(resume_id: int, format: str = "docx", db: Session = Depends(get_db)):
    """导出优化后简历为 Word / PDF（需在 apply-suggestions 之后调用）"""
    from urllib.parse import quote
    from fastapi.responses import Response as RawResponse
    from app.services import export_service

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise BizException(BizCode.NOT_FOUND, "简历不存在")

    # 取最近一次优化记录
    record = (
        db.query(OptimizationRecord)
        .filter(OptimizationRecord.resume_id == resume_id)
        .order_by(OptimizationRecord.id.desc())
        .first()
    )
    text = (record.optimized_text or "") if record else ""
    if not text.strip():
        text = resume.raw_text or ""  # 未应用优化时导出原文
    content = export_service.export_resume(text, format)

    base = (resume.file_name or "resume").rsplit(".", 1)[0]
    filename = f"{base}_优化后.{format}"
    mime = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "docx" else "application/pdf"
    )
    return RawResponse(
        content=content,
        media_type=mime,
        headers={
            # RFC 5987 编码，支持中文文件名
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )


@router.get("/{resume_id}/diff")
def get_diff(resume_id: int, db: Session = Depends(get_db)):
    """获取优化前后对比数据"""
    record = (
        db.query(OptimizationRecord)
        .filter(OptimizationRecord.resume_id == resume_id)
        .order_by(OptimizationRecord.id.desc())
        .first()
    )
    if not record:
        raise BizException(BizCode.NOT_FOUND, "暂无优化记录")
    return Response.ok({
        "original_text": db.query(Resume).filter(Resume.id == resume_id).first().raw_text,
        "optimized_text": record.optimized_text,
        "suggestions": record.suggestions,
    })
