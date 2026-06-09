"""
bias_rules.py - Plan-final cluster-based bias detection.

Rules follow:
- `4. Bias Detection Logic`
- `4d. Python Cluster Code`
- `3a. Key Common variables`
"""

from typing import Dict, List, Tuple

from config import (
    DISPOSITION_GAME_CAP,
    GAME_SCORE_CAP,
    OC_AVG_SIZE_THRESHOLD,
    OC_NUM_TRADES_THRESHOLD,
    ROUND_SCORE_CAP,
    tier_for,
)


LARGE_LOSS_THRESHOLD = -0.07


def unrealized_return_before(row: Dict) -> float:
    """Position return before the decision; internal bias-scoring variable only."""

    if "unrealized_return_before" in row:
        return float(row.get("unrealized_return_before") or 0.0)
    if "unrealized_return" in row:
        return float(row.get("unrealized_return") or 0.0)
    avg_cost = float(row.get("avg_cost_before") or 0.0)
    shares_before = float(row.get("shares_before") or 0.0)
    if shares_before <= 0 or avg_cost <= 0:
        return 0.0
    return (float(row["price_now"]) - avg_cost) / avg_cost


def action_direction(action: str) -> str:
    if action == "buy":
        return "buy"
    if action == "sell":
        return "sell"
    return "none"


def news_direction(news_sentiment: str) -> str:
    if news_sentiment == "positive":
        return "buy"
    if news_sentiment == "negative":
        return "sell"
    return "none"


def frame_direction(news_frame_type: str) -> str:
    if news_frame_type == "positive_spin":
        return "buy"
    if news_frame_type == "negative_spin":
        return "sell"
    return "none"


def frame_contradiction(row: Dict) -> int:
    fd = frame_direction(row["news_frame_type"])
    if fd == "buy" and row["fundamental_signal"] == "weak":
        return 1
    if fd == "sell" and row["fundamental_signal"] == "good":
        return 1
    return 0


def recent_high(log: List[Dict], i: int) -> float:
    prior = log[max(0, i - 3):i]
    return max(r["price_now"] for r in prior) if prior else log[i]["price_now"]


def sell_ratio(row: Dict) -> float:
    shares_before = float(row.get("shares_before") or 0.0)
    if row["action"] != "sell" or shares_before <= 0:
        return 0.0
    return (shares_before - float(row.get("shares_after") or 0.0)) / shares_before


def round_trip_flag(log: List[Dict], i: int) -> int:
    """1 if a sell is followed by a buy in the next one or two rounds."""

    if log[i]["action"] != "sell":
        return 0
    for j in (i + 1, i + 2):
        if j < len(log) and log[j]["action"] == "buy":
            return 1
    return 0


def _round_return(row: Dict) -> float:
    return float(row.get("portfolio_round_return", row.get("round_return")) or 0.0)


