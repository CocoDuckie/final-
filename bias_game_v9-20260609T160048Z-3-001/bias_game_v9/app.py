"""
app.py - Streamlit controller for the Behavioral Investing Simulation Game.

Flow:
welcome -> round -> quiz -> movement -> outcome -> ... -> results
"""

import random
import time

import streamlit as st
import streamlit.components.v1 as components

from bias_rules import detect_all_biases
from charts import (
    animated_candlestick_chart,
    bias_bar_chart,
    leaderboard_chart,
    portfolio_chart,
)
from config import (
    CANDLES_PER_ROUND,
    COURSE_CODE,
    CURRENCY,
    FRAME_DURATION_MS,
    GAME_NAME,
    NUM_ROUNDS,
    SKIP_ROUND_QUESTIONS,
    STARTING_CAPITAL,
)
from data_manager import (
    append_leaderboard,
    build_round_entry,
    load_leaderboard,
    save_round_log,
)
from scenario_engine import get_scenario, load_scenarios
from scoring import compute_results, get_bias_definition, get_suggestion
from trading_logic import Portfolio, execute_trade
from ui_components import (
    inject_css,
    render_bias_card,
    render_chart_shell_start,
    render_crowd_panel,
    render_decision_panel,
    render_fundamentals_panel,
    render_hero,
    render_market_context,
    render_movement_status,
    render_news_panel,
    render_outcome,
    render_portfolio_panel,
    render_price_card,
    render_quiz_panel,
    render_round_banner,
    render_shell_end,
)


st.set_page_config(
    page_title=GAME_NAME,
    page_icon="BI",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()


def init_state():
    defaults = {
        "stage": "welcome",
        "current_round": 1,
        "player_name": "",
        "portfolio": Portfolio(),
        "scenarios": [],
        "round_log": [],
        "pending_decision": None,
        "last_trade_result": None,
        "last_scenario": None,
        "last_prev_portfolio_value": float(STARTING_CAPITAL),
        "chart_seed": random.randint(0, 100_000),
        "scenario_seed": random.randint(0, 100_000),
        "results_saved": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


init_state()


PRICE_CHART_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "doubleClick": "reset",
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
        "toImage",
    ],
}


def ensure_scenarios_loaded():
    if not st.session_state.scenarios:
        st.session_state.scenarios = load_scenarios(
            shuffle_groups=True,
            seed=st.session_state.scenario_seed,
            keep_setup_first=True,
        )


def price_path():
    scenarios = st.session_state.scenarios
    if not scenarios:
        return []
    return [scenarios[0].price_now] + [scenario.next_price for scenario in scenarios]


def media_intensities():
    return [scenario.media_intensity for scenario in st.session_state.scenarios]


def trades_so_far():
    return [
        {"round": entry["round"], "action": entry["action"], "price": entry["price_now"]}
        for entry in st.session_state.round_log
        if entry["action"] in {"buy", "sell"}
    ]


def render_static_price_chart(current_step: int, _height_key: str):
    render_chart_shell_start()
    fig = animated_candlestick_chart(
        all_prices=price_path(),
        media_intensities=media_intensities(),
        current_round=current_step,
        animate_transition=False,
        player_trades=trades_so_far(),
        seed=st.session_state.chart_seed,
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PRICE_CHART_CONFIG,
    )
    render_shell_end()


def render_autoplay_chart(fig, key: str):
    """Render Plotly HTML and trigger animation on load."""

    chart_html = fig.to_html(
        include_plotlyjs=True,
        full_html=False,
        config=PRICE_CHART_CONFIG,
        div_id=f"plotly-{key}",
    )
    autoplay_js = f"""
    <script>
      (function() {{
        function playWhenReady() {{
          const el = document.getElementById('plotly-{key}');
          if (el && window.Plotly && el.data && el.layout) {{
            Plotly.animate('plotly-{key}', null, {{
              frame: {{ duration: {FRAME_DURATION_MS}, redraw: true }},
              transition: {{ duration: 0 }},
              mode: 'immediate',
              fromcurrent: false
            }});
          }} else {{
            setTimeout(playWhenReady, 120);
          }}
        }}
        setTimeout(playWhenReady, 250);
      }})();
    </script>
    """
    components.html(chart_html + autoplay_js, height=535, scrolling=False)


