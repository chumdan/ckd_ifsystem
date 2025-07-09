"""
PIMS 데이터 조회 서비스
장고 방식처럼 직접 SQL 쿼리를 실행해서 결과를 가져오는 함수들
"""

import pymssql
import pandas as pd
import os
from typing import Dict, List, Any
from app.config import get_mssql_connection_dict


def load_tag_mapping() -> Dict[str, str]:
    """
    태그 매핑 CSV 파일을 읽어서 영문 -> 한글 매핑 딕셔너리를 반환합니다.
    
    Returns:
        Dict[str, str]: {영문컬럼명: 한글컬럼명} 형태의 딕셔너리
    """
    try:
        # CSV 파일 경로 (app 폴더 기준)
        csv_path = os.path.join(os.path.dirname(__file__), '..', '태그변형.csv')
        
        # CSV 파일 읽기
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 딕셔너리로 변환 (original_nam -> display_name)
        tag_mapping = dict(zip(df['original_nam'].str.strip(), df['display_name'].str.strip()))
        
        print(f"태그 매핑 로드 완료: {len(tag_mapping)}개")
        return tag_mapping
        
    except Exception as e:
        print(f"태그 매핑 로드 실패: {e}")
        return {}


def convert_columns_to_korean(data: List[Dict[str, Any]], tag_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    데이터의 컬럼명을 영문에서 한글로 변환합니다.
    
    Args:
        data: 원본 데이터 리스트
        tag_mapping: 태그 매핑 딕셔너리
    
    Returns:
        List[Dict[str, Any]]: 컬럼명이 한글로 변환된 데이터 리스트
    """
    if not data or not tag_mapping:
        return data
    
    converted_data = []
    
    for row in data:
        converted_row = {}
        for eng_col, value in row.items():
            # 태그 매핑에서 한글명 찾기 (없으면 원본 컬럼명 사용)
            kor_col = tag_mapping.get(eng_col, eng_col)
            converted_row[kor_col] = value
        converted_data.append(converted_row)
    
    return converted_data


def search_product(itemcode: str, batch_no: str = "", proc_code: str = ""):
    """
    품목 정보를 조회하는 함수
    UP_AI_SearchProduct 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호 (선택사항)
        proc_code (str): 공정 코드 (선택사항)
    
    Returns:
        list: 조회된 결과 리스트 (배치/공정 목록용이므로 영문 컬럼명 유지)
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
    
    # 배치/공정 목록 조회는 프론트엔드에서 CHARG, KTSCH로 접근하므로 영문 컬럼명 유지
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
        limit (int): 조회 건수 제한 (기본: 50건, 0 이하면 모든 데이터)
    
    Returns:
        list: 조회된 PIMS 데이터 리스트 (최대 limit 건, limit <= 0이면 모든 데이터, 컬럼명은 한글로 변환됨)
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
    # limit이 0 이하면 모든 데이터 반환 (다운로드용)
    if limit > 0:
        results = results[:limit]
    
    # 시간 설정이 없으면 모든 데이터 반환
    # 시간 설정이 있으면 향후 필터링 로직 추가 예정
    # 현재는 프로시저에서 반환된 데이터를 limit만큼만 반환
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    # 태그 매핑 로드 및 컬럼명 변환
    tag_mapping = load_tag_mapping()
    converted_results = convert_columns_to_korean(results, tag_mapping)
    
    return converted_results


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
        limit (int): 조회 건수 제한 (기본: 50건, 0 이하면 모든 데이터)
    
    Returns:
        list: 조회된 PIMS 데이터 리스트 (최대 limit 건, limit <= 0이면 모든 데이터, 컬럼명은 한글로 변환됨)
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
    # limit이 0 이하면 모든 데이터 반환 (다운로드용)
    if limit > 0:
        results = results[:limit]
    
    # 시간 설정이 있으면 향후 필터링 로직 추가 예정  
    # 현재는 프로시저에서 반환된 데이터를 limit만큼만 반환
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    # 태그 매핑 로드 및 컬럼명 변환
    tag_mapping = load_tag_mapping()
    converted_results = convert_columns_to_korean(results, tag_mapping)
    
    return converted_results