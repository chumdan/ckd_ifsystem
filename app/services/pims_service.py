"""
PIMS 데이터 조회 서비스
장고 방식처럼 직접 SQL 쿼리를 실행해서 결과를 가져오는 함수들
"""

import pymssql
import pandas as pd
import os
from datetime import datetime
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


def load_process_mapping() -> Dict[str, str]:
    """
    공정명 매핑 CSV 파일을 읽어서 공정코드 -> 한글공정명 매핑 딕셔너리를 반환합니다.
    
    Returns:
        Dict[str, str]: {공정코드: 한글공정명} 형태의 딕셔너리
    """
    try:
        # CSV 파일 경로 (app 폴더 기준)
        csv_path = os.path.join(os.path.dirname(__file__), '..', '공정name.csv')
        
        # CSV 파일 읽기
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 딕셔너리로 변환 (KTSCH -> LTXA1)
        process_mapping = dict(zip(df['KTSCH'].str.strip(), df['LTXA1'].str.strip()))
        
        print(f"공정명 매핑 로드 완료: {len(process_mapping)}개")
        return process_mapping
        
    except Exception as e:
        print(f"공정명 매핑 로드 실패: {e}")
        return {}


def filter_and_convert_processes(data: List[Dict[str, Any]], process_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    공정 데이터를 필터링하고 한글명으로 변환합니다.
    
    Args:
        data: 원본 공정 데이터 리스트
        process_mapping: 공정명 매핑 딕셔너리
    
    Returns:
        List[Dict[str, Any]]: 필터링되고 한글명으로 변환된 공정 데이터 리스트
    """
    if not data or not process_mapping:
        return data
    
    filtered_data = []
    
    for row in data:
        proc_code = row.get('KTSCH', '').strip()
        
        # 공정명 매핑에 있는 공정코드만 포함
        if proc_code in process_mapping:
            # 새로운 행 생성 (원본 데이터 복사)
            new_row = dict(row)
            # 공정명을 한글로 변환해서 추가 (기존 KTSCH는 유지)
            new_row['PROCESS_NAME_KOR'] = process_mapping[proc_code]
            filtered_data.append(new_row)
    
    return filtered_data


def filter_by_time_range(data: List[Dict[str, Any]], start_time: str, end_time: str, tag_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    시간 범위로 데이터를 필터링합니다.
    
    Args:
        data: 원본 데이터 리스트 (한글 컬럼명으로 변환된 상태)
        start_time: 시작 시간 (YYYY-MM-DD HH:MM:SS 형태)
        end_time: 종료 시간 (YYYY-MM-DD HH:MM:SS 형태)
        tag_mapping: 태그 매핑 딕셔너리 (시간 컬럼명을 찾기 위해)
    
    Returns:
        List[Dict[str, Any]]: 시간 범위로 필터링된 데이터 리스트
    """
    if not data or not start_time or not end_time:
        return data
    
    # 태그 매핑에서 '시간' 컬럼명 찾기 (한글명)
    time_column = None
    for eng_col, kor_col in tag_mapping.items():
        if kor_col == '시간':
            time_column = kor_col
            break
    
    if not time_column:
        print("시간 컬럼을 찾을 수 없어서 시간 필터링을 건너뜁니다.")
        return data
    
    try:
        # 시작/종료 시간을 datetime 객체로 변환
        # HTML datetime-local 형태 처리: 2024-05-23T21:04 -> 2024-05-23 21:04:00
        def parse_input_time(time_str):
            time_str = time_str.strip()
            if 'T' in time_str:
                # T를 공백으로 변경
                time_str = time_str.replace('T', ' ')
            
            # 초가 없으면 :00 추가
            if time_str.count(':') == 1:
                time_str += ':00'
            
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        
        start_dt = parse_input_time(start_time)
        end_dt = parse_input_time(end_time)
        
        filtered_data = []
        
        for row in data:
            time_value = row.get(time_column)
            if time_value:
                try:
                    # 데이터의 시간 값을 datetime으로 변환
                    # 2024-05-23 9:05:10 형태에서 앞에 공백이 있을 수 있으므로 strip 처리
                    time_str = str(time_value).strip()
                    
                    # 시간 형태 정규화 (한 자리 시간을 두 자리로)
                    # "2024-05-23 9:05:10" -> "2024-05-23 09:05:10"
                    if ' ' in time_str:
                        date_part, time_part = time_str.split(' ', 1)
                        time_parts = time_part.split(':')
                        if len(time_parts) >= 3:
                            hour = time_parts[0].zfill(2)  # 한 자리 시간을 두 자리로
                            minute = time_parts[1].zfill(2)
                            second = time_parts[2].zfill(2)
                            time_str = f"{date_part} {hour}:{minute}:{second}"
                    
                    row_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    
                    # 시간 범위 체크
                    if start_dt <= row_dt <= end_dt:
                        filtered_data.append(row)
                        
                except ValueError as e:
                    print(f"시간 파싱 오류 ('{time_value}'): {e}")
                    # 파싱 오류가 있어도 해당 행은 포함 (안전장치)
                    filtered_data.append(row)
        
        print(f"시간 필터링 완료: {len(data)}건 -> {len(filtered_data)}건")
        return filtered_data
        
    except Exception as e:
        print(f"시간 필터링 오류: {e}")
        return data


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


def get_pims_data_with_batch_times(itemcode: str, batches_with_times: dict, proc_code: str, limit: int = 50, data_type: str = "basic") -> List[Dict[str, Any]]:
    """
    배치별 개별 시간 설정으로 PIMS 데이터를 조회합니다.
    
    Args:
        itemcode: 품목 코드
        batches_with_times: 배치별 시간 정보 딕셔너리 
                           {"배치번호": {"start": "시작시간", "end": "종료시간"}}
        proc_code: 공정 코드
        limit: 조회 건수 제한
        data_type: 데이터 타입 ("basic" 또는 "l23")
    
    Returns:
        List[Dict[str, Any]]: 모든 배치의 조회 결과를 병합한 데이터 리스트
    """
    all_results = []
    
    for batch_no, time_range in batches_with_times.items():
        start_time = time_range.get('start') or ""
        end_time = time_range.get('end') or ""
        
        print(f"배치 {batch_no} 조회: {start_time} ~ {end_time}")
        
        try:
            # 배치별로 개별 조회
            if data_type == "basic":
                batch_results = get_pims_data_basic(itemcode, batch_no, proc_code, start_time, end_time, limit)
            else:  # l23
                batch_results = get_pims_data_l23(itemcode, batch_no, proc_code, start_time, end_time, limit)
            
            if batch_results:
                print(f"배치 {batch_no}: {len(batch_results)}건 조회됨")
                all_results.extend(batch_results)
            else:
                print(f"배치 {batch_no}: 조회된 데이터 없음")
                
        except Exception as e:
            print(f"배치 {batch_no} 조회 오류: {e}")
            continue
    
    print(f"전체 조회 완료: {len(all_results)}건 (배치 {len(batches_with_times)}개)")
    return all_results


def search_product(itemcode: str, batch_no: str = "", proc_code: str = ""):
    """
    품목 정보를 조회하는 함수
    UP_AI_SearchProduct 프로시저를 호출합니다.
    
    Args:
        itemcode (str): 품목 코드
        batch_no (str): 배치 번호 (선택사항)
        proc_code (str): 공정 코드 (선택사항)
    
    Returns:
        list: 조회된 결과 리스트 (배치/공정 목록용이므로 영문 컬럼명 유지, 공정은 한글명 추가)
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
    
    # 공정명 매핑 로드 및 공정 필터링/변환 (공정코드가 있는 경우만)
    if proc_code == "":  # 공정 목록 조회인 경우
        process_mapping = load_process_mapping()
        results = filter_and_convert_processes(results, process_mapping)
    
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
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    # 태그 매핑 로드 및 컬럼명 변환
    tag_mapping = load_tag_mapping()
    converted_results = convert_columns_to_korean(results, tag_mapping)
    
    # 성능 최적화: 웹 조회(limit > 0)와 다운로드(limit <= 0)를 다르게 처리
    if limit > 0:
        # 웹 조회: 빠른 응답을 위해 처리 순서 최적화
        if start_time and end_time:
            # 시간 필터링이 있으면 정확성을 위해 필터링 후 limit 적용
            converted_results = filter_by_time_range(converted_results, start_time, end_time, tag_mapping)
            converted_results = converted_results[:limit]
        else:
            # 시간 필터링이 없으면 바로 limit 적용 (매우 빠름)
            converted_results = converted_results[:limit]
    else:
        # 다운로드: 정확한 데이터를 위해 시간 필터링 후 모든 데이터
        if start_time and end_time:
            converted_results = filter_by_time_range(converted_results, start_time, end_time, tag_mapping)
    
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
    
    # 연결 닫기
    cursor.close()
    conn.close()
    
    # 태그 매핑 로드 및 컬럼명 변환
    tag_mapping = load_tag_mapping()
    converted_results = convert_columns_to_korean(results, tag_mapping)
    
    # 성능 최적화: 웹 조회(limit > 0)와 다운로드(limit <= 0)를 다르게 처리
    if limit > 0:
        # 웹 조회: 빠른 응답을 위해 처리 순서 최적화
        if start_time and end_time:
            # 시간 필터링이 있으면 정확성을 위해 필터링 후 limit 적용
            converted_results = filter_by_time_range(converted_results, start_time, end_time, tag_mapping)
            converted_results = converted_results[:limit]
        else:
            # 시간 필터링이 없으면 바로 limit 적용 (매우 빠름)
            converted_results = converted_results[:limit]
    else:
        # 다운로드: 정확한 데이터를 위해 시간 필터링 후 모든 데이터
        if start_time and end_time:
            converted_results = filter_by_time_range(converted_results, start_time, end_time, tag_mapping)
    
    return converted_results


def load_process_type_mapping() -> Dict[str, str]:
    """
    공정그룹.csv 파일을 읽어서 공정코드 → 공정타입 매핑 딕셔너리를 반환
    
    예: {'AB0': '과립', 'AH0': '타정', 'AI0': '코팅'}
    
    Returns:
        Dict[str, str]: {공정코드: 공정타입} 형태의 딕셔너리
    """
    try:
        # CSV 파일 경로 (app 폴더 안)
        csv_path = os.path.join(os.path.dirname(__file__), '..', '공정그룹.csv')
        
        # CSV 파일 읽기 (한글 인코딩)
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 딕셔너리로 변환 (공정코드 → 공정타입)
        process_type_mapping = dict(zip(df['공정코드'].str.strip(), df['공정타입'].str.strip()))
        
        print(f"📋 공정타입 매핑 로드 완료: {len(process_type_mapping)}개")
        return process_type_mapping
        
    except Exception as e:
        print(f"❌ 공정타입 매핑 로드 실패: {e}")
        return {}


def load_process_variable_mapping() -> Dict[str, List[str]]:
    """
    공정변수매핑.csv 파일을 읽어서 공정타입 → 변수목록 매핑 딕셔너리를 반환
    
    예: {'과립': ['L11_1110_FBG5_AIR_F', ...], '룸상태': ['L23_2526_REMS_T', ...]}
    
    Returns:
        Dict[str, List[str]]: {공정타입: [변수명들]} 형태의 딕셔너리
    """
    try:
        # CSV 파일 경로 (app 폴더 안)
        csv_path = os.path.join(os.path.dirname(__file__), '..', '공정변수매핑.csv')
        
        # CSV 파일 읽기 (한글 인코딩)
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 공정타입별로 변수들을 그룹화
        process_variable_mapping = {}
        for process_type in df['공정타입'].unique():
            # 해당 공정타입의 모든 변수들을 리스트로 수집
            variables = df[df['공정타입'] == process_type]['변수명(영문)'].str.strip().tolist()
            process_variable_mapping[process_type] = variables
        
        print(f"📋 공정변수 매핑 로드 완료: {len(process_variable_mapping)}개 공정타입")
        
        # 각 공정타입별 변수 개수 출력 (디버깅용)
        for ptype, variables in process_variable_mapping.items():
            print(f"  - {ptype}: {len(variables)}개 변수")
            
        return process_variable_mapping
        
    except Exception as e:
        print(f"❌ 공정변수 매핑 로드 실패: {e}")
        return {}


def filter_data_by_process_type(data: List[Dict[str, Any]], proc_code: str) -> List[Dict[str, Any]]:
    """
    선택된 공정코드에 따라 관련 변수들만 필터링하는 함수
    
    📌 필터링 규칙:
    1. 선택된 공정의 타입에 해당하는 변수들
    2. 룸상태 변수들 (모든 공정에서 항상 표시)
    3. 기본 시스템 변수들 (시간, 배치번호 등)
    
    Args:
        data: 원본 PIMS 데이터 리스트 (한글 컬럼명으로 변환된 상태)
        proc_code: 선택된 공정코드 (예: 'AB1', 'AH0')
    
    Returns:
        List[Dict[str, Any]]: 필터링된 데이터 리스트
    """
    # 데이터가 없으면 그대로 반환
    if not data:
        print("⚠️  필터링할 데이터가 없습니다.")
        return data
    
    print(f"🔍 공정코드 '{proc_code}'에 대한 데이터 필터링 시작...")
    
    # 1. 매핑 정보 로드
    process_type_mapping = load_process_type_mapping()       # 공정코드 → 공정타입
    process_variable_mapping = load_process_variable_mapping()  # 공정타입 → 변수목록
    tag_mapping = load_tag_mapping()  # 영문 → 한글 변수명 매핑
    
    # 2. 선택된 공정의 타입 확인
    process_type = process_type_mapping.get(proc_code, "")
    
    if not process_type:
        print(f"⚠️  공정코드 '{proc_code}'의 타입을 찾을 수 없습니다. 필터링 안함.")
        return data  # 필터링 없이 원본 데이터 반환
    
    print(f"✅ 공정코드 '{proc_code}' → 공정타입 '{process_type}'")
    
    # 3. 표시할 변수들 수집 (허용된 변수들의 집합) - 영문명으로 수집 후 한글명으로 변환
    allowed_variables_eng = set()
    
    # 3-1. 선택된 공정타입의 변수들 추가
    if process_type in process_variable_mapping:
        type_variables = process_variable_mapping[process_type]
        allowed_variables_eng.update(type_variables)
        print(f"📊 '{process_type}' 공정변수: {len(type_variables)}개 추가")
    
    # 3-2. 룸상태 변수들 추가 (모든 공정에서 표시)
    if "룸상태" in process_variable_mapping:
        room_variables = process_variable_mapping["룸상태"]
        allowed_variables_eng.update(room_variables)
        print(f"🏠 룸상태 변수: {len(room_variables)}개 추가")
    
    # 3-3. 기본 시스템 변수들 추가 (항상 표시) - 영문명
    basic_variables_eng = [
        "AUFNR",           # 작업번호
        "MATNR",           # 품목코드  
        "CHARG",           # 배치번호
        "ACT_START",       # 시작시각
        "ACT_FINISH",      # 종료시각
        "VORNR",           # 작업순서
        "KTSCH",           # 공정코드
        "ACT_FINISH_TIMS", # 총시간(초)
        "STATUS3",         # 상태(X=종료)
        "KTEXT",           # 설비정보
        "ITIME"            # 시간
    ]
    allowed_variables_eng.update(basic_variables_eng)
    print(f"⚙️  기본 시스템 변수: {len(basic_variables_eng)}개 추가")
    
    # 3-4. 영문명을 한글명으로 변환 (데이터는 이미 한글 컬럼명으로 변환된 상태)
    allowed_variables_kor = set()
    for eng_var in allowed_variables_eng:
        kor_var = tag_mapping.get(eng_var, eng_var)  # 한글명이 없으면 영문명 그대로
        allowed_variables_kor.add(kor_var)
    
    print(f"🎯 총 허용된 변수: {len(allowed_variables_kor)}개 (한글명 기준)")
    
    # 4. 데이터 필터링 실행
    filtered_data = []
    original_column_count = len(data[0].keys()) if data else 0
    
    for row in data:
        # 새로운 행 생성 (허용된 변수들만 포함)
        filtered_row = {}
        for key, value in row.items():
            if key in allowed_variables_kor:
                filtered_row[key] = value
        
        filtered_data.append(filtered_row)
    
    # 5. 필터링 결과 출력
    filtered_column_count = len(filtered_data[0].keys()) if filtered_data else 0
    print(f"✅ 필터링 완료: {original_column_count}개 → {filtered_column_count}개 컬럼")
    print(f"📈 데이터 행 수: {len(filtered_data)}건")
    
    return filtered_data