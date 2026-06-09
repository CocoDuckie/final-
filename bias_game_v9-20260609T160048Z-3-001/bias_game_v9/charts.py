"""
charts.py - Plotly charts for the trading simulation.

The main price chart uses a Brownian-bridge random walk between scenario price
anchors. During the movement stage, the latest transition is revealed candle by
candle before the outcome card is shown.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import plotly.graph_objects as go

from config import (
    ASSET_NAME,
    CANDLE_VOLATILITY,
    CANDLE_WICK_RANGE,
    CANDLES_PER_ROUND,
    COLOR_ACCENT,
    COLOR_DANGER,
    COLOR_NEUTRAL,
    COLOR_SUCCESS,
    COLOR_WARNING,
    CURRENCY,
    FRAME_DURATION_MS,
    RANDOM_SEED,
    VOLATILITY_BY_INTENSITY,
)


CHART_BG = "#FFFFFF"
GRID = "rgba(17, 24, 39, 0.20)"
TEXT = "#111827"
MUTED = "#6B7280"
TV_GREEN = "#26A69A"
TV_RED = "#EF5350"


@dataclass
class Candle:
    x: float
    open: float
    high: float
    low: float
    close: float


def _brownian_bridge(
    p_start: float,
    p_end: float,
    n: int,
    sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate n points that start at p_start and end exactly at p_end."""

    d_w = rng.normal(0, 1, size=n - 1)
    w = np.concatenate([[0.0], np.cumsum(d_w)])
    t = np.linspace(0, 1, n)
    bridge = w - t * w[-1]
    trend = p_start * (1 - t) + p_end * t
    return trend + sigma * bridge


def _generate_candles_between(
    anchor_idx: int,
    p_start: float,
    p_end: float,
    media_intensity: int,
    rng: np.random.Generator,
) -> List[Candle]:
    sigma = VOLATILITY_BY_INTENSITY.get(media_intensity, CANDLE_VOLATILITY)
    prices = _brownian_bridge(p_start, p_end, CANDLES_PER_ROUND + 1, sigma, rng)

    candles = []
    for i in range(CANDLES_PER_ROUND):
        open_ = float(prices[i])
        close = float(prices[i + 1])
        wick_up = abs(rng.normal(0, CANDLE_WICK_RANGE))
        wick_down = abs(rng.normal(0, CANDLE_WICK_RANGE))
        candles.append(
            Candle(
                x=anchor_idx + (i + 0.5) / CANDLES_PER_ROUND,
                open=open_,
                high=max(open_, close) + wick_up,
                low=min(open_, close) - wick_down,
                close=close,
            )
        )
    return candles


def generate_all_candles(
    price_path: List[float],
    media_intensities: List[int],
    seed: int = None,
) -> Tuple[List[Candle], List[Tuple[float, float]]]:
    rng = np.random.default_rng(seed if seed is not None else RANDOM_SEED)
    anchors = [(i + 1.0, float(price)) for i, price in enumerate(price_path)]
    candles = []
    for i in range(len(price_path) - 1):
        intensity = media_intensities[i] if i < len(media_intensities) else 1
        candles.extend(
            _generate_candles_between(
                anchor_idx=i + 1,
                p_start=float(price_path[i]),
                p_end=float(price_path[i + 1]),
                media_intensity=int(intensity),
                rng=rng,
            )
        )
    return candles, anchors


def animated_candlestick_chart(
    all_prices: List[float],
    media_intensities: List[int],
    current_round: int,
    animate_transition: bool = False,
    player_trades: List[Dict] = None,
    seed: int = None,
):
    """Build a TradingView-style candlestick chart.

    all_prices is now a price path of anchors: R1 price plus every revealed
    next_price, so an 8-round game has 9 anchors (R1..R8..Final).
    current_round means number of anchors currently visible.
    """

    if not all_prices:
        return _empty_chart(1)

    current_round = max(1, min(current_round, len(all_prices)))
    visible_prices = all_prices[:current_round]
    candles, anchors = generate_all_candles(
        visible_prices,
        media_intensities[: max(0, current_round - 1)],
        seed=seed,
    )

    if animate_transition and current_round >= 2:
        full_count = (current_round - 2) * CANDLES_PER_ROUND
        initial_candles = candles[:full_count]
        initial_anchors = anchors[: current_round - 1]
    else:
        initial_candles = candles
        initial_anchors = anchors

    fig = go.Figure()
    _add_price_traces(fig, initial_candles, initial_anchors, player_trades or [])

    if animate_transition and current_round >= 2:
        full_count = (current_round - 2) * CANDLES_PER_ROUND
        frames = []
        for k in range(1, CANDLES_PER_ROUND + 1):
            frame_candles = candles[: full_count + k]
            frame_anchors = anchors[: current_round - 1]
            if k == CANDLES_PER_ROUND:
                frame_anchors = anchors
            frames.append(
                go.Frame(
                    data=_build_frame_data(
                        frame_candles,
                        frame_anchors,
                        player_trades or [],
                    ),
                    name=f"f{k}",
                )
            )
        fig.frames = frames
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    visible=False,
                    buttons=[
                        dict(
                            label="Play",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=FRAME_DURATION_MS, redraw=True),
                                    transition=dict(duration=0),
                                    fromcurrent=False,
                                    mode="immediate",
                                ),
                            ],
                        )
                    ],
                )
            ]
        )

    _style_price_chart(fig, all_prices, candles, visible_prices)
    return fig


