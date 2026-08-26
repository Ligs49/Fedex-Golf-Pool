import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pgatourpy as pga


# -----------------------------
# APP CONFIGURATION
# -----------------------------
TOURNAMENT_ID = "R2026060"
TOURNAMENT_NAME = "2026 TOUR Championship"
REFRESH_MS = 60_000

TEAMS = {
    "Jason": [
        "Scottie Scheffler",
        "Cameron Young",
        "Collin Morikawa",
        "Akshay Bhatia",
        "Justin Rose",
        "Hideki Matsuyama",
        "Alex Smalley",
    ],
    "Josh": [
        "Wyndham Clark",
        "Sam Burns",
        "Patrick Cantlay",
        "Russell Henley",
        "Gary Woodland",
        "Tom Kim",
        "Robert MacIntyre",
    ],
    "Dad": [
        "Xander Schauffele",
        "Viktor Hovland",
        "Matt Fitzpatrick",
        "Tommy Fleetwood",
        "J.J. Spaun",
        "Min Woo Lee",
        "Alex Fitzpatrick",
    ],
    "Jimmy": [
        "Rory McIlroy",
        "Chris Gotterup",
        "Ludvig Åberg",
        "Si Woo Kim",
        "Jacob Bridgeman",
        "Ryan Gerard",
        "Kristoffer Reitan",
    ],
}


# -----------------------------
# HELPERS
# -----------------------------
def normalize_name(name: str) -> str:
    """Normalize names so punctuation/accents do not prevent a roster match."""
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def numeric_position(position):
    """
    Convert PGA display positions such as '1', 'T5', or '=5' into a number.
    Non-playing/non-position values return None.
    """
    if position is None or (isinstance(position, float) and pd.isna(position)):
        return None

    text = str(position).strip().upper()
    if text in {"", "-", "--", "NA", "N/A"}:
        return None

    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def has_teed_off(row: pd.Series) -> bool:
    """
    A player is excluded from the average while PGA TOUR reports NOT_STARTED.
    Includes defensive fallbacks in case the upstream field changes.
    """
    state = str(row.get("player_state", "") or "").strip().upper()

    if state == "NOT_STARTED":
        return False

    if state in {"ACTIVE", "COMPLETE", "CUT", "WITHDRAWN", "WD", "DQ"}:
        return True

    # Defensive fallback: evidence of live/finished play.
    thru = str(row.get("thru", "") or "").strip().upper()
    current_round = row.get("current_round")
    round_1 = row.get("round_1")

    if thru not in {"", "-", "--", "NA", "N/A"}:
        return True
    if pd.notna(current_round):
        try:
            if float(current_round) > 0:
                return True
        except (TypeError, ValueError):
            pass
    if pd.notna(round_1) and str(round_1).strip() not in {"", "-", "--"}:
        return True

    return False


def fetch_leaderboard() -> pd.DataFrame:
    """Fetch the live TOUR Championship leaderboard from PGA TOUR data."""
    leaderboard = pga.pga_leaderboard(TOURNAMENT_ID)
    if leaderboard is None or leaderboard.empty:
        raise RuntimeError("PGA TOUR returned an empty leaderboard.")
    return leaderboard


def build_team_results(leaderboard: pd.DataFrame):
    """Match roster golfers to the live leaderboard and rank the four teams."""
    lb = leaderboard.copy()
    lb["_norm_name"] = lb["display_name"].map(normalize_name)
    lookup = {row["_norm_name"]: row for _, row in lb.iterrows()}

    team_results = []

    for team_name, golfers in TEAMS.items():
        golfer_rows = []
        values_for_average = []

        for golfer in golfers:
            row = lookup.get(normalize_name(golfer))

            if row is None:
                golfer_rows.append(
                    {
                        "golfer": golfer,
                        "display_position": "NA",
                        "numeric_position": None,
                        "status": "Not found in PGA leaderboard",
                    }
                )
                continue

            started = has_teed_off(row)
            pos_display = str(row.get("position", "") or "").strip()
            pos_numeric = numeric_position(pos_display) if started else None

            if not started or pos_numeric is None:
                display = "NA"
            else:
                display = pos_display
                values_for_average.append(pos_numeric)

            golfer_rows.append(
                {
                    "golfer": golfer,
                    "display_position": display,
                    "numeric_position": pos_numeric,
                    "status": str(row.get("player_state", "") or ""),
                }
            )

        average = (
            sum(values_for_average) / len(values_for_average)
            if values_for_average
            else None
        )

        team_results.append(
            {
                "team": team_name,
                "average": average,
                "players_counted": len(values_for_average),
                "golfers": golfer_rows,
            }
        )

    # Lower average standing is better. Teams with no starters remain unranked/tied at bottom.
    team_results.sort(
        key=lambda x: (
            x["average"] is None,
            x["average"] if x["average"] is not None else float("inf"),
            x["team"],
        )
    )

    for rank, result in enumerate(team_results, start=1):
        result["rank"] = rank

    return team_results


# -----------------------------
# PAGE
# -----------------------------
st.set_page_config(
    page_title="FedEx Golf Pool",
    page_icon="⛳",
    layout="centered",
)

st_autorefresh(interval=REFRESH_MS, limit=None, key="fedex_pool_60s_refresh")

st.title("⛳ FedEx Golf Pool")
st.caption(f"{TOURNAMENT_NAME} • Live team standings • Updates every 60 seconds")

if st.button("🔄 Refresh Leaderboard", type="primary", use_container_width=True):
    # Clicking any Streamlit button reruns the script immediately.
    pass

try:
    leaderboard = fetch_leaderboard()
    results = build_team_results(leaderboard)

    now_et = datetime.now(ZoneInfo("America/New_York"))
    st.caption(f"Last updated: {now_et:%a %b %d, %Y • %I:%M:%S %p ET}")

    st.divider()

    for result in results:
        avg_text = (
            f"{result['average']:.2f}"
            if result["average"] is not None
            else "NA"
        )

        st.subheader(
            f"{result['rank']}. {result['team']} — Average Position: {avg_text}"
        )
        st.caption(
            f"{result['players_counted']} of 7 golfers currently included in the average"
        )

        rows = []
        for golfer in result["golfers"]:
            rows.append(
                {
                    "Golfer": golfer["golfer"],
                    "Current Position": golfer["display_position"],
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Golfer": st.column_config.TextColumn("Golfer"),
                "Current Position": st.column_config.TextColumn(
                    "Current Position", width="small"
                ),
            },
        )

        st.divider()

    st.caption(
        "Scoring rule: a golfer listed as NOT_STARTED/NA is excluded from the "
        "team average. For a tied position such as T5, the average uses 5."
    )
    st.caption(
        "Data source: PGA TOUR live leaderboard. This app uses PGA TOUR's "
        "frontend data service through the open-source pgatourPY client."
    )

except Exception as exc:
    st.error("The PGA TOUR leaderboard could not be loaded.")
    st.write(
        "This can happen before the live leaderboard is initialized, during a "
        "temporary PGA TOUR outage, or if PGA TOUR changes its data service."
    )
    with st.expander("Technical details"):
        st.code(str(exc))
