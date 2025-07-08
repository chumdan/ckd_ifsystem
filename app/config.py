"""
설정 파일 - .env 파일의 환경변수를 읽어와서 관리합니다.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    애플리케이션 설정을 관리하는 클래스
    .env 파일에서 환경변수를 자동으로 읽어옵니다.
    """
    
    # FastAPI 기본 설정
    app_name: str = "CKD PIMS/LIMS 조회 시스템"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your-secret-key-here"
    
    # MSSQL 데이터베이스 연결 설정
    mssql_server: str = "192.168.142.68"
    mssql_database: str = "AI"
    mssql_username: str = "aiadmin"
    mssql_password: str = "%AiMeta0109&"
    mssql_driver: str = "ODBC Driver 17 for SQL Server"
    
    # 로그 설정
    log_level: str = "INFO"
    
    class Config:
        """
        Pydantic 설정 클래스
        .env 파일에서 환경변수를 읽어오도록 설정
        """
        env_file = ".env"  # .env 파일에서 환경변수 읽기
        case_sensitive = False  # 대소문자 구분 안함 (MSSQL_SERVER나 mssql_server 둘 다 인식)


# 설정 객체 생성 - 애플리케이션 전체에서 사용할 설정 인스턴스
settings = Settings()


def get_mssql_connection_string() -> str:
    """
    MSSQL 데이터베이스 연결 문자열을 생성하는 함수
    
    Returns:
        str: MSSQL 연결을 위한 connection string
    """
    # pymssql 라이브러리용 연결 문자열 생성
    connection_string = (
        f"mssql+pymssql://{settings.mssql_username}:{settings.mssql_password}"
        f"@{settings.mssql_server}/{settings.mssql_database}"
    )
    return connection_string


def get_mssql_connection_dict() -> dict:
    """
    MSSQL 연결 정보를 딕셔너리 형태로 반환하는 함수
    pymssql.connect() 함수에 직접 전달할 수 있는 형태
    
    Returns:
        dict: MSSQL 연결 정보가 담긴 딕셔너리
    """
    return {
        "server": settings.mssql_server,
        "database": settings.mssql_database,
        "user": settings.mssql_username,
        "password": settings.mssql_password,
        "charset": "utf8"  # 한글 처리를 위한 문자셋 설정
    }