"""
PIMS 배치요약 서비스
PIMS 데이터를 통계량으로 압축하는 간단한 함수들
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any


def calculate_simple_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    PIMS 데이터를 하나의 행으로 통계 압축하는 함수
    
    입력: 3,000~10,000행의 PIMS 데이터 (리스트[딕셔너리])
    출력: 1행의 통계 데이터 (딕셔너리)
    
    각 변수별로 5개 통계량 계산:
    - 변수명_평균
    - 변수명_표준편차  
    - 변수명_25%
    - 변수명_50% (중앙값)
    - 변수명_75%
    
    예시:
    입력: [{"변수1": 10.5, "변수2": 20.1}, {"변수1": 10.7, "변수2": 20.3}, ...]
    출력: {"변수1_평균": 10.6, "변수1_표준편차": 0.1, "변수1_25%": 10.5, ...}
    """
    
    if not data:
        print("⚠️ 통계 계산할 데이터가 없습니다.")
        return {}
    
    print(f"📊 통계 계산 시작: {len(data)}행 → 1행으로 압축")
    
    try:
        # 1. 리스트[딕셔너리]를 pandas DataFrame으로 변환
        df = pd.DataFrame(data)
        print(f"📈 DataFrame 생성 완료: {df.shape[0]}행 × {df.shape[1]}컬럼")
        
        # 2. 숫자 컬럼만 선택 (문자열 컬럼 제외)
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        print(f"🔢 숫자 컬럼 개수: {len(numeric_columns)}개")
        
        if not numeric_columns:
            print("⚠️ 숫자 컬럼이 없어서 통계 계산을 할 수 없습니다.")
            return {"오류": "숫자 데이터가 없음"}
        
        # 3. 각 숫자 컬럼별로 통계량 계산
        stats_result = {}
        
        for column in numeric_columns:
            # null 값 제거
            series = df[column].dropna()
            
            if len(series) == 0:
                # 모든 값이 null인 경우
                stats_result[f"{column}_평균"] = None
                stats_result[f"{column}_표준편차"] = None  
                stats_result[f"{column}_25%"] = None
                stats_result[f"{column}_50%"] = None
                stats_result[f"{column}_75%"] = None
                continue
            
            # 통계량 계산
            try:
                mean_val = series.mean()
                std_val = series.std()
                q25_val = series.quantile(0.25)
                q50_val = series.quantile(0.50)  # 중앙값
                q75_val = series.quantile(0.75)
                
                # 결과에 추가 (소수점 4자리까지)
                stats_result[f"{column}_평균"] = round(mean_val, 4) if pd.notna(mean_val) else None
                stats_result[f"{column}_표준편차"] = round(std_val, 4) if pd.notna(std_val) else None
                stats_result[f"{column}_25%"] = round(q25_val, 4) if pd.notna(q25_val) else None
                stats_result[f"{column}_50%"] = round(q50_val, 4) if pd.notna(q50_val) else None
                stats_result[f"{column}_75%"] = round(q75_val, 4) if pd.notna(q75_val) else None
                
            except Exception as e:
                print(f"⚠️ {column} 컬럼 통계 계산 오류: {e}")
                stats_result[f"{column}_평균"] = None
                stats_result[f"{column}_표준편차"] = None
                stats_result[f"{column}_25%"] = None
                stats_result[f"{column}_50%"] = None
                stats_result[f"{column}_75%"] = None
        
        # 4. 원본 정보도 추가
        stats_result["원본데이터건수"] = len(data)
        stats_result["처리된변수개수"] = len(numeric_columns)
        stats_result["처리일시"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"✅ 통계 계산 완료: {len(numeric_columns)}개 변수 → {len(stats_result)}개 통계 컬럼")
        
        return stats_result
        
    except Exception as e:
        print(f"❌ 통계 계산 중 오류 발생: {e}")
        return {
            "오류": str(e),
            "원본데이터건수": len(data),
            "처리일시": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def calculate_batch_wise_statistics(data: List[Dict[str, Any]], batch_column: str = "배치번호") -> List[Dict[str, Any]]:
    """
    PIMS 데이터를 배치별로 분리하여 각각 통계 압축하는 함수
    
    입력: 여러 배치의 PIMS 데이터 (리스트[딕셔너리])
    출력: 배치별 통계 데이터 (리스트[딕셔너리])
    
    예시:
    입력: [{"배치번호": "A", "변수1": 10}, {"배치번호": "A", "변수1": 12}, 
           {"배치번호": "B", "변수1": 20}, {"배치번호": "B", "변수1": 22}]
    출력: [{"배치번호": "A", "변수1_평균": 11, ...}, 
           {"배치번호": "B", "변수1_평균": 21, ...}]
    """
    
    if not data:
        print("⚠️ 배치별 통계 계산할 데이터가 없습니다.")
        return []
    
    print(f"📊 배치별 통계 계산 시작: {len(data)}행")
    
    try:
        # 1. 데이터를 DataFrame으로 변환
        df = pd.DataFrame(data)
        
        # 2. 배치 컬럼이 없으면 에러
        if batch_column not in df.columns:
            print(f"⚠️ 배치 컬럼 '{batch_column}'이 데이터에 없습니다.")
            # 모든 데이터를 하나의 배치로 처리
            single_stats = calculate_simple_statistics(data)
            single_stats["배치번호"] = "전체"
            return [single_stats]
        
        # 3. 배치별로 데이터 분리
        unique_batches = df[batch_column].unique()
        print(f"🔍 발견된 배치: {list(unique_batches)} ({len(unique_batches)}개)")
        
        batch_stats_list = []
        
        # 4. 각 배치별로 통계 계산
        for batch_no in unique_batches:
            if pd.isna(batch_no):
                continue
                
            # 해당 배치 데이터만 필터링
            batch_data = df[df[batch_column] == batch_no]
            batch_dict_data = batch_data.to_dict('records')
            
            print(f"📈 {batch_no} 배치: {len(batch_dict_data)}행 처리 중...")
            
            # 배치별 통계 계산
            batch_stats = calculate_simple_statistics(batch_dict_data)
            
            if batch_stats:
                # 배치번호를 맨 앞에 추가
                batch_stats["배치번호"] = str(batch_no)
                batch_stats_list.append(batch_stats)
        
        print(f"✅ 배치별 통계 계산 완료: {len(batch_stats_list)}개 배치")
        return batch_stats_list
        
    except Exception as e:
        print(f"❌ 배치별 통계 계산 중 오류 발생: {e}")
        return []


def format_stats_for_display(stats_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    통계 데이터를 화면 표시용으로 포맷팅하는 함수
    
    필요하면 추가 포맷팅 로직 구현
    (예: None 값을 "-"로 표시, 긴 소수점 정리 등)
    """
    
    if not stats_data:
        return {}
    
    # 현재는 그대로 반환 (필요시 포맷팅 로직 추가)
    return stats_data


def convert_stats_to_excel(stats_data: Dict[str, Any]) -> bytes:
    """
    통계 데이터를 Excel 파일로 변환하는 함수 (다운로드용)
    
    향후 구현 예정:
    - pandas to_excel() 사용
    - BytesIO로 메모리 상에서 Excel 파일 생성
    - 바이트 데이터 반환
    """
    
    # TODO: 다음 단계에서 구현
    print("📁 Excel 변환 기능은 다음 단계에서 구현 예정")
    return b""


def generate_chart_data(stats_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    통계 데이터를 Chart.js용 차트 데이터로 변환하는 함수 (Python에서 모든 계산 처리)
    
    📊 생성되는 차트 데이터:
    1. 트렌드 차트용: 배치번호별 각 변수의 평균값
    2. 변동계수(CV) 차트용: 각 변수의 안정성 지표 (CV = 표준편차/평균 × 100)
    
    입력: 배치별 통계 데이터 (리스트[딕셔너리])
    출력: Chart.js용 데이터 구조 (딕셔너리)
    """
    
    if not stats_data:
        print("⚠️ 차트 생성할 통계 데이터가 없습니다.")
        return {
            "variables": [],
            "batches": [],
            "trend_data": {},
            "cv_data": {}
        }
    
    print(f"📊 차트 데이터 생성 시작: {len(stats_data)}개 배치")
    
    try:
        # 1. 배치 번호 추출 (X축 데이터)
        batches = []
        for row in stats_data:
            batch_no = row.get("배치번호", "")
            if batch_no and batch_no not in batches:
                batches.append(str(batch_no))
        
        batches.sort()  # 배치 번호 정렬
        print(f"📈 배치 목록: {batches}")
        
        # 2. 변수 목록 추출 (평균값이 있는 변수들만)
        variables = []
        
        # 첫 번째 배치에서 변수 목록 추출
        first_batch = stats_data[0] if stats_data else {}
        for key in first_batch.keys():
            if key.endswith("_평균") and key != "배치번호":
                # "변수명_평균"에서 "변수명" 추출
                variable_name = key.replace("_평균", "")
                variables.append(variable_name)
        
        variables.sort()  # 변수명 정렬
        print(f"🔢 변수 목록: {len(variables)}개 - {variables[:5]}..." if len(variables) > 5 else f"🔢 변수 목록: {variables}")
        
        # 3. 트렌드 차트용 데이터 생성 (배치별 각 변수의 평균값)
        trend_data = {}
        
        for variable in variables:
            trend_data[variable] = []
            
            for batch in batches:
                # 해당 배치의 해당 변수 평균값 찾기
                avg_value = None
                
                for row in stats_data:
                    if str(row.get("배치번호", "")) == batch:
                        avg_key = f"{variable}_평균"
                        avg_value = row.get(avg_key)
                        break
                
                trend_data[variable].append({
                    "batch": batch,
                    "value": avg_value if avg_value is not None else 0
                })
        
        # 4. 변동계수(CV) 차트용 데이터 생성
        cv_data = []
        
        for variable in variables:
            # 각 변수별로 전체 배치에서의 평균과 표준편차 수집
            avg_values = []
            std_values = []
            
            for row in stats_data:
                avg_key = f"{variable}_평균"
                std_key = f"{variable}_표준편차"
                
                avg_val = row.get(avg_key)
                std_val = row.get(std_key)
                
                if avg_val is not None and std_val is not None:
                    avg_values.append(avg_val)
                    std_values.append(std_val)
            
            # 변동계수 계산: CV = (표준편차의 평균 / 평균값의 평균) × 100
            if avg_values and std_values:
                overall_avg = np.mean(avg_values)  # 전체 배치의 평균값 평균
                overall_std = np.mean(std_values)  # 전체 배치의 표준편차 평균
                
                if overall_avg != 0:
                    cv_value = (overall_std / abs(overall_avg)) * 100
                    cv_data.append({
                        "variable": variable,
                        "cv": round(cv_value, 2),
                        "interpretation": "낮음" if cv_value < 5 else "보통" if cv_value < 15 else "높음"
                    })
        
        # CV 값으로 정렬 (낮은 것부터 = 안정적인 것부터)
        cv_data.sort(key=lambda x: x["cv"])
        
        # 5. 최종 차트 데이터 구조 생성
        chart_result = {
            "variables": variables,
            "batches": batches,
            "trend_data": trend_data,
            "cv_data": cv_data,
            "summary": {
                "total_variables": len(variables),
                "total_batches": len(batches),
                "most_stable_variable": cv_data[0]["variable"] if cv_data else None,
                "least_stable_variable": cv_data[-1]["variable"] if cv_data else None
            }
        }
        
        print(f"✅ 차트 데이터 생성 완료: {len(variables)}개 변수, {len(batches)}개 배치")
        print(f"📊 가장 안정적 변수: {chart_result['summary']['most_stable_variable']}")
        
        return chart_result
        
    except Exception as e:
        print(f"❌ 차트 데이터 생성 중 오류 발생: {e}")
        return {
            "variables": [],
            "batches": [],
            "trend_data": {},
            "cv_data": {},
            "error": str(e)
        } 