def _empty_chart(n_rounds: int):
    fig = go.Figure()
    fig.update_layout(
        height=440,
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        xaxis=dict(visible=False, range=[0.5, n_rounds + 0.5]),
        yaxis=dict(visible=False),
        margin=dict(l=12, r=72, t=44, b=28),
    )
    return fig


def _candlestick_kwargs(candles: List[Candle]) -> dict:
    return dict(
        x=[c.x for c in candles],
        open=[c.open for c in candles],
        high=[c.high for c in candles],
        low=[c.low for c in candles],
        close=[c.close for c in candles],
        increasing_line_color=TV_GREEN,
        decreasing_line_color=TV_RED,
        increasing_fillcolor=TV_GREEN,
        decreasing_fillcolor=TV_RED,
        line_width=0.9,
        whiskerwidth=0.22,
        showlegend=False,
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#CBD5E1", font_color=TEXT),
    )


def _anchor_trace(anchors: List[Tuple[float, float]]):
    return go.Scatter(
        x=[a[0] for a in anchors],
        y=[a[1] for a in anchors],
        mode="markers",
        marker=dict(size=0.1, color="rgba(0,0,0,0)"),
        text=[f"{a[1]:.2f}" for a in anchors],
        hovertemplate=f"Anchor %{{x:.0f}}<br>Price: %{{y:.2f}} {CURRENCY}<extra></extra>",
        showlegend=False,
    )


def _trade_traces(trades: List[Dict]):
    buys = [t for t in trades if t["action"] == "buy"]
    sells = [t for t in trades if t["action"] == "sell"]
    buy_trace = go.Scatter(
        x=[t["round"] for t in buys],
        y=[t["price"] for t in buys],
        mode="markers",
        marker=dict(
            color=COLOR_SUCCESS,
            size=15,
            symbol="triangle-up",
            line=dict(color="#ECFDF5", width=1.4),
        ),
        hovertemplate=f"BUY R%{{x}}<br>%{{y:.2f}} {CURRENCY}<extra></extra>",
        showlegend=False,
    )
    sell_trace = go.Scatter(
        x=[t["round"] for t in sells],
        y=[t["price"] for t in sells],
        mode="markers",
        marker=dict(
            color=COLOR_DANGER,
            size=15,
            symbol="triangle-down",
            line=dict(color="#FEF2F2", width=1.4),
        ),
        hovertemplate=f"SELL R%{{x}}<br>%{{y:.2f}} {CURRENCY}<extra></extra>",
        showlegend=False,
    )
    return buy_trace, sell_trace


def _add_price_traces(
    fig: go.Figure,
    candles: List[Candle],
    anchors: List[Tuple[float, float]],
    trades: List[Dict],
) -> None:
    fig.add_trace(go.Candlestick(**_candlestick_kwargs(candles)))
    fig.add_trace(_anchor_trace(anchors))
    buy_trace, sell_trace = _trade_traces(trades)
    fig.add_trace(buy_trace)
    fig.add_trace(sell_trace)


def _build_frame_data(
    candles: List[Candle],
    anchors: List[Tuple[float, float]],
    trades: List[Dict],
) -> list:
    buy_trace, sell_trace = _trade_traces(trades)
    return [
        go.Candlestick(**_candlestick_kwargs(candles)),
        _anchor_trace(anchors),
        buy_trace,
        sell_trace,
    ]