def _evaluate_round(log: List[Dict], i: int) -> Dict[str, List[Tuple[str, int, str]]]:
    row = log[i]
    action = row["action"]
    size_level = int(row["size_level"])
    news_sentiment = row["news_sentiment"]
    fundamental_signal = row["fundamental_signal"]
    news_frame_type = row["news_frame_type"]
    price_now = row["price_now"]

    ad = action_direction(action)
    nd = news_direction(news_sentiment)
    fd = frame_direction(news_frame_type)
    fc = frame_contradiction(row)
    rh = recent_high(log, i)
    ur = unrealized_return_before(row)

    prev_return = _round_return(log[i - 1]) if i > 0 else None
    prev_size = int(log[i - 1]["size_level"]) if i > 0 else None
    prev_action = log[i - 1]["action"] if i > 0 else None
    ratio = (size_level / max(prev_size, 1)) if prev_size is not None else None

    fires = {
        "Overconfidence": [],
        "Herding": [],
        "Availability": [],
        "Framing": [],
        "Loss Aversion": [],
        "Disposition Effect": [],
    }
    fired_clusters = {bias: set() for bias in fires}

    def fire(bias: str, cluster_id: str, points: int, message: str) -> None:
        if cluster_id in fired_clusters[bias]:
            return
        fired_clusters[bias].add(cluster_id)
        fires[bias].append((cluster_id, points, message))

    # Overconfidence
    if news_sentiment == "negative" and action == "buy" and size_level >= 2:
        fire("Overconfidence", "OC_WARNING_IGNORED", 2,
             "Bought medium+ size despite negative news.")

    if (
        prev_return is not None
        and prev_return > 0
        and prev_size is not None
        and prev_size > 0
        and (size_level > prev_size or (ratio or 0) > 1.5)
    ):
        fire("Overconfidence", "OC_SELF_ATTRIBUTION_AFTER_WIN", 1,
             "Increased size after profit; previous week was a real trade.")

    if round_trip_flag(log, i) == 1:
        fire("Overconfidence", "OC_TIMING_CONFIDENCE", 1,
             "Quick sell-then-rebuy pattern.")

    oc_supporting_fired = bool(
        {"OC_SELF_ATTRIBUTION_AFTER_WIN", "OC_TIMING_CONFIDENCE"}
        & fired_clusters["Overconfidence"]
    )
    if oc_supporting_fired and size_level >= 3:
        fire("Overconfidence", "OC_HIGH_SIZE_AMPLIFIER", 1,
             "High/all-in size amplifies overconfidence after supporting evidence.")

    # Herding - strict core.
    crowd_direction = row["crowd_direction"]
    crowd_strength = int(row["crowd_strength"])
    hd_core_gate = (
        crowd_strength >= 4
        and crowd_direction != "none"
        and ad == crowd_direction
        and (
            (action == "buy" and fundamental_signal != "good")
            or (action == "sell" and fundamental_signal != "weak")
        )
    )
    if hd_core_gate:
        fire("Herding", "HD_FOLLOW_CROWD_WITH_WEAK_SUPPORT", 2,
             "Followed a strong crowd signal without clear fundamental support.")

        if crowd_strength == 5:
            fire("Herding", "HD_EXTREME_CROWD_PRESSURE", 1,
                 "Crowd signal was extreme, making crowd influence more plausible.")

        if size_level >= 2:
            fomo_buy = (
                action == "buy"
                and crowd_direction == "buy"
                and price_now is not None
                and rh is not None
                and price_now >= rh
            )
            panic_sell = (
                action == "sell"
                and crowd_direction == "sell"
                and news_sentiment == "negative"
            )
            if fomo_buy or panic_sell:
                fire("Herding", "HD_FOMO_OR_PANIC_STRICT", 1,
                     "Medium+ FOMO buying or panic selling with the crowd.")

        hd_supporting_fired = bool(
            {"HD_EXTREME_CROWD_PRESSURE", "HD_FOMO_OR_PANIC_STRICT"}
            & fired_clusters["Herding"]
        )
        if hd_supporting_fired and size_level >= 3 and crowd_strength == 5:
            fire("Herding", "HD_HIGH_SIZE_AMPLIFIER", 1,
                 "High/all-in size amplifies herding after strict supporting evidence.")

    # Availability - strict core.
    news_salience = int(row["news_salience"])
    media_intensity = int(row["media_intensity"])
    av_core_gate = (
        news_salience >= 4
        and media_intensity >= 4
        and (news_salience + media_intensity) >= 9
        and nd != "none"
        and ad == nd
        and (
            (nd == "buy" and fundamental_signal != "good")
            or (nd == "sell" and fundamental_signal != "weak")
        )
    )
    if av_core_gate:
        fire("Availability", "AV_SALIENT_NEWS_WITH_WEAK_SUPPORT", 2,
             "Acted in the direction of highly salient news without clear fundamental support.")

        if prev_action == "hold" and action in {"buy", "sell"} and size_level >= 2:
            fire("Availability", "AV_RECENCY_SWITCH_MEDIUM_PLUS", 1,
                 "Switched from hold into medium+ action after vivid news.")

        if news_salience == 5 and media_intensity == 5:
            fire("Availability", "AV_EXTREME_SALIENCE", 1,
                 "Both salience and media intensity were at maximum.")

        av_supporting_fired = bool(
            {"AV_RECENCY_SWITCH_MEDIUM_PLUS", "AV_EXTREME_SALIENCE"}
            & fired_clusters["Availability"]
        )
        if av_supporting_fired and size_level >= 3:
            fire("Availability", "AV_HIGH_SIZE_AMPLIFIER", 1,
                 "High/all-in size amplifies availability after strict supporting evidence.")

    # Framing
    fr_core_gate = fc == 1 and fd != "none" and ad == fd
    if fr_core_gate:
        fire("Framing", "FR_FRAME_CONTRADICTION_FOLLOWED", 2,
             "Followed the frame despite contradictory data.")

        explicit_spin = (
            news_frame_type == "positive_spin"
            and fundamental_signal == "weak"
            and action == "buy"
        ) or (
            news_frame_type == "negative_spin"
            and fundamental_signal != "weak"
            and action == "sell"
        )
        if explicit_spin:
            fire("Framing", "FR_EXPLICIT_SPIN_PATTERN", 1,
                 "Explicit spin pattern matched.")

        if size_level >= 3:
            fire("Framing", "FR_HIGH_SIZE_AMPLIFIER", 1,
                 "High/all-in amplifies framing.")

    has_position_before = float(row.get("shares_before") or 0.0) > 0
    sold_most_position = sell_ratio(row) >= 0.5
    supportive_signal = fundamental_signal == "good" or news_sentiment == "positive"

    # Disposition Effect
    modest_winner_sale = (
        has_position_before
        and action == "sell"
        and 0 < ur < 0.12
        and fundamental_signal != "weak"
        and news_sentiment != "negative"
    )
    if modest_winner_sale:
        if supportive_signal:
            fire(
                "Disposition Effect",
                "DE_SELL_MODEST_WINNER_SUPPORTIVE_SIGNAL",
                2,
                "Sold a modest winning position early despite supportive news or fundamentals.",
            )
        else:
            fire(
                "Disposition Effect",
                "DE_SELL_MODEST_WINNER",
                1,
                "Sold a modest winning position early.",
            )

        if sold_most_position:
            fire(
                "Disposition Effect",
                "DE_SOLD_MOST_MODEST_WINNER",
                1,
                "Sold most or all of a modest winner.",
            )

    if has_position_before and ur <= LARGE_LOSS_THRESHOLD and action == "hold":
        if fundamental_signal == "weak" or news_sentiment == "negative":
            fire(
                "Disposition Effect",
                "DE_HOLD_LARGE_LOSER_BAD_SIGNAL",
                2,
                "Held a >7% losing position despite weak fundamentals or negative news.",
            )
        else:
            fire(
                "Disposition Effect",
                "DE_HOLD_LARGE_LOSER",
                1,
                "Held a >7% losing position instead of reassessing it.",
            )

    if has_position_before and ur <= LARGE_LOSS_THRESHOLD and action == "buy":
        fire(
            "Disposition Effect",
            "DE_AVERAGE_DOWN_LARGE_LOSER",
            1,
            "Added to a position that was already down more than 7%.",
        )

    # Loss Aversion
    la_core_fired = False
    if (
        has_position_before
        and ur <= LARGE_LOSS_THRESHOLD
        and action == "hold"
    ):
        if fundamental_signal == "weak" or news_sentiment == "negative":
            fire("Loss Aversion", "LA_HOLD_LOSER_BAD_SIGNAL", 2,
                 "Held >7% losing position despite weak fundamentals or negative news.")
        else:
            fire("Loss Aversion", "LA_HOLD_LARGE_LOSER", 1,
                 "Held >7% losing position instead of reassessing the loss.")
        la_core_fired = True

    if modest_winner_sale and supportive_signal and sold_most_position:
        fire("Loss Aversion", "LA_LOCK_IN_MODEST_GAIN", 1,
             "Sold most of a modest winner despite supportive signals, consistent with locking in gains to avoid losing them.")

    if ur <= LARGE_LOSS_THRESHOLD and news_sentiment == "negative" and action == "buy":
        fire("Loss Aversion", "LA_AVERAGE_DOWN_BAD_NEWS", 2,
             "Averaged down after negative news while already down >7%.")
        la_core_fired = True

    severe = (
        ur <= -0.20
        and (fundamental_signal == "weak" or news_sentiment == "negative")
    )
    high_size_avg_down = action == "buy" and ur <= LARGE_LOSS_THRESHOLD and size_level >= 3
    if la_core_fired and (severe or high_size_avg_down):
        fire("Loss Aversion", "LA_SEVERE_LOSS_OR_HIGH_SIZE", 1,
             "Severe loss or high-size averaging down after >7% loss.")

    return fires


