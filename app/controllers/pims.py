"""
PIMS API 컨트롤러
PIMS 데이터 조회를 위한 간단한 REST API들
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.pims_service import search_product, get_pims_data_basic, get_pims_data_l23, get_pims_data_with_batch_times

# PIMS API 라우터 생성
router = APIRouter(prefix="/api/pims", tags=["PIMS"])


# 요청 데이터 모델들 (입력 검증용)
class SearchProductRequest(BaseModel):
    """품목 조회 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str = ""      # 배치 번호 (선택, 다중 입력 시 쉼표로 구분)
    proc_code: str = ""     # 공정 코드 (선택)


class GetDataRequest(BaseModel):
    """데이터 조회 요청 데이터 (확장된 시간 설정 지원)"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 최대 10개까지 조회 권장)
    proc_code: str          # 공정 코드 (필수)
    limit: int = 50         # 조회 건수 제한 (기본: 50건, 최대: 1000건)
    
    # 시간 설정 방식 (기존 호환성 유지)
    start_time: Optional[str] = None    # 공통 시작 시간 (기존 방식)
    end_time: Optional[str] = None      # 공통 종료 시간 (기존 방식)
    
    # 새로운 시간 설정 방식 (선택사항)
    mode: Optional[str] = "common"      # 'common' 또는 'individual'
    batch_time_ranges: Optional[Dict[str, Dict[str, Optional[str]]]] = None  # 배치별 개별 시간
    
    class Config:
        schema_extra = {
            "example_common": {
                "itemcode": "029124A",
                "batch_no": "HE001K41",
                "proc_code": "AB1",
                "mode": "common",
                "start_time": "2024-05-23T21:00",
                "end_time": "2024-05-23T22:00",
                "limit": 50
            },
            "example_individual": {
                "itemcode": "029124A", 
                "batch_no": "HE001K41,HE002K41",
                "proc_code": "AB1",
                "mode": "individual",
                "batch_time_ranges": {
                    "HE001K41": {"start": "2024-05-23T21:00", "end": "2024-05-23T22:00"},
                    "HE002K41": {"start": "2024-05-24T09:00", "end": "2024-05-24T10:00"}
                },
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
        # limit 값 검증 및 처리
        # limit <= 0이면 제한 없음 (모든 데이터), limit > 0이면 해당 값 사용 (최대 1000건)
        if request.limit <= 0:
            limit = 0  # 제한 없음 (모든 데이터)
        else:
            limit = min(request.limit, 1000)  # 최대 1000건 제한
        
        # 시간 데이터 처리
        if request.mode == "individual" and request.batch_time_ranges:
            # 배치별 개별 시간 처리
            batches_with_times = {}
            
            # 선택된 배치들 파싱
            batch_list = [b.strip() for b in request.batch_no.split(',') if b.strip()]
            
            # 각 배치의 시간 정보 수집
            for batch_no in batch_list:
                if batch_no in request.batch_time_ranges:
                    batches_with_times[batch_no] = request.batch_time_ranges[batch_no]
                else:
                    # 시간 정보가 없는 배치는 시간 제한 없이 조회
                    batches_with_times[batch_no] = {"start": "", "end": ""}
            
            # 배치별 개별 조회
            result = get_pims_data_with_batch_times(
                itemcode=request.itemcode,
                batches_with_times=batches_with_times,
                proc_code=request.proc_code,
                limit=limit,
                data_type="basic"
            )
        else:
            # 공통 시간 또는 기존 방식
            start_time = request.start_time or ""
            end_time = request.end_time or ""
            
            # 기존 서비스 함수 호출
            result = get_pims_data_basic(
                itemcode=request.itemcode,
                batch_no=request.batch_no,
                proc_code=request.proc_code,
                start_time=start_time,
                end_time=end_time,
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
        # limit 값 검증 및 처리
        # limit <= 0이면 제한 없음 (모든 데이터), limit > 0이면 해당 값 사용 (최대 1000건)
        if request.limit <= 0:
            limit = 0  # 제한 없음 (모든 데이터)
        else:
            limit = min(request.limit, 1000)  # 최대 1000건 제한
        
        # 시간 데이터 처리
        if request.mode == "individual" and request.batch_time_ranges:
            # 배치별 개별 시간 처리
            batches_with_times = {}
            
            # 선택된 배치들 파싱
            batch_list = [b.strip() for b in request.batch_no.split(',') if b.strip()]
            
            # 각 배치의 시간 정보 수집
            for batch_no in batch_list:
                if batch_no in request.batch_time_ranges:
                    batches_with_times[batch_no] = request.batch_time_ranges[batch_no]
                else:
                    # 시간 정보가 없는 배치는 시간 제한 없이 조회
                    batches_with_times[batch_no] = {"start": "", "end": ""}
            
            # 배치별 개별 조회
            result = get_pims_data_with_batch_times(
                itemcode=request.itemcode,
                batches_with_times=batches_with_times,
                proc_code=request.proc_code,
                limit=limit,
                data_type="l23"
            )
        else:
            # 공통 시간 또는 기존 방식
            start_time = request.start_time or ""
            end_time = request.end_time or ""
            
            # 기존 서비스 함수 호출
            result = get_pims_data_l23(
                itemcode=request.itemcode,
                batch_no=request.batch_no,
                proc_code=request.proc_code,
                start_time=start_time,
                end_time=end_time,
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