def _style_price_chart(
    fig: go.Figure,
    full_price_path: List[float],
    candles: List[Candle],
    visible_prices: List[float],
) -> None:
    all_y = [c.low for c in candles] + [c.high for c in candles] + visible_prices
    if all_y:
        y_min = min(all_y)
        y_max = max(all_y)
        pad = max((y_max - y_min) * 0.14, 2.0)
        y_range = [y_min - pad, y_max + pad]
    else:
        p = full_price_path[0]
        y_range = [p - 5, p + 5]

    visible_anchor_count = max(1, len(visible_prices))
    tickvals = list(range(1, visible_anchor_count + 1))
    ticktext = [f"W{i}" for i in range(1, visible_anchor_count)]
    if visible_anchor_count == len(full_price_path):
        ticktext.append("Final")
    else:
        ticktext.append(f"W{visible_anchor_count}")

    if candles:
        x_range = [1, visible_anchor_count]
        last_open = candles[-1].open
        last_close = candles[-1].close
    else:
        x_range = [1, max(2, visible_anchor_count)]
        last_open = visible_prices[-1]
        last_close = visible_prices[-1]

    delta = last_close - (candles[-2].close if len(candles) > 1 else last_open)
    price_color = TV_GREEN if delta >= 0 else TV_RED

    fig.update_layout(
        height=470,
        margin=dict(l=14, r=112, t=48, b=32),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif"),
        dragmode="pan",
        hovermode="x",
        uirevision=f"price-chart-{visible_anchor_count}",
        showlegend=False,
        xaxis=dict(
            title="",
            range=x_range,
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            gridcolor=GRID,
            griddash="dot",
            linecolor="rgba(17, 24, 39, 0.12)",
            tickfont=dict(color=MUTED, size=12),
            zeroline=False,
            rangeslider=dict(visible=False),
            fixedrange=False,
            showspikes=True,
            spikemode="across",
            spikecolor="rgba(17, 24, 39, 0.34)",
            spikedash="dot",
            spikethickness=1,
        ),
        yaxis=dict(
            range=y_range,
            side="right",
            tickformat=".2f",
            gridcolor=GRID,
            griddash="dot",
            linecolor="rgba(17, 24, 39, 0.12)",
            zeroline=False,
            fixedrange=False,
            tickfont=dict(color=TEXT, size=13),
            showspikes=True,
            spikemode="across",
            spikecolor="rgba(17, 24, 39, 0.34)",
            spikedash="dot",
            spikethickness=1,
        ),
    )
    fig.add_shape(
        type="line",
        xref="paper",
        yref="y",
        x0=0,
        x1=1,
        y0=last_close,
        y1=last_close,
        line=dict(color=price_color, width=1, dash="dot"),
    )
    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1.006,
        y=last_close,
        text=f"{last_close:.2f} {CURRENCY}",
        showarrow=False,
        xanchor="left",
        yanchor="middle",
        bgcolor=price_color,
        bordercolor=price_color,
        borderpad=4,
        font=dict(size=13, color="#FFFFFF"),
    )
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=1.075,
        text=f"<b>{ASSET_NAME}</b> - 1D - FOMOPOLY",
        showarrow=False,
        font=dict(size=18, color=TEXT),
        align="left",
        xanchor="left",
    )


def portfolio_chart(log: List[Dict]):
    rounds = [r["round"] for r in log]
    values = [r.get("portfolio_value_end", r.get("portfolio_value")) for r in log]
    y_min = 80_000
    y_max = max(values + [100_000]) if values else 100_000
    y_pad = max((y_max - y_min) * 0.08, 2_000)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rounds,
            y=values,
            mode="lines+markers",
            line=dict(color="#22D3EE", width=3),
            marker=dict(size=9, color="#A7F3D0", line=dict(color="#0F172A", width=1.4)),
            fill="tozeroy",
            fillcolor="rgba(34, 211, 238, 0.12)",
            hovertemplate=f"Week %{{x}}<br>Value: %{{y:,.0f}} {CURRENCY}<extra></extra>",
        )
    )
    _style_small_chart(fig, "Portfolio value")
    fig.update_xaxes(tickmode="linear", dtick=1)
    fig.update_yaxes(tickformat=",.0f", range=[y_min, y_max + y_pad])
    return fig


TIER_COLOR = {
    "None": COLOR_NEUTRAL,
    "Mild": COLOR_SUCCESS,
    "Moderate": COLOR_WARNING,
    "Strong": "#F97316",
    "Very Strong": COLOR_DANGER,
}


def bias_bar_chart(bias_results: Dict[str, Dict]):
    names = list(bias_results.keys())
    scores = [bias_results[b]["score"] for b in names]
    tiers = [bias_results[b]["tier"] for b in names]
    colors = [TIER_COLOR.get(t, COLOR_NEUTRAL) for t in tiers]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=scores,
            y=names,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{s} | {t}" for s, t in zip(scores, tiers)],
            textposition="outside",
            textfont=dict(color="#000000"),
            hovertemplate="%{y}<br>Score: %{x}<extra></extra>",
        )
    )
    _style_small_chart(fig, "Bias scores")
    fig.update_layout(margin=dict(l=140, r=58, t=58, b=38))
    fig.update_xaxes(range=[0, max(scores + [7]) + 1])
    fig.update_yaxes(autorange="reversed")
    return fig


def leaderboard_chart(df):
    if df.empty:
        return None
    top = df.head(10)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=top["player_name"],
            y=top["rationality_score"],
            marker=dict(color=COLOR_ACCENT),
            text=top["rationality_score"],
            textposition="outside",
            textfont=dict(color="#000000"),
            hovertemplate="%{x}<br>Rationality: %{y}<br>Return: %{customdata}%<extra></extra>",
            customdata=top["total_return_pct"],
        )
    )
    _style_small_chart(fig, "Leaderboard")
    fig.update_yaxes(range=[0, 105])
    return fig


def _style_small_chart(fig: go.Figure, title: str) -> None:
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#000000"), x=0.02, xanchor="left"),
        height=350,
        plot_bgcolor="rgba(255, 255, 255, 0)",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        font=dict(color="#000000", family="Inter, Segoe UI, Arial, sans-serif"),
        margin=dict(l=58, r=28, t=58, b=38),
        showlegend=False,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#000000"),
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#000000"),
    )