def _evaluate_game_level(log: List[Dict]) -> List[Tuple[str, Tuple[str, int, str]]]:
    out = []

    trades = [r for r in log if r["action"] in {"buy", "sell"}]
    num_trades = len(trades)
    avg_size_level = (
        sum(int(r["size_level"]) for r in log) / len(log) if log else 0.0
    )
    if num_trades >= OC_NUM_TRADES_THRESHOLD or avg_size_level >= OC_AVG_SIZE_THRESHOLD:
        out.append((
            "Overconfidence",
            (
                "OC_EXCESSIVE_TRADING_OR_SIZE",
                2,
                f"Persistent trading (n={num_trades}) or large sizing "
                f"(avg_size_level={avg_size_level:.2f}).",
            ),
        ))

    premature_winner_sales = []
    bad_signal_large_loser_holds = []
    for row in log:
        ur = unrealized_return_before(row)
        if (
            0 < ur < 0.12
            and row["action"] == "sell"
            and row["fundamental_signal"] != "weak"
            and row["news_sentiment"] != "negative"
        ):
            premature_winner_sales.append(row)
        if (
            ur <= LARGE_LOSS_THRESHOLD
            and row["action"] == "hold"
            and (row["fundamental_signal"] == "weak" or row["news_sentiment"] == "negative")
        ):
            bad_signal_large_loser_holds.append(row)

    winner_count = len(premature_winner_sales)
    loser_count = len(bad_signal_large_loser_holds)
    disposition_core_fired = winner_count >= 1 and loser_count >= 1

    if disposition_core_fired:
        out.append((
            "Disposition Effect",
            (
                "DE_COMBINED_PATTERN",
                2,
                "Sold a modest winner early and later held a >7% loser despite bad signal.",
            ),
        ))

        avg_sell_ratio = (
            sum(sell_ratio(r) for r in premature_winner_sales) / winner_count
            if winner_count else 0.0
        )
        if winner_count >= 2 or loser_count >= 2 or avg_sell_ratio >= 0.5:
            out.append((
                "Disposition Effect",
                (
                    "DE_INTENSITY_AMPLIFIER",
                    1,
                    "Disposition pattern repeated or sold most modest winners.",
                ),
            ))

    return out


