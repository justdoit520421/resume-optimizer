from fastapi import APIRouter

from .resume import router as resume_router

router = APIRouter()
router.include_router(resume_router)
