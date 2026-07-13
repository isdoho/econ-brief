# econ-brief

오늘의 경제를 *내 말로* 풀어주는 AI 경제 비서. 기획 전문은 [PLAN.md](./PLAN.md), 배포 절차는 [DEPLOY.md](./DEPLOY.md).

## 구성

```
econ_brief/            # 메인 패키지
  config.py            # .env 로드 + Postgres DSN
  registry.py          # 수집 대상 지표 정의 (ECOS 10 + FRED 6, 총 16개)
  sources/ecos.py      # 한국은행 ECOS 클라이언트
  sources/fred.py      # 미 연준 FRED 클라이언트
  db.py                # Postgres 적재/조회 (psycopg3)
  collector.py         # 수집 → 적재  (python -m econ_brief.collector)
  changes.py           # 어제 vs 오늘 변동 (python -m econ_brief.changes)
  llm.py               # Gemini 클라이언트 (모델 폴백)
  composer.py          # 변동 → LLM 브리핑 생성 → briefings 저장
  daily.py             # 일일 파이프라인: 수집→생성→발송
  dispatcher.py        # 이메일(Gmail SMTP) 발송
  telegram.py          # 텔레그램 발송
  slack.py             # 슬랙 발송
  scheduler.py         # APScheduler (로컬 상주용, 매일 07:00 KST)
  alerts.py            # 대출 알리미 F2 (CD/국고채)
  backfill.py          # 과거 평일 브리핑 as-of 백필
  export.py            # briefings → public/data/briefings.json
  web.py               # FastAPI 웹 아카이브/구독 (로컬 · 미배포)
  util.py              # 재시도·장애 알림 유틸
app/ lib/ public/      # 정적 웹 (Next.js → Cloudflare Pages 배포)
db/schema.sql          # 스키마 (PLAN §8)
docker-compose.yml     # 로컬 Postgres
scripts/               # 초기 검증/프로토타입 스크립트
.github/workflows/daily-brief.yml  # 평일 07:00 KST 데일리 자동화
```

## 빠른 시작

```bash
# 1) 의존성
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2) Postgres 기동 (스키마 자동 적용)
docker compose up -d db

# 3) 데이터 수집 → 적재
.venv/bin/python -m econ_brief.collector

# 4) 어제 vs 오늘 변동 확인
.venv/bin/python -m econ_brief.changes
```

`.env`에 `FRED_API_KEY` / `ECOS_API_KEY` / `GEMINI_API_KEY` + `POSTGRES_*`가 필요하다.

## 일일 파이프라인 / 발송 / 웹

```bash
# 수집 → 생성 → 발송(설정된 채널만) 한 번에
.venv/bin/python -m econ_brief.daily            # 발송 포함
.venv/bin/python -m econ_brief.daily --no-send  # 생성까지만

# 텔레그램 발송 (봇 토큰 필요, chat_id 자동 탐색)
.venv/bin/python -m econ_brief.telegram --whoami   # chat_id 확인
.venv/bin/python -m econ_brief.telegram            # 발송

# 웹 아카이브 (FastAPI · 로컬/추후 구독 기능용 — 배포된 웹은 아래 '정적 웹' 참고)
.venv/bin/python -m uvicorn econ_brief.web:app --port 8000
#  GET /            목록     GET /b/<date>  상세
#  POST /subscribe  구독     GET /api/briefings  JSON
```

발송 채널은 `.env`에 토큰이 있는 것만 자동 사용: `TELEGRAM_BOT_TOKEN` / `SLACK_BOT_TOKEN`+`SLACK_CHANNEL` / `SMTP_USER`+`SMTP_PASS`.

## 스케줄러 (로컬 상주용)

```bash
.venv/bin/python -m econ_brief.scheduler   # 매일 07:00 KST 자동 실행 (APScheduler)
# BRIEF_HOUR / BRIEF_MINUTE 로 시각 조정
```

로컬/VPS에 상주 프로세스로 띄울 때만 쓴다. **실제 배포 자동화는 GitHub Actions가
평일(월~금) 07:00 KST에 실행**한다(아래 '정적 웹' 참고) — 주말에는 갱신되지 않는다.

## 대출 알리미 (F2)

```bash
.venv/bin/python -m econ_brief.alerts --seed  # 데모 프로필로 변동 영향 계산
.venv/bin/python -m econ_brief.alerts         # 등록 프로필 점검
```

지원 벤치마크는 **CD·국고채(ECOS)뿐**이다. COFIX는 은행연합회(portal.kfb.or.kr)
공시라 별도 연동이 필요해 아직 미구현(안내만 출력).

## 정적 웹 (배포용 · Next.js)

**실제 배포는 이쪽이다** — <https://econ-brief.pages.dev>. FastAPI 아카이브(위)와 별개로,
애드센스/SEO용 **완전 정적 사이트**가 저장소 루트에 있다
(`app/`, `lib/`, `public/data/briefings.json`). 청약 알리미와 동일 패턴:
GitHub Actions가 **평일(월~금) 07:00 KST**(cron `0 22 * * 0-4` UTC)에 브리핑을 생성해
JSON을 커밋하고, Cloudflare Pages가 push를 감지해 `out/`을 재빌드·배포한다.

```bash
# 브리핑 백필(과거 평일 as-of 생성) 및 JSON export
.venv/bin/python -m econ_brief.backfill --days 30
.venv/bin/python -m econ_brief.export        # → public/data/briefings.json

# 정적 사이트 빌드
npm install && npm run build                 # → out/
```

애널리틱스(선택): 빌드 시 `NEXT_PUBLIC_GA_ID`(GA4 측정 ID) / `NEXT_PUBLIC_CF_BEACON_TOKEN`(Cloudflare Web Analytics 토큰)이 설정된 것만 로드되며, 미설정이면 아무 스크립트도 넣지 않는다.

자동화: [.github/workflows/daily-brief.yml](.github/workflows/daily-brief.yml)
(Postgres 서비스 컨테이너에서 수집→생성→export→커밋). 배포 절차는 [DEPLOY.md](./DEPLOY.md).

## 진행 상태

- **W1 ✅** 수집기 + Postgres 적재 + 변동 계산 (ECOS 10 + FRED 6, 총 16개 지표).
  KIS 시세는 검증만 완료(`scripts/verify_kis.py`), 수집 대상엔 미포함.
- **W2 ✅** 브리핑 생성→DB 저장→일일 파이프라인→**텔레그램 라이브 발송**→스케줄러.
- **W3 ✅(로컬)** FastAPI 웹 아카이브(목록/상세/구독/JSON API) — 로컬/추후 구독 기능용,
  **미배포**. 배포된 웹은 W6 정적 사이트. 이중옵트인 확인메일만 추후.
- **W4 ✅** 대출 알리미: 벤치마크 변동→월이자 변화·LLM 설명·alerts 적재 (CD/국고채만.
  COFIX는 은행연합회 연동 필요, 미구현).
- **W5 🟡** 운영 안정화(재시도·장애 알림) 완료. 지인 베타는 실사용자 모집 필요.
- **W6 ✅** 정적 사이트 + 백필 + 데일리 Actions 워크플로우 — **Cloudflare Pages 배포 완료**
  (<https://econ-brief.pages.dev>), 평일 07:00 KST 자동 갱신.
