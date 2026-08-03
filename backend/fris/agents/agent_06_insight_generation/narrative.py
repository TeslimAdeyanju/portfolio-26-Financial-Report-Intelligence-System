"""Verified local-model augmentation for management insight synthesis."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..agent_01_document_processing import ModelStatus
from ...models import AugmentedInsight, FinancialInsight, RiskFinding


DEFAULT_NARRATIVE_MODEL = "phi3:mini"
_PRIORITIES = {"high", "medium", "low"}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_THEME_BY_METRIC = {
    "revenue": "profitability",
    "cost_of_revenue": "profitability",
    "gross_profit": "profitability",
    "operating_income": "profitability",
    "pretax_income": "profitability",
    "net_income": "profitability",
    "gross_margin": "profitability",
    "operating_margin": "profitability",
    "net_margin": "profitability",
    "operating_cash_flow": "cash_flow",
    "free_cash_flow": "cash_flow",
    "capital_expenditure": "cash_flow",
    "ending_cash": "cash_flow",
    "cash_and_equivalents": "liquidity",
    "current_assets": "liquidity",
    "current_liabilities": "liquidity",
    "current_ratio": "liquidity",
    "working_capital": "liquidity",
    "total_debt": "leverage",
    "total_liabilities": "leverage",
    "total_equity": "leverage",
    "debt_to_equity": "leverage",
    "debt_ratio": "leverage",
    "basic_eps": "returns_efficiency",
    "diluted_eps": "returns_efficiency",
    "return_on_assets": "returns_efficiency",
    "return_on_equity": "returns_efficiency",
    "asset_turnover": "returns_efficiency",
}
_THEME_TITLES = {
    "profitability": "Growth and profitability",
    "cash_flow": "Cash generation and investment",
    "liquidity": "Liquidity and working capital",
    "leverage": "Capital structure and leverage",
    "returns_efficiency": "Shareholder returns and efficiency",
    "other": "Other material movements",
}
_UNSUPPORTED_CAUSAL_LANGUAGE = re.compile(
    r"\b(?:caused by|due to|driven by|resulted from)\b", re.I
)
_NUMBER = re.compile(r"(?<![A-Za-z])\(?-?\d[\d,]*(?:\.\d+)?\)?")


class NarrativeAugmentationError(RuntimeError):
    """Raised when a narrative provider or its response fails verification."""


class InsightNarrativeProvider(Protocol):
    model: str

    def status(self) -> ModelStatus: ...

    def generate(self, prompt: str, schema: dict) -> str: ...


class OllamaNarrativeProvider:
    """Generate structured narrative themes through a local Ollama text model."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = DEFAULT_NARRATIVE_MODEL,
        timeout: float = 600,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST" if body is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise NarrativeAugmentationError(
                f"Ollama returned HTTP {exc.code}: {detail[:300]}"
            ) from exc
        except URLError as exc:
            raise NarrativeAugmentationError(
                f"Ollama is unavailable at {self.base_url}. Start Ollama and try again."
            ) from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise NarrativeAugmentationError(
                f"Ollama returned an invalid or timed-out response: {exc}"
            ) from exc

    def status(self) -> ModelStatus:
        try:
            payload = self._request("/api/tags")
        except NarrativeAugmentationError as exc:
            return ModelStatus(False, self.model, str(exc))
        installed = {
            item.get("name") or item.get("model")
            for item in payload.get("models", [])
            if isinstance(item, dict)
        }
        aliases = {self.model, self.model.removesuffix(":latest")}
        if not installed.intersection(aliases):
            return ModelStatus(
                False,
                self.model,
                f"Model {self.model!r} is not installed. Run `ollama pull {self.model}`.",
            )
        return ModelStatus(True, self.model, f"Ollama and {self.model} are ready.")

    def generate(self, prompt: str, schema: dict) -> str:
        payload = self._request(
            "/api/generate",
            {
                "model": self.model,
                "prompt": prompt,
                "format": schema,
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 900},
                # Unload after synthesis so GLM-OCR and the text model do not remain resident.
                "keep_alive": 0,
            },
        )
        response = payload.get("response")
        if not isinstance(response, str) or not response.strip():
            raise NarrativeAugmentationError("The narrative model returned an empty response.")
        return response


_THEME_SCHEMA = {
    "type": "object",
    "properties": {
        "themes": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "theme_id": {"type": "string"},
                    "title": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "narrative": {"type": "string"},
                    "business_meaning": {"type": "string"},
                    "investigation": {"type": "string"},
                },
                "required": [
                    "theme_id", "title", "priority", "narrative",
                    "business_meaning", "investigation",
                ],
            },
        }
    },
    "required": ["themes"],
}


