"""
FastAPI 애플리케이션 메인 파일
PIMS/LIMS 조회 시스템의 진입점입니다.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.controllers import pims, pims_stats, lims, ipc

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# API 라우터 등록
app.include_router(pims.router)
app.include_router(pims_stats.router)
app.include_router(lims.router)
app.include_router(ipc.router)

# 정적 파일 설정 (CSS, JS, 이미지 등)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    메인 페이지 (추후 로그인 페이지 개발 예정)
    """
    return templates.TemplateResponse(
        "base.html", 
        {"request": request, "title": "CKD PIMS/LIMS 조회 시스템"}
    )


@app.get("/pims", response_class=HTMLResponse) 
async def pims_page(request: Request):
    """
    PIMS 조회 페이지를 보여주는 함수
    """
    return templates.TemplateResponse(
        "pims.html",
        {"request": request, "title": "PIMS 데이터 조회"}
    )


@app.get("/pims-stats", response_class=HTMLResponse) 
async def pims_stats_page(request: Request):
    """
    PIMS 배치요약 페이지를 보여주는 함수
    """
    return templates.TemplateResponse(
        "pims_stats.html",
        {"request": request, "title": "PIMS 배치요약"}
    )


@app.get("/lims", response_class=HTMLResponse) 
async def lims_page(request: Request):
    """
    LIMS 실험결과 페이지를 보여주는 함수
    """
    return templates.TemplateResponse(
        "lims.html",
        {"request": request, "title": "LIMS 실험결과"}
    )


@app.get("/ipc", response_class=HTMLResponse) 
async def ipc_page(request: Request):
    """
    생산 IPC 정보 페이지를 보여주는 함수
    """
    return templates.TemplateResponse(
        "ipc.html",
        {"request": request, "title": "생산 IPC 정보"}
    )


# 서버 실행할 때 사용 (개발용)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True  # 코드 변경 시 자동 재시작
    )