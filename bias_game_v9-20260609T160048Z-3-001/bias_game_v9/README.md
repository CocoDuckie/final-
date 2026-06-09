# FOMOPOLY

A Streamlit trading simulation for detecting behavioral investing biases:
Overconfidence, Herding, Availability, Framing, Loss Aversion, and
Disposition Effect.

## Setup

```bash
pip install -r requirements.txt
python smoke_test.py
streamlit run app.py
```

## Updated Flow

1. Welcome: enter player name and start.
2. Week screen: review price, market context, news, fundamentals, crowd signal,
   portfolio, and TradingView-style price chart.
3. Decision: choose Buy, Sell, or Hold. Buy/Sell require a size:
   small 25%, medium 50%, high 75%, all-in 100%. Share quantities are whole
   numbers, so percentage sizing is rounded down to the nearest whole share.
4. Checkpoint questions: answer all three scenario questions correctly to
   confirm the decision.
5. Market movement: a random-walk candlestick animation moves from the current
   price to the scenario target price with 7 one-day candles per weekly round.
   Outcome and P&L stay hidden here.
6. Outcome: reveal scenario outcome, stock return, week portfolio return,
   week P&L, and updated portfolio.
7. Results: after round 8, show total return, bias breakdown, evidence clusters,
   suggestions, decision history, and leaderboard.

## Plan-Based Updates

- Scenarios now come from the newest plan's `6. Scenario Template` sheet.
- Runtime pricing starts at 100 and uses `price_change_pct` to calculate
  `next_price`.
- Scenario groups can be shuffled while preserving pair order. The G1 setup
  pair stays first by default to preserve the overconfidence setup.
- The price path includes a final anchor after round 8, so the last round also
  reveals its target price.
- Bias scoring follows the supporting-gated amplifier design from the updated
  plan:
  - OC/HD/AV high-size amplifiers require supporting evidence.
  - Overconfidence game-level sizing uses `avg_size_level >= 1.8` over all
    runtime weeks, with hold counted as size level 0.
  - Loss Aversion and Disposition Effect use `unrealized_return_before`, the
    stock holding return versus average cost before the decision.
  - `portfolio_return` is total portfolio return versus the initial
    100,000 USD capital after buys, sells, and holds.
  - `portfolio_round_return` is the one-week portfolio return; `round_return`
    remains as a backward-compatible alias.

## Project Structure

```text
bias_game_v9/
  app.py
  config.py
  scenario_engine.py
  trading_logic.py
  bias_rules.py
  scoring.py
  data_manager.py
  charts.py
  ui_components.py
  smoke_test.py
  requirements.txt
  data/scenarios.csv
```
