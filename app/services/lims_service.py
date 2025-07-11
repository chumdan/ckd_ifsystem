"""
LIMS 실험결과 조회 서비스
PIMS 서비스와 유사하지만 LIMS 전용 프로시저를 사용하는 함수들
"""

import pymssql
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any
from app.config import get_mssql_connection_dict

# PIMS 서비스의 유틸리티 함수들 재사용 (LIMS에서 필요한 것만)
from app.services.pims_service import (
    filter_and_convert_processes,
    load_process_type_mapping,
    load_process_variable_mapping
)


def load_lims_process_mapping() -> Dict[str, str]:
    """
    LIMS용 공정명 매핑 CSV 파일을 읽어서 공정코드 -> 한글공정명 매핑 딕셔너리를 반환합니다.
    
    Returns:
        Dict[str, str]: {공정코드: 한글공정명} 형태의 딕셔너리
    """
    try:
        # LIMS용 CSV 파일 경로 (app 폴더 기준)
        csv_path = os.path.join(os.path.dirname(__file__), '..', '공정name_LIMS.csv')
        
        # CSV 파일 읽기
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 딕셔너리로 변환 (KTSCH -> LTXA1)
        process_mapping = dict(zip(df['KTSCH'].str.strip(), df['LTXA1'].str.strip()))
        
        print(f"공정명 매핑 로드 완료 (LIMS용): {len(process_mapping)}개")
        return process_mapping
        
    except Exception as e:
        print(f"LIMS 공정명 매핑 로드 실패: {e}")
        return {}


def search_product_qc(itemcode: str, batch_no: str = "", proc_code: str = ""):
    """
    LIMS용 품목 조회 함수
    UP_AI_SearchProduct_QC 프로시저를 사용합니다.
    
    Args:
        itemcode (str): 품목 코드 (필수)
        batch_no (str): 배치 번호 (선택, 빈 문자열이면 모든 배치 조회)
        proc_code (str): 공정 코드 (선택)
    
    Returns:
        dict: {"batches": [...], "processes": [...]} 형태의 조회 결과
    """
    
    print(f"🔍 LIMS 품목 조회 시작: {itemcode}, {batch_no}, {proc_code}")
    
    # DB 연결 정보 가져오기
    conn_dict = get_mssql_connection_dict()
    
    try:
        # DB 연결
        conn = pymssql.connect(
            server=conn_dict['server'],
            user=conn_dict['user'],
            password=conn_dict['password'],
            database=conn_dict['database'],
            charset='utf8'
        )
        
        cursor = conn.cursor(as_dict=True)
        
        # LIMS용 프로시저 호출
        query = """
        DECLARE @return_value int;
        EXEC @return_value = [dbo].[UP_AI_SearchProduct_QC] 
        @itemcode = %s, 
        @BatchNo = %s, 
        @ProcCode = %s;
        """
        
        print(f"🗃️ 프로시저 실행: UP_AI_SearchProduct_QC")
        print(f"   - itemcode: {itemcode}")
        print(f"   - batch_no: {batch_no}")
        print(f"   - proc_code: {proc_code}")
        
        cursor.execute(query, (itemcode, batch_no, proc_code))
        
        # 모든 결과 가져오기
        raw_results = cursor.fetchall()
        
        if not raw_results:
            print("⚠️ 조회된 데이터가 없습니다.")
            return {"batches": [], "processes": []}
        
        print(f"✅ 프로시저 실행 완료: {len(raw_results)}건 조회")
        
        # 배치 리스트 추출 (중복 제거)
        batches = []
        batch_set = set()
        
        for row in raw_results:
            batch_no = row.get('CHARG', '')
            if batch_no and batch_no not in batch_set:
                batches.append({
                    'KBATCH': batch_no,
                    'batch_display': batch_no  # 화면 표시용
                })
                batch_set.add(batch_no)
        
        # 공정 리스트 추출 (중복 제거)
        processes = []
        process_set = set()
        
        # LIMS용 공정명 매핑 로드
        process_mapping = load_lims_process_mapping()
        
        for row in raw_results:
            proc_code = row.get('KTSCH', '')
            if proc_code and proc_code not in process_set:
                # 한글 공정명 찾기
                process_name = process_mapping.get(proc_code, proc_code)
                
                processes.append({
                    'KTSCH': proc_code,
                    'PROCESS_NAME_KOR': process_name,
                    'process_display': f"{proc_code} - {process_name}"
                })
                process_set.add(proc_code)
        
        # 공정명 매핑에 있는 것만 필터링
        filtered_processes = filter_and_convert_processes(processes, process_mapping)
        
        result = {
            "batches": batches,
            "processes": filtered_processes
        }
        
        print(f"🎯 LIMS 품목 조회 완료: 배치 {len(batches)}개, 공정 {len(filtered_processes)}개")
        
        return result
        
    except Exception as e:
        print(f"❌ LIMS 품목 조회 오류: {e}")
        raise e
        
    finally:
        if 'conn' in locals():
            conn.close()


