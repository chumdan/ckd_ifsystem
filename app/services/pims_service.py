"""
PIMS 데이터 조회 서비스
간단하게 MSSQL 프로시저를 호출해서 결과를 가져오는 함수들
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
    cursor = conn.cursor()
    
    # 프로시저 호출
    cursor.callproc('UP_AI_SearchProduct', [itemcode, batch_no, proc_code])
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results


def get_pims_data_basic(itemcode: str, batch_no: str, proc_code: str):
    """
    기존고형제 PIMS 데이터를 조회하는 함수
    Get_AIDATA 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호
        proc_code (str): 공정 코드
    
    Returns:
        list: 조회된 PIMS 데이터 리스트
    """
    # 데이터베이스 연결 정보 가져오기
    conn_info = get_mssql_connection_dict()
    
    # 데이터베이스에 연결
    conn = pymssql.connect(**conn_info)
    cursor = conn.cursor()
    
    # 프로시저 호출
    cursor.callproc('Get_AIDATA', [itemcode, batch_no, proc_code])
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results


def get_pims_data_l23(itemcode: str, batch_no: str, proc_code: str):
    """
    스마트고형제 PIMS 데이터를 조회하는 함수
    Get_AIDATA_L23 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호 (여러 개인 경우 쉼표로 구분)
        proc_code (str): 공정 코드
    
    Returns:
        list: 조회된 PIMS 데이터 리스트
    """
    # 데이터베이스 연결 정보 가져오기
    conn_info = get_mssql_connection_dict()
    
    # 데이터베이스에 연결
    conn = pymssql.connect(**conn_info)
    cursor = conn.cursor()
    
    # 프로시저 호출
    cursor.callproc('Get_AIDATA_L23', [itemcode, batch_no, proc_code])
    
    # 결과 가져오기
    results = cursor.fetchall()
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    return results