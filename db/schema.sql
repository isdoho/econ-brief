-- econ-brief 스키마 (PLAN §8 기준)
-- W1에서 실제 쓰는 건 indicators / indicator_values 두 개.
-- 나머지(briefings·users·…)는 W2~W4 대비해 미리 정의.

-- ── 원천 시계열 ───────────────────────────────────────────────
-- PLAN §8은 indicators(id, source, series_code, name, unit)지만,
-- ECOS는 (통계표코드 + 항목코드 + 주기)가 있어야 시리즈가 유일해진다.
-- 그래서 item_code·cycle을 추가하고 (source, series_code, item_code)를 자연키로 둔다.
CREATE TABLE IF NOT EXISTS indicators (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL,                 -- 'ECOS' | 'FRED' | 'KIS'
    series_code TEXT NOT NULL,                 -- ECOS 통계표코드 / FRED series_id
    item_code   TEXT NOT NULL DEFAULT '',      -- ECOS 항목코드 (FRED는 '')
    cycle       TEXT NOT NULL DEFAULT '',      -- 'D' | 'M' | 'A' | 'Q'
    name        TEXT NOT NULL,                 -- 사람이 읽는 이름 (예: 기준금리)
    unit        TEXT NOT NULL DEFAULT '',
    UNIQUE (source, series_code, item_code)
);

-- ts는 소스 원본 포맷을 보존(일별 YYYYMMDD, 월별 YYYYMM 등)하기 위해 TEXT.
CREATE TABLE IF NOT EXISTS indicator_values (
    indicator_id INTEGER NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    ts           TEXT NOT NULL,
    value        DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (indicator_id, ts)
);

-- ── 브리핑 ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS briefings (
    id           SERIAL PRIMARY KEY,
    date         DATE UNIQUE NOT NULL,
    payload_json JSONB,
    body_md      TEXT,
    model        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 사용자 / 구독 ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    channel     TEXT NOT NULL DEFAULT 'email',
    verified_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type    TEXT NOT NULL,                     -- daily_brief | fx | loan
    PRIMARY KEY (user_id, type)
);

-- ── 대출 알리미 ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS loan_profiles (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind         TEXT NOT NULL,                -- 변동 | 혼합
    balance      BIGINT,
    benchmark    TEXT,                         -- COFIX | CD | 국고채
    spread       DOUBLE PRECISION,
    current_rate DOUBLE PRECISION,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alerts (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type         TEXT NOT NULL,
    payload_json JSONB,
    sent_at      TIMESTAMPTZ
);

-- ── 발송 이력 ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deliveries (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    briefing_id INTEGER REFERENCES briefings(id) ON DELETE SET NULL,
    channel     TEXT NOT NULL,
    status      TEXT NOT NULL,
    sent_at     TIMESTAMPTZ
);