def show_welcome():
    st.markdown(
        f"""
        <div class="opening-stage">
          <div class="opening-candles">
            <i class="opening-candle up" style="height:46px;animation-delay:.0s"></i>
            <i class="opening-candle down" style="height:76px;animation-delay:.2s"></i>
            <i class="opening-candle up" style="height:58px;animation-delay:.4s"></i>
            <i class="opening-candle up" style="height:92px;animation-delay:.6s"></i>
            <i class="opening-candle down" style="height:70px;animation-delay:.8s"></i>
            <i class="opening-candle up" style="height:116px;animation-delay:1.0s"></i>
            <i class="opening-candle down" style="height:84px;animation-delay:1.2s"></i>
            <i class="opening-candle up" style="height:132px;animation-delay:1.4s"></i>
            <i class="opening-candle up" style="height:104px;animation-delay:1.6s"></i>
            <i class="opening-candle down" style="height:66px;animation-delay:1.8s"></i>
            <i class="opening-candle up" style="height:142px;animation-delay:2.0s"></i>
            <i class="opening-candle down" style="height:96px;animation-delay:2.2s"></i>
            <i class="opening-candle up" style="height:124px;animation-delay:2.4s"></i>
            <i class="opening-candle up" style="height:82px;animation-delay:2.6s"></i>
            <i class="opening-candle down" style="height:112px;animation-delay:2.8s"></i>
            <i class="opening-candle up" style="height:150px;animation-delay:3.0s"></i>
            <i class="opening-candle down" style="height:78px;animation-delay:3.2s"></i>
            <i class="opening-candle up" style="height:118px;animation-delay:3.4s"></i>
            <i class="opening-candle up" style="height:136px;animation-delay:3.6s"></i>
            <i class="opening-candle down" style="height:94px;animation-delay:3.8s"></i>
            <i class="opening-candle up" style="height:126px;animation-delay:4.0s"></i>
            <i class="opening-candle down" style="height:88px;animation-delay:4.2s"></i>
          </div>
          <div class="opening-grid">
            <div>
              <div class="opening-kicker"><span></span>{COURSE_CODE} // Behavioral Trading Arena</div>
              <div class="opening-logo">{GAME_NAME}</div>
              <div class="opening-subtitle">
                Enter an eight-week market simulation where every headline, crowd signal,
                price move, and trade size can reveal how you make decisions under pressure.
              </div>
              <div class="opening-command-row">
                <div class="opening-chip">Capital {STARTING_CAPITAL:,.0f} {CURRENCY}</div>
                <div class="opening-chip">8 market weeks</div>
                <div class="opening-chip">One stock. Many traps.</div>
              </div>
            </div>
            <div class="opening-console">
              <div class="console-top">
                <div class="console-title">Market Boot Sequence</div>
                <div class="console-status">ONLINE</div>
              </div>
              <div class="console-bars">
                <div class="console-bar"><span>Liquidity</span><div class="console-meter"><span style="width:78%"></span></div><b>78%</b></div>
                <div class="console-bar"><span>Noise</span><div class="console-meter"><span style="width:91%"></span></div><b>91%</b></div>
                <div class="console-bar"><span>Bias Risk</span><div class="console-meter"><span style="width:86%"></span></div><b>86%</b></div>
                <div class="console-bar"><span>Control</span><div class="console-meter"><span style="width:42%"></span></div><b>42%</b></div>
              </div>
            </div>
          </div>
          <div class="opening-ticker">
            <div class="opening-ticker-track">
              <span>STEELSTOX <b>+6.2%</b></span><span>STEEL SPREAD <b>+1.3%</b></span>
              <span>CROWD HEAT <i>HIGH</i></span><span>RISK-OFF ALERT <i>ACTIVE</i></span>
              <span>FOMO INDEX <b>ONLINE</b></span><span>BIAS SCANNER <b>READY</b></span>
              <span>STEELSTOX <b>+6.2%</b></span><span>STEEL SPREAD <b>+1.3%</b></span>
              <span>CROWD HEAT <i>HIGH</i></span><span>RISK-OFF ALERT <i>ACTIVE</i></span>
              <span>FOMO INDEX <b>ONLINE</b></span><span>BIAS SCANNER <b>READY</b></span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.16, 0.84])
    with left:
        st.markdown(
            f"""
            <div class="opening-rules-card">
              <div class="opening-rules-title">Mission Briefing</div>
              <div class="body-copy">
                <p>You begin with <strong>{STARTING_CAPITAL:,.0f} {CURRENCY}</strong> in virtual capital and trade one stock through eight scripted market weeks.</p>
                <p>Each week gives you news, fundamentals, crowd sentiment, a decision checkpoint, a simulated market move, and an outcome summary.</p>
                <p>The final screen reports portfolio performance and behavioral-bias evidence from your decisions.</p>
              </div>
              <div class="opening-rule-grid">
                <div class="opening-rule-item"><b>Read</b><span>Compare the market context, news, fundamentals, and crowd signal before acting.</span></div>
                <div class="opening-rule-item"><b>Trade</b><span>Choose Buy, Sell, or Hold. Buy and Sell require a defined position size.</span></div>
                <div class="opening-rule-item"><b>Reveal</b><span>Watch the simulated price path move before the outcome and P&L are shown.</span></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="opening-start-card">
              <div class="opening-start-title">Player Access</div>
              <div class="opening-start-copy">
                Register your trader name to unlock the simulation terminal.
                Your choices will be logged week by week for the final behavioral profile.
              </div>
            """,
            unsafe_allow_html=True,
        )
        name = st.text_input("Player name", placeholder="e.g. Minh Anh", key="name_input")
        if st.button("Start Trading", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                st.session_state.player_name = name.strip()
                st.session_state.scenarios = load_scenarios(
                    shuffle_groups=True,
                    seed=st.session_state.scenario_seed,
                    keep_setup_first=True,
                )
                st.session_state.stage = "round"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def show_round():
    ensure_scenarios_loaded()
    round_num = st.session_state.current_round
    scenario = get_scenario(st.session_state.scenarios, round_num)

    render_round_banner(round_num, NUM_ROUNDS, "Read the information set, choose an action, then answer the checkpoint questions.")

    left, right = st.columns([0.92, 1.15])
    with left:
        render_price_card(scenario.price_now)
        render_market_context(scenario)
        render_news_panel(scenario)
        render_fundamentals_panel(scenario)
        render_crowd_panel(scenario)

    with right:
        render_static_price_chart(round_num, f"static_round_{round_num}")
        render_portfolio_panel(st.session_state.portfolio, scenario.price_now)
        decision = render_decision_panel(st.session_state.portfolio, scenario.price_now)
        if decision["action"] is not None:
            if SKIP_ROUND_QUESTIONS:
                _process_confirmed_decision(decision)
                return
            st.session_state.pending_decision = decision
            st.session_state.stage = "quiz"
            st.rerun()


def show_quiz():
    ensure_scenarios_loaded()
    round_num = st.session_state.current_round
    scenario = get_scenario(st.session_state.scenarios, round_num)
    decision = st.session_state.pending_decision

    if not decision:
        st.session_state.stage = "round"
        st.rerun()

    render_round_banner(round_num, NUM_ROUNDS, "Answer all checkpoint questions correctly to confirm your decision.")
    result = render_quiz_panel(scenario, decision)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back to Decision", use_container_width=True):
            st.session_state.stage = "round"
            st.rerun()

    if result.get("submitted"):
        if result.get("all_correct"):
            _process_confirmed_decision(decision)
        else:
            wrong = result.get("incorrect", [])
            missing = result.get("missing", [])
            detail = []
            if missing:
                detail.append(f"missing: {', '.join(map(str, missing))}")
            if wrong:
                detail.append(f"incorrect: {', '.join(map(str, wrong))}")
            st.error("Please review the questions. " + "; ".join(detail))


def _process_confirmed_decision(decision: dict):
    scenario = get_scenario(st.session_state.scenarios, st.session_state.current_round)
    portfolio = st.session_state.portfolio
    prev_value = portfolio.value(scenario.price_now)
    trade = execute_trade(portfolio, decision["action"], decision["trade_size"], scenario.price_now)
    entry = build_round_entry(scenario, trade, portfolio, prev_value)

    st.session_state.round_log.append(entry)
    st.session_state.last_trade_result = trade
    st.session_state.last_scenario = scenario
    st.session_state.last_prev_portfolio_value = prev_value
    st.session_state.pending_decision = None
    st.session_state.stage = "movement"
    st.rerun()


def show_movement():
    scenario = st.session_state.last_scenario
    if scenario is None:
        st.session_state.stage = "round"
        st.rerun()

    round_num = st.session_state.current_round
    render_round_banner(round_num, NUM_ROUNDS, "Market simulation is running. Outcome is hidden until the target price prints.")
    render_movement_status(scenario)

    render_chart_shell_start()
    fig = animated_candlestick_chart(
        all_prices=price_path(),
        media_intensities=media_intensities(),
        current_round=round_num + 1,
        animate_transition=True,
        player_trades=trades_so_far(),
        seed=st.session_state.chart_seed,
    )
    render_autoplay_chart(fig, key=f"movement_r{round_num}")
    render_shell_end()

    delay = (CANDLES_PER_ROUND * FRAME_DURATION_MS) / 1000 + 0.8
    time.sleep(delay)
    st.session_state.stage = "outcome"
    st.rerun()


def show_outcome():
    scenario = st.session_state.last_scenario
    if scenario is None:
        st.session_state.stage = "round"
        st.rerun()

    round_num = st.session_state.current_round
    portfolio = st.session_state.portfolio
    portfolio_value_now = portfolio.value(scenario.next_price)
    portfolio_change = portfolio_value_now - st.session_state.last_prev_portfolio_value

    render_round_banner(round_num, NUM_ROUNDS, "Outcome revealed. Review the round P&L before moving on.")

    left, right = st.columns([0.95, 1.05])
    with left:
        render_outcome(
            scenario.price_now,
            scenario.next_price,
            portfolio_change,
            scenario.outcome_text,
        )
        render_portfolio_panel(portfolio, scenario.next_price)
        if round_num < NUM_ROUNDS:
            if st.button("Continue to Next Week", type="primary", use_container_width=True):
                st.session_state.current_round += 1
                st.session_state.stage = "round"
                st.rerun()
        else:
            if st.button("See Bias Results", type="primary", use_container_width=True):
                st.session_state.stage = "results"
                st.rerun()

    with right:
        render_static_price_chart(round_num + 1, f"outcome_chart_{round_num}")


def show_results():
    log = st.session_state.round_log
    name = st.session_state.player_name or "Player"
    bias_results = detect_all_biases(log)
    result = compute_results(name, log, bias_results)

    if not st.session_state.results_saved:
        save_round_log(log, name)
        append_leaderboard(
            name,
            result.total_return_pct,
            result.total_bias_score,
            result.rationality_score,
        )
        st.session_state.results_saved = True

    render_hero(f"Game Over, {name}", "Your portfolio performance and behavioral profile are ready.")

    st.markdown(
        f"""
        <div class="result-metric-grid">
          <div class="metric-tile">
            <span class="metric-info" data-tip="Final value = ending cash + ending stock value.">i</span>
            <div class="metric-label">Final Value</div>
            <div class="metric-value">{result.final_value:,.0f} {CURRENCY}</div>
          </div>
          <div class="metric-tile">
            <span class="metric-info" data-tip="Portfolio return = (final value - starting capital) / starting capital.">i</span>
            <div class="metric-label">Portfolio Return</div>
            <div class="metric-value">{result.total_return_pct:+.2f}%</div>
          </div>
          <div class="metric-tile">
            <span class="metric-info" data-tip="Total bias score is the sum of capped bias evidence points detected from your decisions.">i</span>
            <div class="metric-label">Total Bias Score</div>
            <div class="metric-value">{result.total_bias_score}</div>
          </div>
          <div class="metric-tile">
            <span class="metric-info" data-tip="Rationality score combines portfolio performance with bias control. Higher return improves it; detected bias evidence lowers it.">i</span>
            <div class="metric-label">Rationality Score</div>
            <div class="metric-value">{result.rationality_score} / 100</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_chart_shell_start()
        st.plotly_chart(portfolio_chart(log), use_container_width=True, config={"displayModeBar": False})
        render_shell_end()
    with chart_right:
        render_chart_shell_start()
        st.plotly_chart(bias_bar_chart(bias_results), use_container_width=True, config={"displayModeBar": False})
        render_shell_end()

    st.markdown('<div class="section-title">Bias Breakdown</div>', unsafe_allow_html=True)
    items = list(bias_results.items())
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        for offset in (0, 1):
            if i + offset < len(items):
                bias_name, info = items[i + offset]
                with cols[offset]:
                    render_bias_card(
                        bias_name,
                        info,
                        get_suggestion(bias_name, info["tier"]),
                        get_bias_definition(bias_name),
                    )

    with st.expander("Week-by-Week Decision History"):
        import pandas as pd

        display_cols = [
            "round",
            "scenario_pair_id",
            "price_now",
            "next_price",
            "action",
            "trade_size",
            "shares_after",
            "cash_after",
            "portfolio_value_end",
            "unrealized_return_before",
            "portfolio_return",
            "portfolio_round_return",
        ]
        df = pd.DataFrame(log)
        df = df[[c for c in display_cols if c in df.columns]].copy()
        if not df.empty:
            if "shares_after" in df.columns:
                df["shares_after"] = df["shares_after"].astype(int)
            df["cash_after"] = df["cash_after"].round(0)
            if "portfolio_value_end" in df.columns:
                df["portfolio_value_end"] = df["portfolio_value_end"].round(0)
            for return_col in (
                "unrealized_return_before",
                "portfolio_return",
                "portfolio_round_return",
            ):
                if return_col in df.columns:
                    df[return_col] = (df[return_col] * 100).round(2)
            df = df.rename(columns={
                "round": "week",
                "price_now": "price_now_usd",
                "next_price": "next_price_usd",
                "cash_after": "cash_after_usd",
                "portfolio_value_end": "portfolio_value_usd",
                "unrealized_return_before": "unrealized_return_pct",
                "portfolio_return": "portfolio_return_pct",
                "portfolio_round_return": "week_portfolio_return_pct",
            })
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Leaderboard</div>', unsafe_allow_html=True)
    leaderboard = load_leaderboard()
    if not leaderboard.empty:
        lb_left, lb_right = st.columns([1, 1])
        with lb_left:
            render_chart_shell_start()
            fig = leaderboard_chart(leaderboard)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            render_shell_end()
        with lb_right:
            st.dataframe(leaderboard.head(10), use_container_width=True, hide_index=True)

    if st.button("Play Again", type="primary"):
        reset_game()
        st.rerun()


stage = st.session_state.stage

if stage == "welcome":
    show_welcome()
elif stage == "round":
    show_round()
elif stage == "quiz":
    show_quiz()
elif stage == "movement":
    show_movement()
elif stage == "outcome":
    show_outcome()
elif stage == "results":
    show_results()
else:
    st.error(f"Unknown stage: {stage}")
    if st.button("Reset"):
        reset_game()
        st.rerun()
