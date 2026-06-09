"""
scenario_engine.py - Load, order, and price the 8 game scenarios.

The newest plan stores relative price moves and scenario groups instead of a
fixed absolute price path. At runtime we keep paired scenarios together, assign
round numbers, and calculate each next_price from price_change_pct.
"""

from dataclasses import dataclass
import random
from typing import List, Optional

import pandas as pd

from config import CURRENCY, NUM_ROUNDS, SCENARIO_CSV, STARTING_PRICE


@dataclass
class Scenario:
    """A single runtime round.

    Player-facing text and backend scoring variables are deliberately separate.
    The UI must never show the hidden scoring fields directly.
    """

    round: int
    price_now: float
    next_price: float
    price_change_pct: float

    market_context: str
    news_text: str
    fundamentals_text: str
    crowd_text: str
    outcome_text: str

    question_1: str = ""
    q1_options: str = ""
    q1_correct: str = ""
    question_2: str = ""
    q2_options: str = ""
    q2_correct: str = ""
    question_3: str = ""
    q3_options: str = ""
    q3_correct: str = ""

    news_sentiment: str = "neutral"
    fundamental_signal: str = "neutral"
    crowd_direction: str = "none"
    crowd_strength: int = 0
    news_frame_type: str = "neutral"
    news_salience: int = 1
    media_intensity: int = 1

    expected_bias: str = ""
    scenario_pair_id: str = ""
    scenario_pair_name: str = ""
    pair_order: int = 1
    detection_logic: str = ""
    notes: str = ""


_REQUIRED_COLUMNS = {
    "round",
    "market_context",
    "news_text",
    "fundamentals_text",
    "crowd_text",
    "news_sentiment",
    "fundamental_signal",
    "crowd_direction",
    "crowd_strength",
    "news_frame_type",
    "news_salience",
    "media_intensity",
}


def load_scenarios(
    csv_path=SCENARIO_CSV,
    *,
    shuffle_groups: bool = False,
    seed: Optional[int] = None,
    keep_setup_first: bool = True,
) -> List[Scenario]:
    """Load scenarios, optionally shuffle groups, and assign runtime prices."""

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Scenario CSV is missing columns: {missing}")
    if len(df) != NUM_ROUNDS:
        raise ValueError(f"Expected {NUM_ROUNDS} rounds, got {len(df)}")

    dynamic_pricing = "price_change_pct" in df.columns and df["price_change_pct"].notna().any()
    if dynamic_pricing:
        df = _order_by_group(df, shuffle_groups, seed, keep_setup_first)
        df = _apply_runtime_prices(df)
    else:
        if {"price_now", "next_price"} - set(df.columns):
            raise ValueError("Scenario CSV needs price_now/next_price or price_change_pct.")

    scenarios = []
    for _, row in df.iterrows():
        price_now = float(row["price_now"])
        market_context = _clean_text(row.get("market_context"))
        if _needs_market_context_fallback(market_context):
            market_context = _fallback_market_context(price_now)

        scenarios.append(
            Scenario(
                round=int(row["round"]),
                price_now=price_now,
                next_price=float(row["next_price"]),
                price_change_pct=_as_pct(row.get("price_change_pct")),
                market_context=market_context,
                news_text=_clean_text(row.get("news_text")),
                fundamentals_text=_clean_text(row.get("fundamentals_text")),
                crowd_text=_clean_text(row.get("crowd_text")),
                outcome_text=_clean_text(row.get("outcome_text")),
                question_1=_clean_text(row.get("question_1")),
                q1_options=_clean_text(row.get("q1_options")),
                q1_correct=_clean_text(row.get("q1_correct")).upper(),
                question_2=_clean_text(row.get("question_2")),
                q2_options=_clean_text(row.get("q2_options")),
                q2_correct=_clean_text(row.get("q2_correct")).upper(),
                question_3=_clean_text(row.get("question_3")),
                q3_options=_clean_text(row.get("q3_options")),
                q3_correct=_clean_text(row.get("q3_correct")).upper(),
                news_sentiment=_clean_text(row.get("news_sentiment")).lower(),
                fundamental_signal=_clean_text(row.get("fundamental_signal")).lower(),
                crowd_direction=_clean_text(row.get("crowd_direction")).lower() or "none",
                crowd_strength=_as_int(row.get("crowd_strength"), 0),
                news_frame_type=_clean_text(row.get("news_frame_type")).lower() or "neutral",
                news_salience=_as_int(row.get("news_salience"), 1),
                media_intensity=_as_int(row.get("media_intensity"), 1),
                expected_bias=_clean_text(row.get("expected_bias")),
                scenario_pair_id=_clean_text(row.get("scenario_pair_id")),
                scenario_pair_name=_clean_text(row.get("scenario_pair_name")),
                pair_order=_as_int(row.get("pair_order"), 1),
                detection_logic=_clean_text(row.get("detection_logic")),
                notes=_clean_text(row.get("notes")),
            )
        )
    return scenarios


def get_scenario(scenarios: List[Scenario], round_num: int) -> Optional[Scenario]:
    """Get scenario for a specific runtime round."""

    for scenario in scenarios:
        if scenario.round == round_num:
            return scenario
    return None


def _order_by_group(
    df: pd.DataFrame,
    shuffle_groups: bool,
    seed: Optional[int],
    keep_setup_first: bool,
) -> pd.DataFrame:
    """Shuffle scenario groups while preserving pair_order inside each group."""

    if "scenario_pair_id" not in df.columns:
        return df.copy().reset_index(drop=True)

    work = df.copy()
    work["scenario_pair_id"] = work["scenario_pair_id"].fillna("").astype(str)
    group_ids = list(dict.fromkeys(work["scenario_pair_id"].tolist()))

    if shuffle_groups:
        fixed = []
        variable = group_ids[:]
        if keep_setup_first and "G1" in variable:
            fixed = ["G1"]
            variable = [g for g in variable if g != "G1"]
        rng = random.Random(seed)
        rng.shuffle(variable)
        group_ids = fixed + variable

    pieces = []
    for group_id in group_ids:
        group = work[work["scenario_pair_id"] == group_id].copy()
        if "pair_order" in group.columns:
            group = group.sort_values("pair_order", kind="stable")
        pieces.append(group)
    return pd.concat(pieces, ignore_index=True)


def _apply_runtime_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate price_now and next_price from price_change_pct."""

    work = df.copy().reset_index(drop=True)
    current_price = float(STARTING_PRICE)
    rounds = []
    prices_now = []
    next_prices = []

    for idx, row in work.iterrows():
        pct = _as_pct(row.get("price_change_pct"))
        next_price = round(current_price * (1 + pct), 2)
        rounds.append(idx + 1)
        prices_now.append(round(current_price, 2))
        next_prices.append(next_price)
        current_price = next_price

    work["round"] = rounds
    work["price_now"] = prices_now
    work["next_price"] = next_prices
    return work


def _as_pct(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        text = value.strip().replace("%", "")
        if not text:
            return 0.0
        parsed = float(text)
        return parsed / 100 if abs(parsed) > 1 else parsed
    return float(value)


def _as_int(value, default: int) -> int:
    if pd.isna(value):
        return default
    return int(float(value))


def _clean_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text


def _needs_market_context_fallback(value: str) -> bool:
    return not value or value.isdigit() or len(value) < 30


def _fallback_market_context(price_now: float) -> str:
    return (
        f"The stock is currently trading at {price_now:,.2f} {CURRENCY}. "
        "The latest news, fundamentals and crowd narrative below are the "
        "available information set before your decision. Compare the evidence "
        "carefully before choosing an action and trade size."
    )
