"""
간단한 IPC 개발 중 페이지 컨트롤러
"""

from fastapi import APIRouter

# IPC 라우터 생성 (간단하게)
router = APIRouter(prefix="/api/ipc", tags=["생산 IPC 정보"])

# 개발 중이므로 API는 최소한만
@router.get("/status")
async def get_status():
    """개발 중 상태 반환"""
    return {
        "success": True,
        "message": "개발 중입니다. 완료 후 오픈 예정입니다.",
        "contact": "정보기획팀 고동현 주임 (내선: 189)"
    }
