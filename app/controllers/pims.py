"""
PIMS API 컨트롤러
PIMS 데이터 조회를 위한 간단한 REST API들
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.pims_service import search_product, get_pims_data_basic, get_pims_data_l23

# PIMS API 라우터 생성
router = APIRouter(prefix="/api/pims", tags=["PIMS"])


# 요청 데이터 모델들 (입력 검증용)
class SearchProductRequest(BaseModel):
    """품목 조회 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str = ""      # 배치 번호 (선택, 다중 입력 시 쉼표로 구분)
    proc_code: str = ""     # 공정 코드 (선택)


class GetDataRequest(BaseModel):
    """데이터 조회 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 최대 10개까지 조회 권장)
    proc_code: str          # 공정 코드 (필수)
    start_time: str = ""    # 시작 시간 (선택사항, 없으면 모든 데이터)
    end_time: str = ""      # 종료 시간 (선택사항, 없으면 모든 데이터)
    limit: int = 50         # 조회 건수 제한 (기본: 50건, 최대: 1000건)
    
    class Config:
        # limit 값 검증: 1~1000 사이의 값만 허용
        schema_extra = {
            "example": {
                "itemcode": "029124A",
                "batch_no": "HE001K41",
                "proc_code": "AB1",
                "start_time": "",
                "end_time": "",
                "limit": 50
            }
        }


@router.post("/search-product")
async def api_search_product(request: SearchProductRequest):
    """
    품목 정보를 조회하는 API
    UP_AI_SearchProduct 프로시저를 호출합니다.
    
    사용법:
    POST /api/pims/search-product
    {
        "itemcode": "029124A",
        "batch_no": "",  // 빈 문자열: 모든 배치 조회
        "proc_code": ""
    }
    
    특정 배치들만 조회 (최대 10개 권장):
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41,HE002K41,HE003K41",  // 쉼표로 구분
        "proc_code": ""
    }
    """
    try:
        # 서비스 함수 호출
        result = search_product(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code
        )
        
        # 성공 응답
        return {
            "success": True,
            "message": "품목 조회 성공",
            "data": result
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        raise HTTPException(
            status_code=500, 
            detail=f"품목 조회 실패: {str(e)}"
        )


@router.post("/get-data-basic") 
async def api_get_data_basic(request: GetDataRequest):
    """
    기존고형제 PIMS 데이터를 조회하는 API
    Get_AIDATA 프로시저를 호출합니다.
    
    사용법:
    POST /api/pims/get-data-basic
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41", 
        "proc_code": "AB1",
        "start_time": "2024-01-01 00:00:00",  // 선택사항
        "end_time": "2024-01-01 23:59:59"    // 선택사항
    }
    
    시간 설정 없이 조회 (기본 50건):
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41", 
        "proc_code": "AB1"
    }
    
    더 많은 데이터 조회 (최대 1000건):
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41", 
        "proc_code": "AB1",
        "limit": 200
    }
    """
    try:
        # limit 값 검증 (최대 1000건)
        limit = min(request.limit, 1000) if request.limit > 0 else 50
        
        # 서비스 함수 호출
        result = get_pims_data_basic(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=limit
        )
        
        # 성공 응답
        return {
            "success": True,
            "message": f"기존고형제 데이터 조회 성공 ({len(result)}건 조회됨)",
            "data": result,
            "total_count": len(result),
            "limit": limit
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        raise HTTPException(
            status_code=500,
            detail=f"기존고형제 데이터 조회 실패: {str(e)}"
        )


@router.post("/get-data-l23")
async def api_get_data_l23(request: GetDataRequest):
    """
    스마트고형제 PIMS 데이터를 조회하는 API
    Get_AIDATA_L23 프로시저를 호출합니다.
    
    사용법:
    POST /api/pims/get-data-l23
    {
        "itemcode": "056421A",
        "batch_no": "HE002M61",  // 1개 배치만 (최대 10개까지 권장)
        "proc_code": "AB1",
        "start_time": "2024-01-01 00:00:00",  // 선택사항
        "end_time": "2024-01-01 23:59:59"    // 선택사항
    }
    
    시간 설정 없이 조회 (기본 50건):
    {
        "itemcode": "056421A",
        "batch_no": "HE002M61", 
        "proc_code": "AB1"
    }
    
    더 많은 데이터 조회 (최대 1000건):
    {
        "itemcode": "056421A",
        "batch_no": "HE002M61", 
        "proc_code": "AB1",
        "limit": 200
    }
    """
    try:
        # limit 값 검증 (최대 1000건)
        limit = min(request.limit, 1000) if request.limit > 0 else 50
        
        # 서비스 함수 호출
        result = get_pims_data_l23(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=limit
        )
        
        # 성공 응답
        return {
            "success": True,
            "message": f"스마트고형제 데이터 조회 성공 ({len(result)}건 조회됨)", 
            "data": result,
            "total_count": len(result),
            "limit": limit
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        raise HTTPException(
            status_code=500,
            detail=f"스마트고형제 데이터 조회 실패: {str(e)}"
        )