def _decimal_tokens(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for token in _NUMBER.findall(text):
        cleaned = token.replace(",", "").strip("()")
        try:
            values.add(Decimal(cleaned).normalize())
        except InvalidOperation:
            continue
    return values


def _group_insights(insights: list[FinancialInsight]) -> dict[str, dict]:
    groups: dict[str, list[FinancialInsight]] = {}
    for insight in insights:
        metric = insight.related_metrics[0]
        theme_id = _THEME_BY_METRIC.get(metric, "other")
        groups.setdefault(theme_id, []).append(insight)
    packed: dict[str, dict] = {}
    for theme_id, items in groups.items():
        priorities = [item.priority for item in items]
        packed[theme_id] = {
            "theme_id": theme_id,
            "suggested_title": _THEME_TITLES[theme_id],
            "priority": min(priorities, key=lambda value: _PRIORITY_ORDER[value]),
            "movements": [
                {
                    "metric": item.related_metrics[0],
                    "narrative": item.narrative,
                    "business_meaning": item.business_meaning,
                    "investigation": item.investigation,
                }
                for item in items
            ],
            "metrics": list(dict.fromkeys(metric for item in items for metric in item.related_metrics)),
            "risks": list(dict.fromkeys(risk for item in items for risk in item.related_risks)),
            "evidence_pages": sorted({e.page for item in items for e in item.evidence}),
        }
    return packed


def _prompt(insights: list[FinancialInsight]) -> tuple[str, set[Decimal], dict[str, dict]]:
    packed = _group_insights(insights)
    source = {"validated_themes": list(packed.values())}
    serialized = json.dumps(source, separators=(",", ":"))
    allowed_numbers = _decimal_tokens(serialized)
    for value in tuple(allowed_numbers):
        allowed_numbers.add(value.quantize(Decimal("1")))
        allowed_numbers.add(value.quantize(Decimal("0.1")))
        allowed_numbers.add(value.quantize(Decimal("0.01")))
    prompt = """You are a financial management commentary editor. Rewrite each supplied validated theme into concise, connected management commentary. Return exactly one output object for every supplied theme_id and do not create or omit a theme. Explicitly name every supplied metric within its theme and combine their movements into connected prose. Use only supplied figures and do not add a currency symbol. Never recalculate, introduce a new number, or claim an operational cause. Do not use 'caused by', 'due to', 'driven by', or 'resulted from'. Put possible explanations only in investigation as review actions or questions. Preserve balanced context. Return only JSON matching the schema.\n\nVALIDATED_INPUT:\n""" + serialized
    return prompt, allowed_numbers, packed


def _nonempty_string(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise NarrativeAugmentationError(f"Theme field {key!r} must be a non-empty string.")
    return value.strip()


def _verify(
    raw: str,
    insights: list[FinancialInsight],
    allowed_numbers: set[Decimal],
    packed: dict[str, dict],
) -> list[AugmentedInsight]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NarrativeAugmentationError("The narrative model did not return valid JSON.") from exc
    themes = payload.get("themes") if isinstance(payload, dict) else None
    if not isinstance(themes, list) or not 1 <= len(themes) <= 6:
        raise NarrativeAugmentationError("The narrative response must contain 1 to 6 themes.")

    verified: list[AugmentedInsight] = []
    returned_theme_ids: set[str] = set()
    for theme in themes:
        if not isinstance(theme, dict):
            raise NarrativeAugmentationError("Every narrative theme must be an object.")
        theme_id = _nonempty_string(theme, "theme_id")
        if theme_id not in packed or theme_id in returned_theme_ids:
            raise NarrativeAugmentationError("The response returned an unknown or duplicate theme.")
        returned_theme_ids.add(theme_id)
        source_theme = packed[theme_id]
        priority = _nonempty_string(theme, "priority").lower()
        if priority not in _PRIORITIES:
            raise NarrativeAugmentationError(f"Unsupported theme priority: {priority}")
        if priority != source_theme["priority"]:
            raise NarrativeAugmentationError("The model changed a validated theme priority.")
        narrative = re.sub(r"[$£€]", "", _nonempty_string(theme, "narrative"))
        meaning = re.sub(r"[$£€]", "", _nonempty_string(theme, "business_meaning"))
        investigation = _nonempty_string(theme, "investigation")
        combined = " ".join((narrative, meaning))
        if _UNSUPPORTED_CAUSAL_LANGUAGE.search(combined):
            raise NarrativeAugmentationError("The narrative asserted an unsupported causal claim.")
        if not _decimal_tokens(combined).issubset(allowed_numbers):
            raise NarrativeAugmentationError("The narrative introduced a figure not present in validated input.")
        normalized_combined = " ".join(combined.casefold().replace("_", " ").split())
        missing_metrics = [
            metric
            for metric in source_theme["metrics"]
            if " ".join(metric.casefold().replace("_", " ").split()) not in normalized_combined
        ]
        if missing_metrics:
            omitted_sentences = [
                movement["narrative"]
                for movement in source_theme["movements"]
                if movement["metric"] in missing_metrics
            ]
            narrative = " ".join([narrative, *omitted_sentences])
            normalized_combined = " ".join(
                f"{narrative} {meaning}".casefold().replace("_", " ").split()
            )
            if any(
                " ".join(metric.casefold().replace("_", " ").split())
                not in normalized_combined
                for metric in missing_metrics
            ):
                raise NarrativeAugmentationError(
                    "A validated metric could not be restored to the narrative."
                )

        verified.append(
            AugmentedInsight(
                title=_nonempty_string(theme, "title"),
                priority=priority,
                narrative=narrative,
                business_meaning=meaning,
                investigation=investigation,
                related_metrics=tuple(source_theme["metrics"]),
                related_risks=tuple(source_theme["risks"]),
                evidence_pages=tuple(source_theme["evidence_pages"]),
            )
        )
    if returned_theme_ids != set(packed):
        raise NarrativeAugmentationError("The narrative omitted a validated financial theme.")
    return verified


def augment_financial_insights(
    insights: list[FinancialInsight],
    risks: list[RiskFinding],
    provider: InsightNarrativeProvider,
) -> list[AugmentedInsight]:
    """Ask a model to consolidate insights, then verify every returned reference."""
    if not insights:
        return []
    prompt, allowed_numbers, packed = _prompt(insights)
    return _verify(provider.generate(prompt, _THEME_SCHEMA), insights, allowed_numbers, packed)
