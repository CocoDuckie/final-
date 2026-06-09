"""
data_manager.py - Build round log entries and persist player results.
"""

from pathlib import Path
import csv
from typing import Dict, List

import pandas as pd

from config import LEADERBOARD_CSV, LOGS_DIR, STARTING_CAPITAL
from scenario_engine import Scenario
from trading_logic import Portfolio, TradeResult


def build_round_entry(
    scenario: Scenario,
    trade: TradeResult,
    portfolio_after: Portfolio,
    prev_portfolio_value: float,
) -> Dict:
    """Merge scenario, trade, and portfolio state for scoring/results."""

    portfolio_value_start = prev_portfolio_value
    portfolio_value_end = portfolio_after.cash + portfolio_after.shares * scenario.next_price
    portfolio_round_return = (
        (portfolio_value_end - portfolio_value_start) / portfolio_value_start
        if prev_portfolio_value else 0.0
    )
    unrealized_return_before = (
        (scenario.price_now - trade.avg_cost_before) / trade.avg_cost_before
        if trade.shares_before > 0 and trade.avg_cost_before > 0 else 0.0
    )
    unrealized_return_after = (
        (scenario.next_price - trade.avg_cost_after) / trade.avg_cost_after
        if trade.shares_after > 0 and trade.avg_cost_after > 0 else 0.0
    )
    portfolio_return = (
        (portfolio_value_end - STARTING_CAPITAL) / STARTING_CAPITAL
        if STARTING_CAPITAL else 0.0
    )
    position_weight_after = (
        (portfolio_after.shares * scenario.next_price) / portfolio_value_end
        if portfolio_value_end else 0.0
    )

    return {
        "round": scenario.round,
        "price_now": scenario.price_now,
        "next_price": scenario.next_price,
        "price_change_pct": scenario.price_change_pct,
        "scenario_pair_id": scenario.scenario_pair_id,
        "scenario_pair_name": scenario.scenario_pair_name,
        "market_context": scenario.market_context,
        "news_text": scenario.news_text,
        "fundamentals_text": scenario.fundamentals_text,
        "crowd_text": scenario.crowd_text,
        "outcome_text": scenario.outcome_text,
        "news_sentiment": scenario.news_sentiment,
        "fundamental_signal": scenario.fundamental_signal,
        "crowd_direction": scenario.crowd_direction,
        "crowd_strength": scenario.crowd_strength,
        "news_frame_type": scenario.news_frame_type,
        "news_salience": scenario.news_salience,
        "media_intensity": scenario.media_intensity,
        "action": trade.action,
        "trade_size": trade.trade_size,
        "size_level": trade.size_level,
        "size_pct": 0.0 if trade.size_level == 0 else {
            "small": 0.25,
            "medium": 0.50,
            "high": 0.75,
            "all_in": 1.00,
        }.get(trade.trade_size, 0.0),
        "cash_before": trade.cash_before,
        "shares_before": int(trade.shares_before),
        "shares_after": int(trade.shares_after),
        "shares_traded": int(trade.shares_traded),
        "cash_after": trade.cash_after,
        "avg_cost_before": trade.avg_cost_before,
        "avg_cost_after": trade.avg_cost_after,
        "portfolio_value_start": portfolio_value_start,
        "portfolio_value_end": portfolio_value_end,
        "portfolio_value": portfolio_value_end,
        "portfolio_round_return": portfolio_round_return,
        "portfolio_return": portfolio_return,
        "round_return": portfolio_round_return,
        "total_return": portfolio_return,
        "unrealized_return": unrealized_return_before,
        "unrealized_return_before": unrealized_return_before,
        "unrealized_return_after": unrealized_return_after,
        "position_weight_after": position_weight_after,
    }


def save_round_log(log: List[Dict], player_name: str) -> Path:
    """Save the full per-round log to CSV and return the file path."""

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in player_name if c.isalnum() or c in "_-") or "player"
    path = LOGS_DIR / f"log_{safe_name}.csv"
    df = pd.DataFrame(log)
    df = df.drop(
        columns=[
            c for c in (
                "market_context",
                "news_text",
                "fundamentals_text",
                "crowd_text",
                "outcome_text",
            )
            if c in df.columns
        ]
    )
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def append_leaderboard(
    player_name: str,
    total_return_pct: float,
    total_bias_score: int,
    rationality_score: float,
) -> None:
    """Append one row to leaderboard CSV."""

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    is_new = not LEADERBOARD_CSV.exists()
    with open(LEADERBOARD_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow([
                "player_name",
                "total_return_pct",
                "total_bias_score",
                "rationality_score",
            ])
        writer.writerow([
            player_name,
            round(total_return_pct, 2),
            total_bias_score,
            rationality_score,
        ])


def load_leaderboard() -> pd.DataFrame:
    """Load leaderboard sorted by rationality_score descending."""

    if not LEADERBOARD_CSV.exists():
        return pd.DataFrame(
            columns=[
                "player_name",
                "total_return_pct",
                "total_bias_score",
                "rationality_score",
            ]
        )
    df = pd.read_csv(LEADERBOARD_CSV)
    return df.sort_values("rationality_score", ascending=False).reset_index(drop=True)