def get_lims_data(itemcode: str, batch_no: str, proc_code: str) -> List[Dict[str, Any]]:
    """
    LIMS 실험결과 데이터 조회 함수
    UP_LIMS_Get_AI_LIMSDATA 프로시저를 사용합니다.
    
    참고: LIMS는 시간 정보가 필요 없어서 시간 관련 파라미터를 제거했습니다.
          또한 태그변형 처리를 하지 않고 원본 컬럼명을 그대로 사용합니다.
    
    Args:
        itemcode (str): 품목 코드 (필수)
        batch_no (str): 배치 번호 (필수, 다중 선택 시 쉼표로 구분)
        proc_code (str): 공정 코드 (필수)
    
    Returns:
        List[Dict[str, Any]]: LIMS 실험결과 데이터 리스트 (원본 컬럼명 그대로)
    """
    
    print(f"🔍 LIMS 실험결과 조회 시작: {itemcode}, {batch_no}, {proc_code}")
    
    # DB 연결 정보 가져오기
    conn_dict = get_mssql_connection_dict()
    
    try:
        # DB 연결
        conn = pymssql.connect(
            server=conn_dict['server'],
            user=conn_dict['user'],
            password=conn_dict['password'],
            database=conn_dict['database'],
            charset='utf8'
        )
        
        cursor = conn.cursor(as_dict=True)
        
        # LIMS용 프로시저 호출
        query = """
        DECLARE @return_value int;
        EXEC @return_value = [dbo].[UP_LIMS_Get_AI_LIMSDATA] 
        @itemcode = %s, 
        @BatchNo = %s, 
        @ProcCode = %s;
        """
        
        print(f"🗃️ 프로시저 실행: UP_LIMS_Get_AI_LIMSDATA")
        print(f"   - itemcode: {itemcode}")
        print(f"   - batch_no: {batch_no}")
        print(f"   - proc_code: {proc_code}")
        
        cursor.execute(query, (itemcode, batch_no, proc_code))
        
        # 모든 결과 가져오기
        raw_results = cursor.fetchall()
        
        if not raw_results:
            print("⚠️ 조회된 LIMS 데이터가 없습니다.")
            return []
        
        print(f"✅ LIMS 프로시저 실행 완료: {len(raw_results)}건 조회")
        
        # LIMS에서는 원본 컬럼명 그대로 사용 (태그변형 처리 안함)
        print("📋 LIMS는 원본 컬럼명을 그대로 사용합니다.")
        
        print(f"🎯 LIMS 실험결과 조회 완료: {len(raw_results)}건")
        
        return raw_results
        
    except Exception as e:
        print(f"❌ LIMS 실험결과 조회 오류: {e}")
        raise e
        
    finally:
        if 'conn' in locals():
            conn.close()


def filter_data_by_process_type(data: List[Dict[str, Any]], proc_code: str) -> List[Dict[str, Any]]:
    """
    공정별 변수 매핑에 따라 데이터를 필터링하는 함수
    PIMS 서비스의 동일한 함수를 재사용합니다.
    
    Args:
        data: 원본 데이터 리스트
        proc_code: 공정 코드
    
    Returns:
        List[Dict[str, Any]]: 필터링된 데이터 리스트
    """
    # PIMS 서비스의 함수를 그대로 재사용
    from app.services.pims_service import filter_data_by_process_type as pims_filter
    return pims_filter(data, proc_code)


def get_lims_data_with_multiple_batches(itemcode: str, batch_list: List[str], proc_code: str) -> List[Dict[str, Any]]:
    """
    여러 배치의 LIMS 데이터를 한 번에 조회하는 함수
    
    Args:
        itemcode (str): 품목 코드
        batch_list (List[str]): 배치 번호 리스트
        proc_code (str): 공정 코드
    
    Returns:
        List[Dict[str, Any]]: 모든 배치의 LIMS 데이터를 합친 리스트
    """
    
    if not batch_list:
        return []
    
    # 배치 리스트를 쉼표로 연결
    batch_no_str = ','.join(batch_list)
    
    # 통합 조회
    return get_lims_data(
        itemcode=itemcode,
        batch_no=batch_no_str,
        proc_code=proc_code
    )


def validate_lims_request(itemcode: str, batch_no: str, proc_code: str) -> Dict[str, Any]:
    """
    LIMS 조회 요청 데이터를 검증하는 함수
    
    Args:
        itemcode: 품목 코드
        batch_no: 배치 번호
        proc_code: 공정 코드
    
    Returns:
        Dict[str, Any]: {"valid": bool, "message": str} 형태의 검증 결과
    """
    
    # 필수 필드 검증
    if not itemcode or not itemcode.strip():
        return {"valid": False, "message": "품목 코드는 필수입니다."}
    
    if not batch_no or not batch_no.strip():
        return {"valid": False, "message": "배치 번호는 필수입니다."}
    
    if not proc_code or not proc_code.strip():
        return {"valid": False, "message": "공정 코드는 필수입니다."}
    
    # 배치 번호 개수 제한 (성능 고려)
    batch_list = [b.strip() for b in batch_no.split(',') if b.strip()]
    if len(batch_list) > 20:
        return {"valid": False, "message": "배치 번호는 최대 20개까지 선택 가능합니다."}
    
    return {"valid": True, "message": "검증 성공"}


def get_lims_summary_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    LIMS 데이터의 간단한 요약 통계를 계산하는 함수
    
    Args:
        data: LIMS 데이터 리스트
    
    Returns:
        Dict[str, Any]: 요약 통계 정보
    """
    
    if not data:
        return {
            "total_rows": 0,
            "batch_count": 0,
            "variable_count": 0,
            "date_range": None
        }
    
    # 기본 통계
    total_rows = len(data)
    
    # 배치 개수 계산
    batch_set = set()
    for row in data:
        batch_no = row.get('배치번호') or row.get('CHARG', '') or row.get('KBATCH', '')
        if batch_no:
            batch_set.add(batch_no)
    
    batch_count = len(batch_set)
    
    # 변수 개수 계산 (숫자형 컬럼만)
    if data:
        import pandas as pd
        df = pd.DataFrame(data)
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        variable_count = len(numeric_columns)
    else:
        variable_count = 0
    
    return {
        "total_rows": total_rows,
        "batch_count": batch_count,
        "variable_count": variable_count,
        "batches": list(batch_set)
    } 