# AI 기반의 지능형 쿼리 분석 시스템

**📖 프로젝트 개요**
- 데이터베이스 쿼리 로그를 분석하고 AI 기반 튜닝 제안을 제공하는 웹 애플리케이션입니다. 
- PostgreSQL, MariaDB, MySQL 등 다양한 DBMS의 로그를 분석하여 슬로우 쿼리와 에러 쿼리에 대한 최적화 제안을 제공합니다.


## ✨ 주요 기능
- 다중 DBMS 지원: PostgreSQL, MariaDB, MySQL 로그 분석
- 슬로우 쿼리 분석: 사용자 정의 임계값 기반 성능 쿼리 탐지
- 에러 쿼리 분석: 실행 오류 쿼리 자동 감지
- AI 튜닝 제안: OpenAI GPT 모델을 활용한 최적화 제안
- 유사 쿼리 검색: Azure AI Search 기반 자연어(키워드) 검색
- 사용자 관리: 관리자/일반 사용자 관리 
- 프로젝트 관리: 다중 프로젝트 환경 지원
- 다국어 지원: 한국어, 영어, 베트남어 튜닝 제안

## 🛠 사용 기술 스택
- Database: SQLite (개발환경)
- State Managemnet: Steamlit Session State
- File Upload: Streamlit File Uploader
- AI & Search
  - OpenAI API: GPT 모델을 통한 튜닝 제안
  - Azure AI Search: 검색 및 유사 쿼리 매칭
  - Azure Blob Storage: 로그 파일 저장
- UI Framework: Streamlit
  - Components
    - streamlit-option-menu
    - streamlit-aggrid
- Styling: Custom CSS

## 📦 Python 패키지 의존성
- streamlit
- streamlit-option-menu
- streamlit-aggrid
- pandas
- sqlite3
- requests
- openai
- azure-storage-blob
- azure-search-documents
- python-dotenv
- bcrypt
- uuid
- datetime
- html
- urllib

## 🏗 프로젝트 구조
<pre lang="markdown"> <code>
SMART-QUERY-AI/```
├── app.py                     # 메인 애플리케이션
├── requirements.txt           # 의존성 패키지
├── .env                       # 환경 변수
├── README.md                  
├── .gitignore                 
├── ai/                        # AI 모듈
│   ├── __init__.py
│   ├── blob.py                # Azure Blob Storage
│   ├── openai_client.py       # OpenAI API 클라이언트
│   └── search_client.py       # Azure Search 클라이언트
├── auth/                      # 인증 모듈
│   ├── __init__.py
│   ├── login.py               # 로그인 처리
│   ├── password.py            # 비밀번호 암호화
│   └── session.py             # 세션 관리
├── database/                  # 데이터베이스 모듈
│   ├── __init__.py
│   ├── connection.py          # DB 연결
│   ├── login_log.py           # 로그인 로그
│   ├── project.py             # 프로젝트 관리
│   ├── query_log.py           # 쿼리 로그
│   ├── user.py                # 사용자 관리
│   └── user_project.py        # 사용자 프로젝트 매핑
├── parser/                    # 로그 파서 모듈
│   ├── __init__.py
│   ├── base.py                # Base 클래스
│   ├── mariadb.py             # MariaDB 로그 파서
│   ├── mysql.py               # MySQL 로그 파서
│   └── postgresql.py          # PostgreSQL 로그 파서
├── router/                    # 라우팅 모듈
│   ├── __init__.py
│   ├── admin_dashboard.py     # 관리자 대시보드
│   ├── login_page.py          # 로그인 페이지
│   └── user_dashboard.py      # 사용자 대시보드
├── session_states/            # 세션 상태 저장
├── session_tokens/            # 세션 토큰 저장
└── utils/                     # 유틸리티 모듈
    ├── __init__.py
    ├── datetime.py            # 날짜/시간 유틸리티
    └── string.py              # 문자열 유틸리티
</code> </pre>

## 🔧 설치 및 실행
- 패키지 설치
  - pip install -r requirements.txt
- 환경 변수 설정
  - .env 파일 생성:
    - envOPENAI_API_KEY
    - AZURE_SEARCH_SERVICE_NAME
    - AZURE_SEARCH_ADMIN_KEY
    - AZURE_SEARCH_INDEX_NAME
    - AZURE_STORAGE_CONNECTION_STRING
    - AZURE_STORAGE_CONTAINER_NAME
- 애플리케이션 실행
  - streamlit run app.py
    
## 🎯 기능
- 관리자
  - 사용자 관리: 사용자 등록, 수정, 권한 설정
  - 프로젝트 관리: 프로젝트 등록, 수정
  - 사용자 프로젝트 매핑: 사용자별 프로젝트 할당

- 일반 사용자
  - 로그 파일 업로드: PostgreSQL, MariaDB, MySQL 로그 파일 업로드
  - 슬로우 쿼리 분석: 임계값 설정을 통한 성능 쿼리 탐지
  - 에러 쿼리 분석: 실행 오류 쿼리 자동 감지
  - AI 튜닝 제안: 각 쿼리별 최적화 제안 확인
  - 분석 이력 관리: 과거 분석 결과 조회

## 🏛 시스템 아키텍처
- 데이터 흐름
  - 로그 업로드 → Azure Blob Storage
  - 로그 파싱 → 슬로우/에러 쿼리 추출
  - AI 분석 → OpenAI API 호출
  - 유사 쿼리 검색 → Azure AI Search
  - 결과 저장 → SQLite Database
  - 인덱싱 → Azure Search Index

- 모듈 설계
  - Parser 모듈: Base 클래스 기반 확장 가능한 파서
  - Auth 모듈: 세션 기반 인증 시스템
  - Database 모듈: 데이터 액세스 레이어
  - AI 모듈: Azure AI 서비스 통합
  - Router 모듈: 페이지 라우팅 및 UI 컴포넌트

## 🚀 Azure 서비스 활용
- Azure Blob Storage
  - 로그 파일 안전한 저장
  - 프로젝트별 폴더 구조 관리
- Azure AI Search
  - 키워드 검색을 통한 유사 쿼리 매칭
  - 임베딩 기반 시맨틱 검색
  - 인덱스 업데이트
