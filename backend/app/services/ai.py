"""AI-синтезатор вердикта (RAG): LLM получает только строгий JSON метрик.

Fallback: детерминированная rule-based генерация на русском, если API-ключ не задан
или LLM недоступен — MVP никогда не падает.
"""
from __future__ import annotations

import json
import logging

from ..config import get_settings
from ..models import ClimateStats, DisasterAlert, GeopoliticalRisk, HolidayInfo, IndoorPlace
from .scoring import ScoreBreakdown

logger = logging.getLogger("trisp.ai")

SYSTEM_PROMPT = (
    "Ты — аналитик туристических рисков. Тебе передан СТРОГИЙ JSON с историческими "
    "метриками климата, геополитики, стихийных бедствий и праздников. "
    "ЖЁСТКИЕ ПРАВИЛА: 1) НИКОГДА не выдумывай числа о погоде или политические события — "
    "используй ТОЛЬКО переданные метрики. 2) Пиши на русском. 3) Формат ответа (markdown):\n"
    "## Главный вердикт\n2–3 честных предложения об оценке.\n"
    "## Красные флаги\n- маркеры конкретных угроз с числами из JSON\n"
    "## Совет по датам / альтернативы\n- что сдвинуть или взять с собой\n"
    "## Чем заняться в дождь (План Б)\n- коротко свяжи с перечисленными крытыми местами"
)


async def synthesize_verdict(
    location_name: str,
    country: str,
    dates_label: str,
    trip_type: str,
    score: ScoreBreakdown,
    climate: ClimateStats,
    geopolitics: GeopoliticalRisk,
    disasters: list[DisasterAlert],
    holidays: list[HolidayInfo],
    plan_b: list[IndoorPlace],
) -> tuple[str, str]:
    """Возвращает (markdown_вердикт, источник: 'llm' | 'fallback')."""
    settings = get_settings()
    context = {
        "location": location_name,
        "country": country,
        "dates": dates_label,
        "trip_type": trip_type,
        "trip_viability_score": score.total,
        "breakdown": {
            "climate": score.climate,
            "safety": score.safety,
            "seasonality": score.seasonality,
        },
        "verdict": score.verdict_ru,
        "climate_metrics": {
            "avg_temp_max_c": climate.avg_temp_max,
            "avg_temp_min_c": climate.avg_temp_min,
            "rain_day_probability_pct": climate.rain_day_probability,
            "heavy_rain_risk_pct": climate.heavy_rain_risk,
            "storm_wind_risk_pct": climate.storm_wind_risk,
            "sample_days": climate.total_days_sampled,
        },
        "geopolitics": {
            "articles_last_30d": geopolitics.article_count,
            "avg_tone": geopolitics.avg_tone,
            "headlines": [h["title"] for h in geopolitics.headlines],
        },
        "disaster_alerts": [
            {"type": d.event_type, "severity": d.severity, "title": d.title,
             "distance_km": d.distance_km}
            for d in disasters
        ],
        "holiday_overlaps": [{"name": h.name, "date": h.date} for h in holidays],
        "plan_b_places": [{"name": p.name, "kind": p.category_ru} for p in plan_b],
    }

    if settings.llm_api_key:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url or None,
                timeout=30,
            )
            resp = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
                ],
                temperature=0.3,
                max_tokens=900,
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text, "llm"
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM synthesis failed, using fallback: %s", exc)

    return _rule_based_fallback(context), "fallback"


