"""
smoke_test.py — End-to-end pipeline test without Streamlit.

Simulates a playthrough designed to trigger every bias, runs detect_all_biases,
prints results. Use this to verify changes to bias_rules.py haven't broken
anything before launching the app.

Run:
    python smoke_test.py
"""

from scenario_engine import load_scenarios
from trading_logic import Portfolio, execute_trade
from bias_rules import detect_all_biases
from scoring import compute_results, get_suggestion
from data_manager import build_round_entry
from config import CURRENCY, NUM_ROUNDS, STARTING_CAPITAL


# A playthrough that should trigger overconfidence, herding, availability,
# framing, loss aversion, AND disposition effect.
TEST_DECISIONS = [
    ("buy",   "small"),   # R1 enter
    ("buy",   "high"),    # R2 escalate after R1 profit → OC_SELF_ATTRIB + amp
    ("buy",   "all_in"),  # R3 strong-crowd follow with all_in → HD + AV (all amps)
    ("hold",  "none"),    # R4 hold loser despite weak fundamentals → LA core
    ("sell",  "small"),   # R5 sell (sets up DE later if winner)
    ("buy",   "high"),    # R6 buy positive-spin weak fundamentals → FR all amps
    ("sell",  "medium"),  # R7 sell again
    ("sell",  "all_in"),  # R8 panic sell with negative_spin → FR sell-side
]


def main():
    print("=" * 70)
    print("BIAS GAME v9 — SMOKE TEST")
    print("=" * 70)

    scenarios = load_scenarios()
    print(f"\n✓ Loaded {len(scenarios)} scenarios")
    print(f"  Round 1 paragraph preview: "
          f"{scenarios[0].news_text[:90]}...\n")

    portfolio = Portfolio()
    print(f"Starting cash: {portfolio.cash:,.0f} {CURRENCY}")
    print(f"Starting shares: {int(portfolio.shares):,}\n")
    print("-" * 70)
    print(f"{'R':>2}  {'Action':<6} {'Size':<7}  "
          f"{'Price USD':>9}  {'Shares':>14}  "
          f"{'Cash':>14}  {'PF':>14}  "
          f"{'UR%':>8}  {'PF Ret%':>8}")
    print("-" * 70)

    log = []
    prev_value = float(STARTING_CAPITAL)

    for i in range(NUM_ROUNDS):
        scen = scenarios[i]
        action, trade_size = TEST_DECISIONS[i]
        trade = execute_trade(portfolio, action, trade_size, scen.price_now)
        entry = build_round_entry(scen, trade, portfolio, prev_value)
        log.append(entry)
        prev_value = entry["portfolio_value_end"]
        print(f"{scen.round:>2}  {action:<6} {trade_size:<7}  "
              f"{scen.price_now:>9.0f}  {int(portfolio.shares):>14,}  "
              f"{portfolio.cash:>14,.0f}  "
              f"{entry['portfolio_value_end']:>14,.0f}  "
              f"{entry['unrealized_return_before'] * 100:>+8.2f}  "
              f"{entry['portfolio_return'] * 100:>+8.2f}")

    print("\n" + "=" * 70)
    print("BIAS DETECTION RESULTS")
    print("=" * 70)

    bias_results = detect_all_biases(log)
    for bias_name, info in bias_results.items():
        print(f"\n{bias_name}: score={info['score']} "
              f"(raw={info.get('raw_score', '?')}) — {info['tier']}")
        for rnd, cluster_id, points, msg in info["rules"]:
            rnd_label = f"R{rnd}" if isinstance(rnd, int) else "Game"
            print(f"  {rnd_label} {cluster_id} +{points}: {msg}")

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    result = compute_results("TestPlayer", log, bias_results)
    print(f"  Initial capital:    {result.initial_capital:>16,.0f} {CURRENCY}")
    print(f"  Final value:        {result.final_value:>16,.0f} {CURRENCY}")
    print(f"  Total return:       {result.total_return_pct:>+16.2f}%")
    print(f"  Total bias score:   {result.total_bias_score:>16d}")
    print(f"  Rationality score:  {result.rationality_score:>16.1f} / 100")

    print("\n" + "=" * 70)
    print("SUGGESTIONS")
    print("=" * 70)
    for bias_name, info in bias_results.items():
        suggestion = get_suggestion(bias_name, info["tier"])
        print(f"\n[{bias_name} — {info['tier']}]\n  {suggestion}")


if __name__ == "__main__":
    main()
