# CKD PIMS/LIMS 조회 시스템

회사의 PIMS, LIMS 시스템 데이터를 조회하는 웹 서비스입니다.

## 📋 기능

- **PIMS 데이터 조회**: 품목 코드로 배치 및 공정 정보 조회
- **고형제 타입 지원**: 
  - 기존고형제 (1-1): `Get_AIDATA` 프로시저
  - 스마트고형제 (2-3): `Get_AIDATA_L23` 프로시저

## 🛠 기술 스택

- **Backend**: FastAPI
- **Database**: MSSQL (pymssql)
- **Frontend**: Jinja2 템플릿 + Bootstrap
- **Python**: 3.11

## 🚀 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일에서 데이터베이스 연결 정보를 확인하세요.

### 3. 서버 실행
```bash
# 방법 1
uvicorn app.main:app --reload

# 방법 2  
python -m app.main
```

### 4. 접속
- 메인페이지: http://localhost:8000
- PIMS 조회: http://localhost:8000/pims

## 📁 프로젝트 구조

```
ckd_ifsystem/
├── app/
│   ├── controllers/     # API 컨트롤러
│   ├── services/        # 비즈니스 로직
│   ├── static/          # CSS, JS, 이미지
│   ├── templates/       # HTML 템플릿
│   ├── config.py        # 설정 파일
│   └── main.py          # FastAPI 앱
├── .env                 # 환경변수
├── requirements.txt     # Python 의존성
└── README.md
```

## 🔧 PIMS 조회 프로세스

1. **고형제 타입 선택**: 기존고형제 또는 스마트고형제
2. **품목 조회**: `UP_AI_SearchProduct` 프로시저로 배치 및 공정 조회
3. **데이터 조회**: 
   - 기존고형제: `Get_AIDATA` 프로시저
   - 스마트고형제: `Get_AIDATA_L23` 프로시저

## 📝 개발 현황

- [x] 프로젝트 기본 구조 설정
- [x] MSSQL 연결 설정
- [x] PIMS 서비스 함수 구현
- [x] FastAPI 기본 설정
- [ ] 웹 템플릿 구현
- [ ] API 엔드포인트 구현
- [ ] 사용자 인터페이스 완성