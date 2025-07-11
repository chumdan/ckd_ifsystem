"""
LIMS 실험결과 API 컨트롤러
LIMS 데이터를 배치별 통계량으로 압축하여 조회하는 간단한 REST API들
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# LIMS 서비스 함수들
from app.services.lims_service import search_product_qc, get_lims_data, filter_data_by_process_type

# 통계 서비스 함수들 (PIMS와 동일한 함수 재사용)
from app.services.pims_stats_service import calculate_batch_wise_statistics, format_stats_for_display

# LIMS 실험결과 API 라우터 생성
router = APIRouter(prefix="/api/lims", tags=["LIMS 실험결과"])


# 요청 데이터 모델들
class SearchProductLimsRequest(BaseModel):
    """품목 조회 요청 데이터 (LIMS용)"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str = ""      # 배치 번호 (선택, 다중 입력 시 쉼표로 구분)
    proc_code: str = ""     # 공정 코드 (선택)


class GetLimsDataRequest(BaseModel):
    """LIMS 데이터 조회 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 최대 10개까지 조회 권장)
    proc_code: str          # 공정 코드 (필수)
    # 참고: LIMS는 시간 정보가 필요 없음 (PIMS와 다른 점)


class GetLimsChartDataRequest(BaseModel):
    """LIMS 차트 데이터 생성 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 쉼표로 구분)
    proc_code: str          # 공정 코드 (필수)
    # 참고: LIMS는 제품 타입 구분과 시간 정보가 필요 없음
    
    class Config:
        schema_extra = {
            "example": {
                "itemcode": "029124A",
                "batch_no": "HE001k41,HE002k41,HE003k41",
                "proc_code": "AC0"
            }
        }


@router.post("/search-product")
async def api_search_product_lims(request: SearchProductLimsRequest):
    """
    품목 정보를 조회하는 API (LIMS용)
    UP_AI_SearchProduct_QC 프로시저를 사용합니다.
    
    사용법:
    POST /api/lims/search-product
    {
        "itemcode": "029124A",
        "batch_no": "",  // 빈 문자열: 모든 배치 조회
        "proc_code": ""
    }
    """
    try:
        # LIMS 전용 서비스 함수 호출
        result = search_product_qc(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code
        )
        
        # 성공 응답
        return {
            "success": True,
            "message": "품목 조회 성공 (LIMS용)",
            "data": result
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        raise HTTPException(
            status_code=500, 
            detail=f"품목 조회 실패: {str(e)}"
        )


@router.post("/get-lims-data") 
async def api_get_lims_data(request: GetLimsDataRequest):
    """
    LIMS 실험결과 데이터를 원본 그대로 조회하는 API
    UP_LIMS_Get_AI_LIMSDATA 프로시저를 사용합니다.
    
    📊 조회 과정:
    1. UP_LIMS_Get_AI_LIMSDATA로 원본 데이터 조회
    2. 원본 실험 결과를 그대로 반환 (통계 계산 없음)
    
    사용법:
    POST /api/lims/get-lims-data
    {
        "itemcode": "029124A",
        "batch_no": "IE009k41", 
        "proc_code": "AK7"
    }
    """
    try:
        print(f"🔍 LIMS 실험결과 조회 시작: {request.itemcode}, {request.batch_no}, {request.proc_code}")
        
        # LIMS 데이터 조회 (시간 정보 없음)
        raw_data = get_lims_data(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code
        )
        
        # 원본 데이터 그대로 반환 (통계 계산 없음)
        if raw_data:
            print(f"✅ LIMS 실험결과 조회 완료: {len(raw_data)}건의 실험 결과")
            result_data = raw_data
        else:
            result_data = []
        
        # 성공 응답
        return {
            "success": True,
            "message": f"LIMS 실험결과 조회 성공 ({len(result_data)}건의 실험 결과)",
            "data": result_data,
            "total_records": len(result_data)
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        print(f"❌ LIMS 실험결과 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LIMS 실험결과 조회 실패: {str(e)}"
        )


@router.post("/get-chart-data")
async def api_get_lims_chart_data(request: GetLimsChartDataRequest):
    """
    LIMS 실험결과를 이용하여 차트용 데이터를 생성하는 API
    
    📊 차트 데이터 생성 과정:
    1. LIMS 원본 데이터 조회
    2. 배치별 통계 계산
    3. 차트용 JSON 형태로 변환
    
    사용법:
    POST /api/lims/get-chart-data
    {
        "itemcode": "029124A",
        "batch_no": "HE001k41,HE002k41",
        "proc_code": "AC0"
    }
    """
    try:
        print(f"🔍 LIMS 차트 데이터 생성 시작: {request.itemcode}, {request.batch_no}, {request.proc_code}")
        
        # LIMS 데이터 조회
        raw_data = get_lims_data(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code
        )
        
        # 공정별 변수 필터링 적용
        if raw_data and request.proc_code:
            filtered_data = filter_data_by_process_type(raw_data, request.proc_code)
        else:
            filtered_data = raw_data
        
        # 배치별 통계 계산 및 차트 데이터 생성
        if filtered_data:
            stats_result = calculate_batch_wise_statistics(filtered_data)
            
            # 차트용 데이터 포맷 변환 (PIMS와 동일한 로직 적용)
            chart_data = {
                "stats_data": stats_result,
                "batch_count": len(stats_result),
                "variables": [],
                "chart_ready": True
            }
            
            # 사용 가능한 변수들 추출
            if stats_result:
                for key in stats_result[0].keys():
                    if key.endswith("_평균") and not key.startswith("배치번호"):
                        variable_name = key.replace("_평균", "")
                        chart_data["variables"].append(variable_name)
        else:
            chart_data = {
                "stats_data": [],
                "batch_count": 0,
                "variables": [],
                "chart_ready": False
            }
        
        # 성공 응답
        return {
            "success": True,
            "message": "LIMS 차트 데이터 생성 성공",
            "data": chart_data
        }
        
    except Exception as e:
        print(f"❌ LIMS 차트 데이터 생성 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LIMS 차트 데이터 생성 실패: {str(e)}"
        ) 