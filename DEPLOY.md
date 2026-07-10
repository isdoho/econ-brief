# econ-brief 배포 절차

정적 사이트(Next.js `output: export`)를 청약 알리미와 같은 방식으로 올린다.
로컬 준비는 끝난 상태(브리핑 23건 백필 완료, `npm run build` 통과). 아래만 하면 라이브.

## 1. GitHub 저장소

```bash
cd ~/Desktop/econ-brief
git init && git add -A && git commit -m "feat: 정적 웹 + 데일리 파이프라인"
gh repo create isdoho/econ-brief --public --source . --push
```

## 2. Actions 시크릿 (데일리 브리핑 생성용)

저장소 → Settings → Secrets and variables → Actions:

| 시크릿 | 값 |
|---|---|
| `ECOS_API_KEY` | 로컬 `.env`와 동일 |
| `FRED_API_KEY` | 〃 |
| `GEMINI_API_KEY` | 〃 |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | (선택) 파이프라인 장애 알림 |

등록 후 Actions 탭에서 **Daily Brief** 워크플로우를 `workflow_dispatch`로 한 번 수동 실행해 검증.
이후 매 평일 07:00 KST에 자동 실행되어 `public/data/briefings.json`을 커밋한다.

## 3. Netlify

1. app.netlify.com → Add new site → Import an existing project → GitHub `econ-brief` 연결
2. 빌드 설정은 `netlify.toml`이 자동 적용 (command `npm run build` · publish `out`)
3. 환경변수(빌드):
   - `NEXT_PUBLIC_SITE_URL` = 배포 도메인 (예: `https://econ-brief.netlify.app` 또는 커스텀 도메인 — netlify.toml에 이미 기본값 있음)
   - `NEXT_PUBLIC_ADSENSE_CLIENT` = 애드센스 승인 후 `ca-pub-…` (승인 전엔 비워둠)
   - `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION` / `NEXT_PUBLIC_NAVER_SITE_VERIFICATION` = 서치콘솔 인증값

## 4. 애드센스 신청 전 체크리스트

- [ ] 콘텐츠 20건 이상 ✅ (23건, 매일 +1 자동)
- [ ] 개인정보처리방침 `/privacy` ✅ · 사이트 소개/문의 `/about` ✅
- [ ] sitemap.xml / robots.txt ✅ (빌드에 포함)
- [ ] 서치콘솔·네이버 서치어드바이저 등록 + sitemap 제출 (배포 후)
- [ ] 커스텀 도메인 연결 권장 — `*.netlify.app` 서브도메인은 애드센스 등록이 안 될 수 있음
- [ ] 2~4주 운영해 아카이브를 더 쌓은 뒤 신청하면 승인 확률↑

## 참고

- 워크플로우의 Postgres는 CI 내 일회용 컨테이너다. `econ_brief.export`가 기존
  `briefings.json`과 병합하므로 과거 아카이브는 유실되지 않는다.
- 브리핑을 과거로 더 채우고 싶으면 로컬에서
  `.venv/bin/python -m econ_brief.backfill --days 60` 후 export → 커밋.
- FastAPI(`econ_brief.web`)는 로컬/추후 구독 기능용으로 그대로 남아 있다. 정적 사이트와 무관.
