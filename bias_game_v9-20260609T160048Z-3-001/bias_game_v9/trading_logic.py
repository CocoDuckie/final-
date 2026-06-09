"""
trading_logic.py - Execute Buy / Sell with percentage sizing, or Hold.

Plan-final semantics:
- small=25%, medium=50%, high=75%, all_in=100%.
- BUY spends size_pct of available cash.
- SELL sells size_pct of current holdings.
- HOLD has no size and no position change.
- Shares are whole numbers; percentage sizing is rounded down to whole shares.
"""

from dataclasses import dataclass
import math

from config import STARTING_CAPITAL, TRADE_SIZE_MAP


@dataclass
class Portfolio:
    """Player portfolio state. Mutated in place by execute_*()."""

    cash: float = float(STARTING_CAPITAL)
    shares: int = 0
    avg_cost: float = 0.0

    def value(self, price: float) -> float:
        return self.cash + self.shares * price


def size_to_pct(trade_size: str) -> float:
    """Convert trade_size to fraction in [0, 1]."""

    return TRADE_SIZE_MAP[trade_size][1]


def size_to_level(trade_size: str) -> int:
    """Convert trade_size to size_level in {0, 1, 2, 3, 4}."""

    return TRADE_SIZE_MAP[trade_size][0]


@dataclass
class TradeResult:
    """Result of one trade, consumed by data_manager."""

    action: str
    trade_size: str
    size_level: int
    cash_before: float
    shares_before: int
    shares_after: int
    cash_after: float
    avg_cost_before: float
    avg_cost_after: float
    shares_traded: int = 0


def execute_buy(portfolio: Portfolio, trade_size: str, price: float) -> TradeResult:
    """Buy up to size_pct x cash worth of whole shares at price_now."""

    size_pct = size_to_pct(trade_size)
    shares_before = int(portfolio.shares)
    cash_before = portfolio.cash
    avg_cost_before = portfolio.avg_cost

    target_cash_to_spend = cash_before * size_pct
    shares_to_buy = math.floor(target_cash_to_spend / price) if price > 0 else 0
    if shares_to_buy <= 0:
        raise ValueError("Not enough cash to buy 1 share at the current price.")
    cash_spent = shares_to_buy * price

    if shares_before + shares_to_buy > 0:
        new_avg_cost = (
            shares_before * avg_cost_before + cash_spent
        ) / (shares_before + shares_to_buy)
    else:
        new_avg_cost = 0.0

    portfolio.shares = shares_before + shares_to_buy
    portfolio.cash = cash_before - cash_spent
    portfolio.avg_cost = new_avg_cost

    return TradeResult(
        action="buy",
        trade_size=trade_size,
        size_level=size_to_level(trade_size),
        cash_before=cash_before,
        shares_before=shares_before,
        shares_after=portfolio.shares,
        cash_after=portfolio.cash,
        avg_cost_before=avg_cost_before,
        avg_cost_after=portfolio.avg_cost,
        shares_traded=shares_to_buy,
    )


def execute_sell(portfolio: Portfolio, trade_size: str, price: float) -> TradeResult:
    """Sell size_pct x current holdings, rounded down to whole shares."""

    size_pct = size_to_pct(trade_size)
    shares_before = int(portfolio.shares)
    cash_before = portfolio.cash
    avg_cost_before = portfolio.avg_cost

    shares_to_sell = shares_before if trade_size == "all_in" else math.floor(shares_before * size_pct)
    proceeds = shares_to_sell * price

    portfolio.shares = shares_before - shares_to_sell
    portfolio.cash = cash_before + proceeds
    if portfolio.shares == 0:
        portfolio.avg_cost = 0.0

    return TradeResult(
        action="sell",
        trade_size=trade_size,
        size_level=size_to_level(trade_size),
        cash_before=cash_before,
        shares_before=shares_before,
        shares_after=portfolio.shares,
        cash_after=portfolio.cash,
        avg_cost_before=avg_cost_before,
        avg_cost_after=portfolio.avg_cost,
        shares_traded=shares_to_sell,
    )


def execute_hold(portfolio: Portfolio) -> TradeResult:
    """Hold with no position change."""

    return TradeResult(
        action="hold",
        trade_size="none",
        size_level=0,
        cash_before=portfolio.cash,
        shares_before=int(portfolio.shares),
        shares_after=int(portfolio.shares),
        cash_after=portfolio.cash,
        avg_cost_before=portfolio.avg_cost,
        avg_cost_after=portfolio.avg_cost,
        shares_traded=0,
    )


def execute_trade(portfolio: Portfolio, action: str, trade_size: str, price: float) -> TradeResult:
    """Dispatch to buy, sell, or hold execution."""

    if action == "buy":
        return execute_buy(portfolio, trade_size, price)
    if action == "sell":
        return execute_sell(portfolio, trade_size, price)
    if action == "hold":
        return execute_hold(portfolio)
    raise ValueError(f"Unknown action: {action}")
