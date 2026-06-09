"""
ui_components.py - Reusable Streamlit UI blocks.
"""

from html import escape
import math
import re
from typing import Dict, List, Tuple

import streamlit as st

from config import (
    COLOR_DANGER,
    COLOR_SUCCESS,
    CURRENCY,
    STARTING_CAPITAL,
    TRADE_SIZE_LABELS,
    TRADE_SIZE_MAP,
)
from scenario_engine import Scenario
from trading_logic import Portfolio


def inject_css():
    """Inject the app theme once at startup."""

    st.markdown(
        """
    <style>
      :root {
        --ink: #0A1744;
        --muted: #63708A;
        --line: rgba(47, 80, 150, 0.16);
        --panel: rgba(255, 255, 255, 0.92);
        --panel-strong: #FFFFFF;
        --dark: #071331;
        --dark-2: #120B34;
        --cyan: #13C8E8;
        --green: #14B88A;
        --amber: #E99A24;
        --red: #EF4444;
        --violet: #7848E8;
      }

      .stApp {
        background:
          radial-gradient(circle at 8% 8%, rgba(19, 200, 232, 0.18), transparent 28%),
          radial-gradient(circle at 95% 2%, rgba(120, 72, 232, 0.18), transparent 28%),
          linear-gradient(135deg, #EEF5FF 0%, #EAFBF6 46%, #FFF7ED 100%);
        color: var(--ink);
      }

      .block-container {
        max-width: 1540px;
        padding: 18px 22px 42px;
      }

      [data-testid="stHeader"] { background: transparent; }
      #MainMenu, footer { visibility: hidden; }

      .opening-stage {
        position: relative;
        overflow: hidden;
        min-height: 540px;
        border-radius: 8px;
        padding: 44px 48px;
        margin-bottom: 16px;
        color: #FFFFFF;
        background:
          linear-gradient(125deg, #061A45 0%, #082C6D 38%, #31156F 72%, #5B1C7E 100%);
        border: 1px solid rgba(142, 178, 255, 0.42);
        box-shadow: 0 28px 74px rgba(13, 28, 78, 0.26);
      }

      .opening-stage:before {
        content: "";
        position: absolute;
        inset: 0;
        background:
          repeating-linear-gradient(90deg, rgba(255,255,255,.045) 0 1px, transparent 1px 86px),
          repeating-linear-gradient(0deg, rgba(255,255,255,.030) 0 1px, transparent 1px 72px);
        opacity: .72;
        pointer-events: none;
      }

      .opening-stage:after {
        content: "";
        position: absolute;
        inset: -30% 0;
        background: linear-gradient(180deg, transparent 0%, rgba(24,225,192,.11) 50%, transparent 100%);
        animation: openingScan 7s linear infinite;
        pointer-events: none;
      }

      .opening-grid {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: minmax(0, 1.14fr) minmax(360px, .72fr);
        gap: 34px;
        align-items: stretch;
      }

      .opening-kicker {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        border: 1px solid rgba(255,255,255,.22);
        background: rgba(255,255,255,.08);
        border-radius: 999px;
        padding: 8px 13px;
        color: rgba(255,255,255,.82);
        font-size: 12px;
        font-weight: 850;
        text-transform: uppercase;
      }

      .opening-kicker span {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #18E1C0;
        box-shadow: 0 0 18px rgba(24,225,192,.9);
        animation: openingPulse 1.3s ease-in-out infinite;
      }

      .opening-logo {
        margin: 34px 0 12px;
        font-size: clamp(72px, 8.4vw, 142px);
        line-height: .86;
        letter-spacing: 0;
        color: #FFFFFF;
        font-weight: 950;
        text-shadow: 0 16px 42px rgba(0,0,0,.32);
        animation: logoRise .7s ease-out both;
      }

      .opening-subtitle {
        max-width: 760px;
        color: rgba(235, 245, 255, .82);
        font-size: 20px;
        line-height: 1.5;
        text-align: justify;
        text-align-last: left;
      }

      .opening-command-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 24px;
      }

      .opening-chip {
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,.20);
        background: rgba(255,255,255,.09);
        color: #FFFFFF;
        padding: 9px 12px;
        font-size: 13px;
        font-weight: 800;
      }

      .opening-ticker {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 2;
        height: 44px;
        overflow: hidden;
        border-top: 1px solid rgba(255,255,255,.13);
        background: rgba(2, 8, 28, .28);
      }

      .opening-ticker-track {
        display: flex;
        width: max-content;
        gap: 26px;
        align-items: center;
        height: 44px;
        white-space: nowrap;
        animation: tickerMove 22s linear infinite;
      }

      .opening-ticker-track span {
        color: rgba(255,255,255,.88);
        font-size: 12px;
        font-weight: 850;
      }

      .opening-ticker-track b { color: #18E1C0; }
      .opening-ticker-track i { color: #FB7185; font-style: normal; }

      .opening-candles {
        position: absolute;
        left: 5%;
        right: 42%;
        bottom: 60px;
        z-index: 0;
        display: grid;
        grid-template-columns: repeat(22, 1fr);
        gap: 12px;
        height: 154px;
        align-items: end;
        opacity: .34;
      }

      .opening-candle {
        position: relative;
        width: 8px;
        justify-self: center;
        border-radius: 999px;
        background: #18E1C0;
        animation: candleBeat 2.6s ease-in-out infinite;
      }

      .opening-candle:before {
        content: "";
        position: absolute;
        left: 50%;
        top: -22px;
        bottom: -22px;
        width: 1px;
        transform: translateX(-50%);
        background: currentColor;
        opacity: .8;
      }

      .opening-candle.down { background: #FB7185; color: #FB7185; }
      .opening-candle.up { color: #18E1C0; }

      .opening-console {
        align-self: center;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,.18);
        background: rgba(4, 12, 34, .58);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 24px 58px rgba(0,0,0,.28);
        backdrop-filter: blur(16px);
        padding: 22px;
      }

      .console-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 18px;
      }

      .console-title {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 950;
        text-transform: uppercase;
      }

      .console-status {
        color: #18E1C0;
        font-size: 12px;
        font-weight: 900;
      }

      .console-bars {
        display: grid;
        gap: 11px;
      }

      .console-bar {
        display: grid;
        grid-template-columns: 104px 1fr 48px;
        gap: 12px;
        align-items: center;
        color: rgba(255,255,255,.78);
        font-size: 12px;
        font-weight: 800;
      }

      .console-meter {
        height: 8px;
        border-radius: 999px;
        background: rgba(255,255,255,.12);
        overflow: hidden;
      }

      .console-meter span {
        display: block;
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #18E1C0, #38BDF8);
      }

      .opening-panels {
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(360px, .74fr);
        gap: 18px;
        margin-top: 16px;
      }

      .opening-rules-card, .opening-start-card {
        border-radius: 8px;
        border: 1px solid rgba(47, 80, 150, 0.16);
        background: rgba(255,255,255,.94);
        box-shadow: 0 20px 48px rgba(21, 45, 92, 0.12);
        padding: 22px 24px;
      }

      .opening-rules-title, .opening-start-title {
        color: #0B1E55;
        font-size: 18px;
        font-weight: 950;
        text-transform: uppercase;
        margin-bottom: 14px;
      }

      .opening-rule-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 16px;
      }

      .opening-rule-item {
        border-radius: 8px;
        background: #F5F8FF;
        border: 1px solid #DDE8FF;
        padding: 13px 14px;
        min-height: 116px;
      }

      .opening-rule-item b {
        display: block;
        color: #0B67D4;
        font-size: 12px;
        text-transform: uppercase;
        margin-bottom: 8px;
      }

      .opening-rule-item span {
        display: block;
        color: #14213F;
        font-size: 14px;
        line-height: 1.48;
        text-align: justify;
        text-align-last: left;
      }

      .opening-start-card div[data-testid="stTextInput"] label {
        color: #0B1E55;
        font-weight: 850;
      }

      .opening-start-card input {
        min-height: 54px;
        border-radius: 8px;
      }

      .opening-start-card div.stButton > button {
        min-height: 56px;
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 0;
      }

      .opening-start-copy {
        color: #14213F;
        font-size: 15px;
        line-height: 1.55;
        margin-bottom: 16px;
        text-align: justify;
        text-align-last: left;
      }

      .top-hero, .round-banner, .chart-shell, .movement-shell {
        border: 1px solid rgba(142, 178, 255, 0.34);
        box-shadow: 0 22px 60px rgba(16, 35, 91, 0.16);
      }

      .top-hero {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        padding: 30px 34px;
        margin-bottom: 16px;
        color: #FFFFFF;
        background:
          linear-gradient(110deg, rgba(5, 24, 74, 0.96) 0%, rgba(8, 35, 105, 0.93) 46%, rgba(74, 20, 120, 0.92) 100%);
      }

      .top-hero:before, .round-banner:before {
        content: "";
        position: absolute;
        inset: 0;
        background:
          linear-gradient(90deg, transparent 0%, rgba(255,255,255,.08) 50%, transparent 100%),
          repeating-linear-gradient(90deg, rgba(255,255,255,.04) 0 1px, transparent 1px 72px);
        opacity: 0.42;
        pointer-events: none;
      }

      .top-hero h1 {
        position: relative;
        margin: 0;
        font-size: 34px;
        line-height: 1.08;
        color: #FFFFFF;
        letter-spacing: 0;
      }

      .top-hero p {
        position: relative;
        margin: 8px 0 0;
        color: rgba(255,255,255,.78);
        font-size: 15px;
        text-align: justify;
        text-align-last: left;
      }

      .round-banner {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        padding: 22px 26px;
        margin-bottom: 14px;
        color: #FFFFFF;
        background:
          linear-gradient(110deg, #082463 0%, #0A3A83 42%, #431572 100%);
      }

      .round-banner-grid {
        position: relative;
        display: grid;
        grid-template-columns: 1fr 230px;
        gap: 18px;
        align-items: center;
      }

      .round-title {
        font-size: 31px;
        font-weight: 800;
        line-height: 1.1;
        color: #FFFFFF;
      }

      .round-sub {
        margin-top: 7px;
        color: rgba(255,255,255,.78);
        font-size: 15px;
        text-align: justify;
        text-align-last: left;
      }

      .progress-label {
        color: rgba(255,255,255,.78);
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .progress-num {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 800;
        margin: 2px 0 8px;
      }

      .progress-track {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: rgba(255,255,255,.13);
        overflow: hidden;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.18);
      }

      .progress-fill {
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #18E1C0, #36A3FF);
      }

      .info-card {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        border: 1px solid var(--line);
        background: var(--panel);
        padding: 18px 20px;
        margin-bottom: 10px;
        box-shadow: 0 16px 34px rgba(26, 48, 96, 0.10);
      }

      .info-card:after {
        content: "";
        position: absolute;
        right: -40px;
        bottom: -60px;
        width: 180px;
        height: 150px;
        background: linear-gradient(180deg, rgba(19, 200, 232, .12), rgba(120, 72, 232, .08));
        transform: skewX(-14deg);
        pointer-events: none;
      }

      .card-row {
        display: grid;
        grid-template-columns: 52px 1fr;
        gap: 16px;
        align-items: start;
        position: relative;
        z-index: 1;
      }

      .icon-box {
        width: 52px;
        height: 52px;
        border-radius: 8px;
        display: grid;
        place-items: center;
        font-weight: 900;
        color: white;
        letter-spacing: 0;
        box-shadow: 0 10px 20px rgba(18, 58, 123, .18);
      }

      .icon-price { background: linear-gradient(135deg, #0DBE7D, #15A465); }
      .icon-context { background: linear-gradient(135deg, #1778FF, #13C8E8); }
      .icon-news { background: linear-gradient(135deg, #7C3AED, #B04CF5); }
      .icon-fund { background: linear-gradient(135deg, #0BA596, #11B981); }
      .icon-crowd { background: linear-gradient(135deg, #F59E0B, #EF4444); }

      .eyebrow {
        margin: 0 0 7px;
        color: #0B67D4;
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0;
      }

      .body-copy {
        color: #14213F;
        font-size: 15px;
        line-height: 1.58;
        text-align: justify;
        text-align-last: left;
        hyphens: auto;
      }

      .body-copy p {
        margin: 0 0 11px;
        text-align: justify;
        text-align-last: left;
      }
      .body-copy p:last-child { margin-bottom: 0; }
      .body-copy strong { color: #3321C8; font-weight: 800; }

      .price-num {
        font-size: 48px;
        line-height: 1;
        color: #101B4E;
        font-weight: 900;
      }

      .price-unit {
        color: var(--muted);
        font-size: 18px;
        font-weight: 850;
        margin-left: 6px;
      }

      .chart-shell {
        border-radius: 8px;
        background: #FFFFFF;
        border: 1px solid rgba(17, 24, 39, .10);
        padding: 4px 6px 0;
        margin-bottom: 10px;
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
      }

      .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin: 10px 0;
      }

      .metric-tile {
        position: relative;
        border-radius: 8px;
        border: 1px solid rgba(32, 76, 140, .15);
        background: rgba(255,255,255,.88);
        padding: 15px 16px;
        min-height: 106px;
        box-shadow: 0 14px 28px rgba(30, 52, 92, 0.10);
      }

      .metric-tile.primary-metric {
        min-height: 126px;
      }

      .metric-label {
        color: var(--muted);
        font-size: 13px;
        font-weight: 750;
        margin-bottom: 9px;
      }

      .metric-value {
        color: #0B1E55;
        font-size: 25px;
        line-height: 1.08;
        font-weight: 900;
        word-break: break-word;
      }

      .metric-subline {
        margin-top: 11px;
        padding-top: 9px;
        border-top: 1px solid rgba(32, 76, 140, .12);
        color: var(--muted);
        font-size: 12px;
        font-weight: 800;
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
      }

      .metric-subline b {
        font-size: 16px;
        font-weight: 900;
      }

      .result-metric-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin: 10px 0 14px;
      }

      .result-metric-grid .metric-tile {
        min-height: 92px;
        padding: 14px 16px;
      }

      .result-metric-grid .metric-label {
        margin-bottom: 8px;
        font-size: 12px;
      }

      .result-metric-grid .metric-value {
        font-size: 22px;
      }

      .metric-info {
        position: absolute;
        top: 12px;
        right: 12px;
        width: 19px;
        height: 19px;
        border-radius: 999px;
        border: 1px solid rgba(32, 76, 140, .22);
        background: #F8FAFC;
        color: #52617A;
        display: grid;
        place-items: center;
        font-size: 12px;
        line-height: 1;
        font-weight: 900;
        cursor: help;
      }

      .metric-info:after {
        content: attr(data-tip);
        position: absolute;
        top: 25px;
        right: 0;
        z-index: 20;
        width: 270px;
        padding: 10px 12px;
        border-radius: 8px;
        background: #111827;
        color: #FFFFFF;
        font-size: 12px;
        line-height: 1.45;
        font-weight: 650;
        text-align: left;
        opacity: 0;
        pointer-events: none;
        transform: translateY(-4px);
        transition: opacity .14s ease, transform .14s ease;
        box-shadow: 0 16px 36px rgba(15, 23, 42, .22);
      }

      .metric-info:hover:after {
        opacity: 1;
        transform: translateY(0);
      }

      .decision-shell, .quiz-shell, .outcome-shell, .result-card {
        border-radius: 8px;
        border: 1px solid rgba(47, 80, 150, 0.16);
        background: rgba(255,255,255,.92);
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 18px 38px rgba(22, 45, 92, 0.12);
      }

      .quiz-shell {
        background: #FFFFFF;
        border-color: rgba(15, 23, 42, 0.14);
      }

      .quiz-shell [data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 0;
      }

      div[data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(15, 23, 42, 0.14) !important;
        border-radius: 8px !important;
        padding: 18px 20px !important;
        box-shadow: 0 18px 38px rgba(22, 45, 92, 0.10) !important;
      }

      div[data-testid="stForm"] > div {
        background: #FFFFFF !important;
      }

      div[data-testid="stForm"],
      div[data-testid="stForm"] *,
      div[data-testid="stForm"] label,
      div[data-testid="stForm"] p,
      div[data-testid="stForm"] span {
        color: #14213F !important;
        opacity: 1 !important;
      }

      div[data-testid="stForm"] [data-testid="stMarkdownContainer"] p {
        color: #14213F !important;
        font-weight: 650;
      }

      div[data-testid="stForm"] [role="radiogroup"] label {
        color: #14213F !important;
      }

      div[data-testid="stFormSubmitButton"] button {
        background: #0B1E55 !important;
        border: 1px solid #0B1E55 !important;
        color: #FFFFFF !important;
        box-shadow: 0 12px 24px rgba(11, 30, 85, 0.18) !important;
      }

      div[data-testid="stFormSubmitButton"] button *,
      div[data-testid="stFormSubmitButton"] button p {
        color: #FFFFFF !important;
      }

      div[data-testid="stFormSubmitButton"] button:hover {
        background: #132B74 !important;
        border-color: #132B74 !important;
        color: #FFFFFF !important;
      }

      .section-title {
        color: #14206A;
        font-size: 16px;
        font-weight: 900;
        text-transform: uppercase;
        margin-bottom: 12px;
        letter-spacing: 0;
      }

      .decision-summary {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-bottom: 14px;
      }

      .summary-pill {
        border-radius: 8px;
        background: #F4F7FF;
        border: 1px solid #DDE8FF;
        padding: 10px 12px;
      }

      .summary-pill span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        font-weight: 750;
      }

      .summary-pill b {
        display: block;
        margin-top: 3px;
        color: #0B1E55;
        font-size: 16px;
      }

      div.stButton > button {
        border-radius: 8px;
        border: 0;
        background: linear-gradient(90deg, #D80A5E 0%, #FF4B1F 100%);
        color: white;
        font-weight: 850;
        min-height: 48px;
        box-shadow: 0 12px 24px rgba(216, 10, 94, 0.25);
      }

      div.stButton > button:hover {
        border: 0;
        color: white;
        filter: brightness(1.04);
      }

      .stRadio, .stSelectSlider, .stSelectbox {
        color: #14213F;
      }

      .outcome-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 14px;
      }

      .outcome-metric {
        border-radius: 8px;
        background: #F6F8FF;
        border: 1px solid #E0E8FF;
        padding: 14px 16px;
      }

      .outcome-metric span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        font-weight: 750;
        margin-bottom: 5px;
      }

      .outcome-metric b {
        display: block;
        color: #0B1E55;
        font-size: 22px;
      }

      .callout {
        border-left: 4px solid #13C8E8;
        background: #F4FBFF;
        border-radius: 8px;
        padding: 12px 14px;
        color: #14213F;
        font-size: 15px;
        line-height: 1.55;
        text-align: justify;
        text-align-last: left;
        hyphens: auto;
      }

      .movement-shell {
        border-radius: 8px;
        background:
          linear-gradient(135deg, #061431 0%, #071B45 48%, #160B36 100%);
        color: #FFFFFF;
        padding: 18px 20px;
        margin-bottom: 14px;
      }

      .movement-title {
        font-size: 23px;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 4px;
      }

      .movement-sub {
        color: rgba(255,255,255,.72);
        font-size: 14px;
        text-align: justify;
        text-align-last: left;
        hyphens: auto;
      }

      .quiz-shell div[data-testid="stMarkdownContainer"] p,
      .quiz-shell label,
      .outcome-shell .callout p,
      .result-card li {
        text-align: justify;
        text-align-last: left;
        hyphens: auto;
      }

      .tier-chip {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 11px;
        font-size: 12px;
        font-weight: 800;
      }

      @media (max-width: 920px) {
        .opening-grid, .opening-panels, .round-banner-grid, .metric-grid, .decision-summary, .outcome-grid {
          grid-template-columns: 1fr;
        }
        .result-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .opening-stage { padding: 30px 24px 68px; min-height: auto; }
        .opening-candles { right: 5%; opacity: .20; }
        .opening-logo { font-size: 56px; }
        .opening-subtitle { font-size: 17px; }
        .opening-rule-grid { grid-template-columns: 1fr; }
        .price-num { font-size: 38px; }
        .round-title { font-size: 25px; }
      }

      @media (max-width: 560px) {
        .result-metric-grid { grid-template-columns: 1fr; }
      }

      @keyframes openingScan {
        0% { transform: translateY(-24%); }
        100% { transform: translateY(24%); }
      }

      @keyframes openingPulse {
        0%, 100% { transform: scale(.85); opacity: .78; }
        50% { transform: scale(1.24); opacity: 1; }
      }

      @keyframes logoRise {
        0% { transform: translateY(18px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
      }

      @keyframes tickerMove {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
      }

      @keyframes candleBeat {
        0%, 100% { transform: scaleY(.92); opacity: .68; }
        50% { transform: scaleY(1.12); opacity: 1; }
      }
      /* Ép chữ của Radio (Buy/Hold) và Slider (Trade size) thành màu tối */
        div[data-testid="stRadio"] label p, 
        div[data-testid="stSlider"] label p,
        div[data-testid="stSlider"] div {
            color: #1e1e1e !important;
            font-weight: 600 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="top-hero">
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_round_banner(round_num: int, total_rounds: int, hint: str = ""):
    progress = round_num / total_rounds
    st.markdown(
        f"""
        <div class="round-banner">
          <div class="round-banner-grid">
            <div>
              <div class="round-title">Week {round_num}/{total_rounds}</div>
              <div class="round-sub">{escape(hint)}</div>
            </div>
            <div>
              <div class="progress-label">Progress</div>
              <div class="progress-num">{progress:.0%}</div>
              <div class="progress-track">
                <div class="progress-fill" style="width:{progress:.0%};"></div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_shell_start():
    st.markdown('<div class="chart-shell">', unsafe_allow_html=True)


def render_shell_end():
    st.markdown("</div>", unsafe_allow_html=True)


def render_price_card(price: float):
    st.markdown(
        f"""
        <div class="info-card">
          <div class="card-row">
            <div class="icon-box icon-price">$</div>
            <div>
              <div class="eyebrow">Current Price</div>
              <div class="price-num">{price:,.2f}<span class="price-unit">{CURRENCY}</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_context(scenario: Scenario):
    _render_text_card("Market Context", "MKT", "icon-context", scenario.market_context)


def render_news_panel(scenario: Scenario):
    _render_text_card("Market News", "NEWS", "icon-news", scenario.news_text)


def render_fundamentals_panel(scenario: Scenario):
    _render_text_card("Key Fundamentals", "DATA", "icon-fund", scenario.fundamentals_text)


def render_crowd_panel(scenario: Scenario):
    _render_text_card("Forum Sentiment", "SOC", "icon-crowd", scenario.crowd_text)


def _render_text_card(title: str, icon: str, icon_class: str, text: str):
    html = _paragraphs_to_html(text)
    st.markdown(
        f"""
        <div class="info-card">
          <div class="card-row">
            <div class="icon-box {icon_class}">{escape(icon)}</div>
            <div>
              <div class="eyebrow">{escape(title)}</div>
              <div class="body-copy">{html}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_portfolio_panel(portfolio: Portfolio, price_now: float):
    portfolio_value = portfolio.value(price_now)
    stock_value = portfolio.shares * price_now
    total_cost = portfolio.shares * portfolio.avg_cost
    portfolio_return = (
        (portfolio_value - STARTING_CAPITAL) / STARTING_CAPITAL * 100
        if STARTING_CAPITAL else 0.0
    )
    unrealized_return = (
        (price_now - portfolio.avg_cost) / portfolio.avg_cost * 100
        if portfolio.shares > 0 and portfolio.avg_cost > 0 else 0.0
    )
    portfolio_return_text = f"{portfolio_return:+.2f}%"
    unrealized_return_text = f"{unrealized_return:+.2f}%"
    portfolio_return_color = COLOR_SUCCESS if portfolio_return >= 0 else COLOR_DANGER
    unrealized_return_color = COLOR_SUCCESS if unrealized_return >= 0 else COLOR_DANGER

    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-tile primary-metric">
            <span class="metric-info" data-tip="Cash is the uninvested money left after completed buy and sell orders.">i</span>
            <div class="metric-label">Cash</div>
            <div class="metric-value">{portfolio.cash:,.0f} {CURRENCY}</div>
          </div>
          <div class="metric-tile primary-metric">
            <span class="metric-info" data-tip="Stock value = shares held x current price. Total cost = shares held x average cost. Unrealized return = (current price - average cost) / average cost.">i</span>
            <div class="metric-label">Stock Value / Total Cost</div>
            <div class="metric-value">{stock_value:,.0f} {CURRENCY}</div>
            <div class="metric-subline">
              <span>{int(portfolio.shares):,} shares | total cost {total_cost:,.0f} {CURRENCY}</span>
              <b style="color:{unrealized_return_color};">{unrealized_return_text}</b>
            </div>
          </div>
          <div class="metric-tile primary-metric">
            <span class="metric-info" data-tip="Portfolio value = cash + stock value. Portfolio return = (portfolio value - starting capital) / starting capital.">i</span>
            <div class="metric-label">Portfolio Value</div>
            <div class="metric-value">{portfolio_value:,.0f} {CURRENCY}</div>
            <div class="metric-subline">
              <span>Portfolio return</span>
              <b style="color:{portfolio_return_color};">{portfolio_return_text}</b>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_panel(portfolio: Portfolio, price_now: float) -> dict:
    """Return pending decision after the player proceeds to questions."""

    st.markdown('<div class="decision-shell"><div class="section-title">Your Decision</div>', unsafe_allow_html=True)
    can_buy_one_share = price_now > 0 and portfolio.cash >= price_now
    action_options = []
    if can_buy_one_share:
        action_options.append("buy")
    if portfolio.shares > 0:
        action_options.append("sell")
    action_options.append("hold")
    action = st.radio(
        "Action",
        options=action_options,
        format_func=lambda x: {"buy": "BUY", "sell": "SELL", "hold": "HOLD"}[x],
        horizontal=True,
        label_visibility="collapsed",
        key=f"action_radio_{st.session_state.get('current_round', 0)}",
    )
    if not can_buy_one_share:
        st.caption(f"Buy is unavailable because cash is below the current price of 1 share ({price_now:,.2f} {CURRENCY}).")
    if portfolio.shares <= 0:
        st.caption("Sell is unavailable because you do not hold any shares.")

    trade_size = "none"
    if action in ("buy", "sell"):
        if action == "sell" and portfolio.shares == 0:
            st.warning("You have no shares to sell. Choose Buy or Hold.")
            st.markdown("</div>", unsafe_allow_html=True)
            return {"action": None}
        if action == "buy" and not can_buy_one_share:
            st.warning("You do not have enough cash to buy 1 share. Choose Sell or Hold.")
            st.markdown("</div>", unsafe_allow_html=True)
            return {"action": None}
        size_options = ["small", "medium", "high", "all_in"]
        if action == "buy":
            size_options = [
                size
                for size in size_options
                if math.floor(portfolio.cash * TRADE_SIZE_MAP[size][1] / price_now) >= 1
            ]
        if action == "sell":
            size_options = [
                size
                for size in size_options
                if size == "all_in" or math.floor(portfolio.shares * TRADE_SIZE_MAP[size][1]) >= 1
            ]
        if not size_options:
            st.warning("No valid trade size is available for this action. Choose another action.")
            st.markdown("</div>", unsafe_allow_html=True)
            return {"action": None}
        trade_size = st.select_slider(
            "Trade size",
            options=size_options,
            value="medium" if "medium" in size_options else size_options[-1],
            format_func=lambda x: TRADE_SIZE_LABELS[x],
            key=f"size_slider_{st.session_state.get('current_round', 0)}",
        )

    submit = st.button(
        "Continue to Questions",
        type="primary",
        use_container_width=True,
        key=f"submit_{st.session_state.get('current_round', 0)}",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    if submit:
        return {"action": action, "trade_size": trade_size}
    return {"action": None}


def render_quiz_panel(scenario: Scenario, decision: Dict) -> Dict:
    """Render 3 ending questions and return validation state."""

    st.markdown(
        f"""
        <div class="quiz-shell">
          <div class="section-title">Decision Checkpoint</div>
          <div class="decision-summary">
            <div class="summary-pill"><span>Action</span><b>{escape(decision.get('action', '').upper())}</b></div>
            <div class="summary-pill"><span>Trade size</span><b>{escape(_size_label(decision.get('trade_size', 'none')))}</b></div>
            <div class="summary-pill"><span>Decision price</span><b>{scenario.price_now:,.2f} {CURRENCY}</b></div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    questions = _scenario_questions(scenario)
    if not questions:
        st.markdown("</div>", unsafe_allow_html=True)
        return {"submitted": True, "all_correct": True}

    with st.form(f"quiz_form_{scenario.round}", clear_on_submit=False):
        selections = {}
        for idx, (question, options, correct) in enumerate(questions, start=1):
            labels = [f"{key}. {label}" for key, label in options]
            answer = st.radio(
                question,
                options=labels,
                index=None,
                key=f"quiz_{scenario.round}_{idx}",
            )
            selections[idx] = (answer[0] if answer else None, correct)
        submitted = st.form_submit_button("Confirm Decision", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    if not submitted:
        return {"submitted": False, "all_correct": False}

    missing = [idx for idx, (answer, _) in selections.items() if answer is None]
    incorrect = [
        idx for idx, (answer, correct) in selections.items()
        if answer is not None and answer != correct
    ]
    return {
        "submitted": True,
        "all_correct": not missing and not incorrect,
        "missing": missing,
        "incorrect": incorrect,
    }


def render_movement_status(scenario: Scenario):
    st.markdown(
        f"""
        <div class="movement-shell">
          <div class="movement-title">Market movement in progress</div>
          <div class="movement-sub">
            The simulated market is walking from {scenario.price_now:,.2f} {CURRENCY} toward the scenario target.
            Outcome and P&L are hidden until the move completes.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_outcome(
    price_before: float,
    price_after: float,
    portfolio_change: float,
    outcome_text: str = "",
):
    price_pct = (price_after - price_before) / price_before * 100
    price_color = COLOR_SUCCESS if price_pct >= 0 else COLOR_DANGER
    pnl_color = COLOR_SUCCESS if portfolio_change >= 0 else COLOR_DANGER
    body = _paragraphs_to_html(outcome_text)

    st.markdown(
        f"""
        <div class="outcome-shell">
          <div class="section-title">Outcome Revealed</div>
          <div class="outcome-grid">
            <div class="outcome-metric">
              <span>Price move</span>
              <b style="color:{price_color};">{price_before:.2f} to {price_after:.2f} {CURRENCY}</b>
            </div>
            <div class="outcome-metric">
              <span>Stock return</span>
              <b style="color:{price_color};">{price_pct:+.2f}%</b>
            </div>
            <div class="outcome-metric">
              <span>Week P&L</span>
              <b style="color:{pnl_color};">{portfolio_change:+,.0f} {CURRENCY}</b>
            </div>
          </div>
          <div class="callout">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


TIER_STYLE = {
    "None": ("#F1F5F9", "#475569"),
    "Mild": ("#DCFCE7", "#166534"),
    "Moderate": ("#FEF3C7", "#92400E"),
    "Strong": ("#FFEDD5", "#9A3412"),
    "Very Strong": ("#FEE2E2", "#991B1B"),
}


def render_bias_card(bias_name: str, info: dict, suggestion: str, definition: str = ""):
    bg, fg = TIER_STYLE.get(info["tier"], ("#E5E7EB", "#374151"))
    rules_html = ""
    for fire in info.get("rules", []):
        rnd, _cluster_id, points, msg = fire
        rnd_label = f"Week {rnd}" if isinstance(rnd, int) else "Game"
        rules_html += (
            "<li style='margin-bottom:7px;text-align:justify;text-align-last:left;'>"
            f"<span style='color:#111827;font-weight:800;'>{escape(rnd_label)}</span> "
            f"<b style='color:#000000;'>+{points}</b> "
            f"<span style='color:#24324A;'>- {escape(msg)}</span>"
            "</li>"
        )
    if not rules_html:
        rules_html = "<li style='color:#24324A;'>No evidence cluster fired for this bias.</li>"

    definition_html = ""
    if definition:
        definition_html = f"""
          <div style="margin-top:12px;background:#F8FAFC;border:1px solid #E2E8F0;
                      border-radius:8px;padding:11px 12px;color:#111827;font-size:13px;
                      line-height:1.48;text-align:justify;text-align-last:left;hyphens:auto;">
            <b style="color:#000000;">Definition:</b> {escape(definition)}
          </div>
        """

    st.markdown(
        f"""
        <div class="result-card">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
            <div style="font-size:19px;font-weight:900;color:#0B1E55;">{escape(bias_name)}</div>
            <div>
              <span class="tier-chip" style="background:{bg};color:{fg};">{escape(info['tier'])}</span>
              <span style="margin-left:8px;color:#64748B;font-size:13px;">Score <b style="color:#0B1E55;">{info['score']}</b></span>
            </div>
          </div>
          {definition_html}
          <div style="margin-top:12px;color:#14213F;font-size:14px;">
            <div style="font-size:12px;font-weight:900;text-transform:uppercase;color:#000000;
                        margin-bottom:8px;">Evidence</div>
            <ul style="margin:0;padding-left:20px;">{rules_html}</ul>
          </div>
          <div class="callout" style="margin-top:12px;border-left-color:#7848E8;">
            <b>How to avoid:</b> {escape(suggestion)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _paragraphs_to_html(text: str) -> str:
    if not text:
        return ""
    safe = escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    parts = [p.strip() for p in safe.split("\n\n") if p.strip()]
    return "\n".join(f"<p>{p}</p>" for p in parts)


def _size_label(size: str) -> str:
    if size == "none":
        return "None"
    return TRADE_SIZE_LABELS.get(size, size)


def _scenario_questions(scenario: Scenario) -> List[Tuple[str, List[Tuple[str, str]], str]]:
    raw = [
        (scenario.question_1, scenario.q1_options, scenario.q1_correct),
        (scenario.question_2, scenario.q2_options, scenario.q2_correct),
        (scenario.question_3, scenario.q3_options, scenario.q3_correct),
    ]
    questions = []
    for question, options_text, correct in raw:
        options = _parse_options(options_text)
        if question and options and correct:
            questions.append((question, options, correct.upper()))
    return questions


def _parse_options(options_text: str) -> List[Tuple[str, str]]:
    options = []
    for line in (options_text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^([A-C])\.\s*(.+)$", line)
        if match:
            options.append((match.group(1), match.group(2).strip()))
    return options
