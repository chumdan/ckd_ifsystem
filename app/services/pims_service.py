"""
PIMS 데이터 조회 서비스
장고 방식처럼 직접 SQL 쿼리를 실행해서 결과를 가져오는 함수들
"""

import pymssql
from app.config import get_mssql_connection_dict


def search_product(itemcode: str, batch_no: str = "", proc_code: str = ""):
    """
    품목 정보를 조회하는 함수
    UP_AI_SearchProduct 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호 (선택사항)
        proc_code (str): 공정 코드 (선택사항)
    
    Returns:
        list: 조회된 결과 리스트
    """
    # 데이터베이스 연결 정보 가져오기
    conn_info = get_mssql_connection_dict()
    
    # 데이터베이스에 연결
    conn = pymssql.connect(**conn_info)
    cursor = conn.cursor(as_dict=True)  # 딕셔너리 형태로 결과 받기
    
    # SQL 쿼리 실행 (장고 방식처럼)
    query = """
        DECLARE @return_value int;
        EXEC @return_value = [dbo].[UP_AI_SearchProduct] 
        @itemcode = %s, 
        @BatchNo = %s, 
        @ProcCode = %s;
    """
    cursor.execute(query, (itemcode, batch_no, proc_code))
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results


def get_pims_data_basic(itemcode: str, batch_no: str, proc_code: str, start_time: str = "", end_time: str = "", limit: int = 50):
    """
    기존고형제 PIMS 데이터를 조회하는 함수
    Get_AIDATA 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호
        proc_code (str): 공정 코드
        start_time (str): 시작 시간 (선택사항)
        end_time (str): 종료 시간 (선택사항)
        limit (int): 조회 건수 제한 (기본: 50건)
    
    Returns:
        list: 조회된 PIMS 데이터 리스트 (최대 limit 건)
    """
    # 데이터베이스 연결 정보 가져오기
    conn_info = get_mssql_connection_dict()
    
    # 데이터베이스에 연결
    conn = pymssql.connect(**conn_info)
    cursor = conn.cursor(as_dict=True)  # 딕셔너리 형태로 결과 받기
    
    # SQL 쿼리 실행
    query = """
        DECLARE @return_value int; 
        EXEC @return_value = [dbo].[Get_AIDATA] 
        @itemcode = %s, 
        @BatchNo = %s, 
        @ProcCode = %s;
    """
    cursor.execute(query, (itemcode, batch_no, proc_code))
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # limit 건수만큼만 반환 (성능 최적화)
    if limit > 0:
        results = results[:limit]
    
    # 시간 설정이 없으면 모든 데이터 반환
    # 시간 설정이 있으면 향후 필터링 로직 추가 예정
    # 현재는 프로시저에서 반환된 데이터를 limit만큼만 반환
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results


def get_pims_data_l23(itemcode: str, batch_no: str, proc_code: str, start_time: str = "", end_time: str = "", limit: int = 50):
    """
    스마트고형제 PIMS 데이터를 조회하는 함수
    Get_AIDATA_L23 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호 (여러 개인 경우 쉼표로 구분)
        proc_code (str): 공정 코드
        start_time (str): 시작 시간 (선택사항)
        end_time (str): 종료 시간 (선택사항)
        limit (int): 조회 건수 제한 (기본: 50건)
    
    Returns:
        list: 조회된 PIMS 데이터 리스트 (최대 limit 건)
    """
    # 데이터베이스 연결 정보 가져오기
    conn_info = get_mssql_connection_dict()
    
    # 데이터베이스에 연결
    conn = pymssql.connect(**conn_info)
    cursor = conn.cursor(as_dict=True)  # 딕셔너리 형태로 결과 받기
    
    # SQL 쿼리 실행
    query = """
        DECLARE @return_value int; 
        EXEC @return_value = [dbo].[Get_AIDATA_L23] 
        @itemcode = %s, 
        @BatchNo = %s, 
        @ProcCode = %s;
    """
    cursor.execute(query, (itemcode, batch_no, proc_code))
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # limit 건수만큼만 반환 (성능 최적화)
    if limit > 0:
        results = results[:limit]
    
    # 시간 설정이 없으면 모든 데이터 반환
    # 시간 설정이 있으면 향후 필터링 로직 추가 예정  
    # 현재는 프로시저에서 반환된 데이터를 limit만큼만 반환
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results