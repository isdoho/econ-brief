"""LLM 클라이언트 — 메인은 Gemini Flash(대량·저비용), 모델 폴백 포함."""
import requests

from econ_brief.config import GEMINI_API_KEY

# 사용 가능한 최신 모델부터 시도(404면 다음으로 폴백). brief_demo.py와 동일 전략.
GEMINI_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]


def gemini(prompt: str, temperature: float = 0.7) -> tuple[str, str]:
    """(model, text) 반환. 사용 가능한 모델이 없으면 예외."""
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=90)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        j = r.json()
        return model, j["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError("사용 가능한 Gemini 모델 없음")