def detect_all_biases(log: List[Dict]) -> Dict[str, Dict]:
    """Run all per-round and game-level clusters on the full game log."""

    from config import BIAS_NAMES

    out = {b: {"score": 0, "raw_score": 0, "rules": []} for b in BIAS_NAMES}

    for i in range(len(log)):
        round_fires = _evaluate_round(log, i)
        for bias_name, fires in round_fires.items():
            round_raw = sum(points for _, points, _ in fires)
            out[bias_name]["raw_score"] += round_raw
            out[bias_name]["score"] += min(ROUND_SCORE_CAP, round_raw)
            for cluster_id, points, message in fires:
                out[bias_name]["rules"].append(
                    (log[i]["round"], cluster_id, points, message)
                )

    for bias_name, fire in _evaluate_game_level(log):
        cluster_id, points, message = fire
        out[bias_name]["raw_score"] += points
        out[bias_name]["score"] += points
        out[bias_name]["rules"].append(("game", cluster_id, points, message))

    for bias_name in BIAS_NAMES:
        cap = DISPOSITION_GAME_CAP if bias_name == "Disposition Effect" else GAME_SCORE_CAP
        out[bias_name]["score"] = min(cap, out[bias_name]["score"])
        out[bias_name]["tier"] = tier_for(out[bias_name]["score"])

    return out