def _rule_based_fallback(ctx: dict) -> str:
    """Детерминированная генерация вердикта из тех же метрик."""
    cm = ctx["climate_metrics"]
    geo = ctx["geopolitics"]
    alerts = ctx["disaster_alerts"]
    hol = ctx["holiday_overlaps"]
    places = ctx["plan_b_places"]
    score = ctx["trip_viability_score"]
    name = ctx["location"]
    lines: list[str] = []

    # --- Главный вердикт ---
    lines.append("## Главный вердикт")
    intro = f"{name}, {ctx['dates']}: итоговая оценка готовности — **{score}/100** ({ctx['verdict']}). "
    rain = cm.get("rain_day_probability_pct")
    if rain is not None:
        if rain >= 40:
            intro += f"Исторически в эти даты дождливыми бывают {rain:.0f}% дней — погода будет активно вмешиваться в планы. "
        elif rain >= 20:
            intro += f"Дождливых дней около {rain:.0f}% — зонтик обязателен, но поездка жизнеспособна. "
        else:
            intro += f"Дожди редки (лишь {rain:.0f}% дней исторически) — окно погоды отличное. "
    tmax = cm.get("avg_temp_max_c")
    if tmax is not None:
        intro += f"Средний максимум +{tmax:.0f}°C."
    lines.append(intro)
    lines.append("")

    # --- Красные флаги ---
    lines.append("## Красные флаги")
    flags: list[str] = []
    heavy = cm.get("heavy_rain_risk_pct")
    if rain is not None and rain > 30:
        flags.append(f"Исторически {rain:.0f}% дней в этот период — устойчивые дожди.")
    if heavy is not None and heavy > 8:
        flags.append(f"Сильные ливни (>15 мм) фиксируются в {heavy:.0f}% дней.")
    wind = cm.get("storm_wind_risk_pct")
    if wind is not None and wind > 10:
        flags.append(f"Штормовой ветер (>40 км/ч) в {wind:.0f}% исторических дней — моря/экскурсии на лодках под риском.")
    if tmax is not None and tmax > 36:
        flags.append(f"Экстремальная жара: средний максимум +{tmax:.0f}°C.")
    if geo.get("articles_last_30d", 0) >= 5:
        flags.append(
            f"GDELT зафиксировал {geo['articles_last_30d']} новостей о протестах/забастовках/ЧС за 30 дней."
        )
        for h in (geo.get("headlines") or [])[:2]:
            flags.append(f"Заголовок источника: «{h}»")
    for a in alerts:
        if a["severity"] in ("Red", "Orange"):
            flags.append(f"GDACS {a['severity'].upper()}: {a['title']} (~{a['distance_km']} км).")
    for h in hol:
        flags.append(f"Праздник в даты поездки: {h['name']} ({h['date']}) — ожидаемые толпы и закрытая инфраструктура.")
    if not flags:
        flags.append("Существенных красных флагов не обнаружено.")
    lines += [f"- {f}" for f in flags]
    lines.append("")

    # --- Совет по датам ---
    lines.append("## Совет по датам / альтернативы")
    advice: list[str] = []
    if rain is not None and rain >= 35:
        advice.append("Сдвиньте поездку на 2–3 недели ближе к сухому окну или выбирайте направление вне пика муссона.")
    if tmax is not None and tmax > 36:
        advice.append("Планируйте активности на утро/вечер, лёгкая одежда и SPF 50+ обязательны.")
    if wind is not None and wind > 10:
        advice.append("Морские экскурсии могут отменяться — держите гибкость в последних 3 днях.")
    if geo.get("articles_last_30d", 0) >= 15:
        advice.append("Следите за локальными новостями перед выездом, избегайте районов скоплений протестующих.")
    if not advice:
        advice.append("Окно дат удачное — берите стандартный набор: страховка, копии документов, аптечка.")
    lines += [f"- {a}" for a in advice]
    lines.append("")

    # --- План Б ---
    lines.append("## Чем заняться в дождь (План Б)")
    if places:
        kinds = ", ".join(f"{p['name']} ({p['kind']})" for p in places[:4])
        lines.append(
            f"Если небо затянет, спасайте отпуск в крытых местах рядом с курортом: {kinds}. "
            "Это реальные точки с OpenStreetMap — координаты в блоке «План Б» ниже."
        )
    else:
        lines.append("Крытые места пока не найдены — запросите «План Б» повторно позже.")
    return "\n".join(lines)
