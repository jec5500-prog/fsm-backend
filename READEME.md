# FSM Backend

FastAPI + SQLAlchemy 기반 백엔드 프로젝트입니다.

## 기술 스택

- **Python 3.13**
- **FastAPI** — 웹 API 프레임워크
- **SQLAlchemy** — ORM (데이터베이스)
- **Pydantic** — 데이터 검증
- **SQLite** — 개발용 데이터베이스

## 프로젝트 구조

```
fsm-backend/
├── app/
│   ├── core/        # 설정, DB 연결
│   ├── models/      # DB 테이블 정의 (SQLAlchemy)
│   ├── schemas/     # 요청/응답 형식 (Pydantic)
│   ├── services/    # 비즈니스 로직
│   └── routers/     # API 엔드포인트
├── venv/            # 가상환경 (git 제외)
└── README.md
```

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings

# 3. 서버 실행 (추후 main.py 작성 후)
uvicorn app.main:app --reload
```

## 진행 상황

- [x] 프로젝트 구조 설계
- [x] 개발 환경 세팅 (venv, 패키지 설치)
- [x] core 모듈 (config, database)
- [ ] models / schemas
- [ ] services / routers
- [ ] main.py 및 서버 실행