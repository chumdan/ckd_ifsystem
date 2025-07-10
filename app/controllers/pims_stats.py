"""
PIMS 배치요약 API 컨트롤러
PIMS 데이터를 배치별 통계량으로 압축하여 조회하는 간단한 REST API들
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 기존 PIMS 서비스 함수들 재활용 (조회 로직은 동일)
from app.services.pims_service import search_product, get_pims_data_basic, get_pims_data_l23, get_pims_data_with_batch_times, filter_data_by_process_type

# 새로운 통계 서비스 함수들
from app.services.pims_stats_service import calculate_simple_statistics, calculate_batch_wise_statistics, format_stats_for_display

# PIMS 배치요약 API 라우터 생성
router = APIRouter(prefix="/api/pims-stats", tags=["PIMS 배치요약"])


# 요청 데이터 모델들 (기존과 동일하지만 별도 정의)
class SearchProductStatsRequest(BaseModel):
    """품목 조회 요청 데이터 (배치요약용)"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str = ""      # 배치 번호 (선택, 다중 입력 시 쉼표로 구분)
    proc_code: str = ""     # 공정 코드 (선택)


class GetStatsDataRequest(BaseModel):
    """배치요약 데이터 조회 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 최대 10개까지 조회 권장)
    proc_code: str          # 공정 코드 (필수)
    
    # 시간 설정 방식 (기존 호환성 유지)
    start_time: Optional[str] = None    # 공통 시작 시간 (기존 방식)
    end_time: Optional[str] = None      # 공통 종료 시간 (기존 방식)
    
    # 새로운 시간 설정 방식 (선택사항)
    mode: Optional[str] = "common"      # 'common' 또는 'individual'
    batch_time_ranges: Optional[Dict[str, Dict[str, Optional[str]]]] = None  # 배치별 개별 시간


class GetChartDataRequest(BaseModel):
    """차트 데이터 생성 요청 데이터"""
    itemcode: str           # 품목 코드 (필수)
    batch_no: str           # 배치 번호 (필수, 쉼표로 구분)
    proc_code: str          # 공정 코드 (필수)
    product_type: str       # 제품 타입 (basic 또는 l23)
    
    # 시간 설정 (기존과 동일)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    mode: Optional[str] = "common"
    batch_time_ranges: Optional[Dict[str, Dict[str, Optional[str]]]] = None
    
    class Config:
        schema_extra = {
            "example_common": {
                "itemcode": "029124A",
                "batch_no": "HE001K41",
                "proc_code": "AB1",
                "mode": "common",
                "start_time": "2024-05-23T21:00",
                "end_time": "2024-05-23T22:00"
            },
            "example_individual": {
                "itemcode": "029124A", 
                "batch_no": "HE001K41,HE002K41",
                "proc_code": "AB1",
                "mode": "individual",
                "batch_time_ranges": {
                    "HE001K41": {"start": "2024-05-23T21:00", "end": "2024-05-23T22:00"},
                    "HE002K41": {"start": "2024-05-24T09:00", "end": "2024-05-24T10:00"}
                }
            }
        }


@router.post("/search-product")
async def api_search_product_stats(request: SearchProductStatsRequest):
    """
    품목 정보를 조회하는 API (배치요약용)
    기존 search_product 함수를 재활용합니다.
    
    사용법:
    POST /api/pims-stats/search-product
    {
        "itemcode": "029124A",
        "batch_no": "",  // 빈 문자열: 모든 배치 조회
        "proc_code": ""
    }
    """
    try:
        # 기존 서비스 함수 재활용
        result = search_product(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code
        )
        
        # 성공 응답
        return {
            "success": True,
            "message": "품목 조회 성공 (배치요약용)",
            "data": result
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        raise HTTPException(
            status_code=500, 
            detail=f"품목 조회 실패: {str(e)}"
        )


@router.post("/get-stats-basic") 
async def api_get_stats_basic(request: GetStatsDataRequest):
    """
    기존고형제 PIMS 데이터를 배치별 통계량으로 조회하는 API
    
    📊 통계 처리 과정:
    1. 기존 get_pims_data_basic으로 원본 데이터 조회 (3,000~10,000건)
    2. 공정별 변수 필터링 적용
    3. 배치별로 그룹화하여 통계량 계산
    4. 각 변수별로 평균, 표준편차, 25%, 50%, 75% 계산
    5. 배치당 1행으로 압축하여 반환
    
    사용법:
    POST /api/pims-stats/get-stats-basic
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41", 
        "proc_code": "AB1",
        "start_time": "2024-01-01T00:00",  // 선택사항
        "end_time": "2024-01-01T23:59"    // 선택사항
    }
    """
    try:
        print(f"🔍 기존고형제 배치요약 조회 시작: {request.itemcode}, {request.batch_no}, {request.proc_code}")
        
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
            
            # 배치별 개별 조회 (모든 데이터)
            raw_data = get_pims_data_with_batch_times(
                itemcode=request.itemcode,
                batches_with_times=batches_with_times,
                proc_code=request.proc_code,
                limit=0,  # 통계 계산을 위해 모든 데이터 필요
                data_type="basic"
            )
        else:
            # 공통 시간 또는 기존 방식
            start_time = request.start_time or ""
            end_time = request.end_time or ""
            
            # 기존 서비스 함수 호출 (모든 데이터)
            raw_data = get_pims_data_basic(
                itemcode=request.itemcode,
                batch_no=request.batch_no,
                proc_code=request.proc_code,
                start_time=start_time,
                end_time=end_time,
                limit=0  # 통계 계산을 위해 모든 데이터 필요
            )
        
        # 공정별 변수 필터링 적용
        if raw_data and request.proc_code:
            print(f"🔍 공정별 변수 필터링 적용: {request.proc_code}")
            filtered_data = filter_data_by_process_type(raw_data, request.proc_code)
        else:
            filtered_data = raw_data
        
        # 📊 배치별 통계량 계산 (기존고형)
        if filtered_data:
            print(f"📊 기존고형 배치별 통계 계산 시작: {len(filtered_data)}건 → 배치별 압축")
            
            # 배치별 통계 계산 함수 호출 (이미 리스트로 반환됨)
            stats_result = calculate_batch_wise_statistics(filtered_data)
            
            # 각 배치에 추가 정보 덧붙이기
            for stats_row in stats_result:
                stats_row["품목코드"] = request.itemcode
                stats_row["공정코드"] = request.proc_code
                
                # 화면 표시용 포맷팅
                stats_row.update(format_stats_for_display(stats_row))
        else:
            stats_result = []
        
        # 성공 응답
        return {
            "success": True,
            "message": f"기존고형제 배치요약 조회 성공 ({len(stats_result)}개 배치 처리)",
            "data": stats_result,
            "total_batches": len(stats_result),
            "original_data_count": len(filtered_data) if filtered_data else 0
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        print(f"❌ 기존고형제 배치요약 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"기존고형제 배치요약 조회 실패: {str(e)}"
        )


@router.post("/get-stats-l23")
async def api_get_stats_l23(request: GetStatsDataRequest):
    """
    스마트고형제 PIMS 데이터를 배치별 통계량으로 조회하는 API
    
    📊 통계 처리 과정:
    1. 기존 get_pims_data_l23으로 원본 데이터 조회 (3,000~10,000건)
    2. 공정별 변수 필터링 적용
    3. 배치별로 그룹화하여 통계량 계산
    4. 각 변수별로 평균, 표준편차, 25%, 50%, 75% 계산
    5. 배치당 1행으로 압축하여 반환
    
    사용법:
    POST /api/pims-stats/get-stats-l23
    {
        "itemcode": "056421A",
        "batch_no": "HE002M61", 
        "proc_code": "AB1",
        "start_time": "2024-01-01T00:00",  // 선택사항
        "end_time": "2024-01-01T23:59"    // 선택사항
    }
    """
    try:
        print(f"🔍 스마트고형제 배치요약 조회 시작: {request.itemcode}, {request.batch_no}, {request.proc_code}")
        
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
            
            # 배치별 개별 조회 (모든 데이터)
            raw_data = get_pims_data_with_batch_times(
                itemcode=request.itemcode,
                batches_with_times=batches_with_times,
                proc_code=request.proc_code,
                limit=0,  # 통계 계산을 위해 모든 데이터 필요
                data_type="l23"
            )
        else:
            # 공통 시간 또는 기존 방식
            start_time = request.start_time or ""
            end_time = request.end_time or ""
            
            # 기존 서비스 함수 호출 (모든 데이터)
            raw_data = get_pims_data_l23(
                itemcode=request.itemcode,
                batch_no=request.batch_no,
                proc_code=request.proc_code,
                start_time=start_time,
                end_time=end_time,
                limit=0  # 통계 계산을 위해 모든 데이터 필요
            )
        
        # 공정별 변수 필터링 적용
        if raw_data and request.proc_code:
            print(f"🔍 공정별 변수 필터링 적용: {request.proc_code}")
            filtered_data = filter_data_by_process_type(raw_data, request.proc_code)
        else:
            filtered_data = raw_data
        
        # 📊 배치별 통계량 계산 (스마트고형)
        if filtered_data:
            print(f"📊 스마트고형 배치별 통계 계산 시작: {len(filtered_data)}건 → 배치별 압축")
            
            # 배치별 통계 계산 함수 호출 (이미 리스트로 반환됨)
            stats_result = calculate_batch_wise_statistics(filtered_data)
            
            # 각 배치에 추가 정보 덧붙이기
            for stats_row in stats_result:
                stats_row["품목코드"] = request.itemcode
                stats_row["공정코드"] = request.proc_code
                
                # 화면 표시용 포맷팅
                stats_row.update(format_stats_for_display(stats_row))
        else:
            stats_result = []
        
        # 성공 응답
        return {
            "success": True,
            "message": f"스마트고형제 배치요약 조회 성공 ({len(stats_result)}개 배치 처리)",
            "data": stats_result,
            "total_batches": len(stats_result),
            "original_data_count": len(filtered_data) if filtered_data else 0
        }
        
    except Exception as e:
        # 에러 발생 시 응답
        print(f"❌ 스마트고형제 배치요약 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"스마트고형제 배치요약 조회 실패: {str(e)}"
        )


@router.post("/get-chart-data")
async def api_get_chart_data(request: GetChartDataRequest):
    """
    차트 분석용 데이터 생성 API (Python에서 모든 계산 처리)
    
    📊 생성되는 차트 데이터:
    1. 트렌드 차트용: 배치번호별 각 변수의 평균값
    2. 변동계수(CV) 차트용: 각 변수의 안정성 지표 (CV = 표준편차/평균 × 100)
    
    사용법:
    POST /api/pims-stats/get-chart-data
    {
        "itemcode": "029124A",
        "batch_no": "HE001K41,HE002K41,HE003K41",
        "proc_code": "AB1",
        "product_type": "basic"
    }
    """
    try:
        print(f"📊 차트 데이터 생성 요청: {request.itemcode}, {request.batch_no}, {request.proc_code}")
        
        # 통계 데이터 조회 (기존 로직 재사용)
        stats_request = GetStatsDataRequest(
            itemcode=request.itemcode,
            batch_no=request.batch_no,
            proc_code=request.proc_code,
            start_time=request.start_time,
            end_time=request.end_time,
            mode=request.mode,
            batch_time_ranges=request.batch_time_ranges
        )
        
        if request.product_type == 'basic':
            stats_response = await api_get_stats_basic(stats_request)
        elif request.product_type == 'l23':
            stats_response = await api_get_stats_l23(stats_request)
        else:
            return {
                "success": False,
                "message": "지원하지 않는 제품 타입입니다. (basic 또는 l23만 가능)",
                "data": {}
            }
        
        if not stats_response.get("success") or not stats_response.get("data"):
            return {
                "success": False,
                "message": "차트 생성을 위한 통계 데이터가 없습니다.",
                "data": {}
            }
        
        stats_data = stats_response["data"]
        print(f"📊 차트용 통계 데이터 수집 완료: {len(stats_data)}개 배치")
        
        # Python에서 차트용 데이터 생성 (pims_stats_service에 위임)
        from app.services.pims_stats_service import generate_chart_data
        chart_data = generate_chart_data(stats_data)
        
        return {
            "success": True,
            "message": f"차트 데이터 생성 성공: {len(chart_data.get('variables', []))}개 변수, {len(stats_data)}개 배치",
            "data": chart_data
        }
        
    except Exception as e:
        print(f"❌ 차트 데이터 생성 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"차트 데이터 생성 실패: {str(e)}"
        ) 