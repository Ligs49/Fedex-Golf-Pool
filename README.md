# FedEx Golf Pool — 2026 TOUR Championship

A small Streamlit web app for four 7-golfer fantasy teams.

## What it does

- Pulls the live PGA TOUR leaderboard for tournament `R2026060`
- Matches each golfer to Jason, Josh, Dad, or Jimmy
- Shows each golfer's current position
- Shows `NA` until the golfer has teed off
- Excludes `NA` golfers from the average
- Converts ties such as `T5` to `5` for the average calculation
- Ranks the four teams from lowest average position to highest
- Automatically refreshes every 60 seconds
- Includes a manual **Refresh Leaderboard** button

## Run locally

Open Anaconda Prompt or another terminal and move into this folder.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open the app in your browser.

## Deploy free on Streamlit Community Cloud

1. Create a free GitHub repository, for example `fedex-golf-pool`.
2. Upload these files to the root of the repository:
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Go to Streamlit Community Cloud.
4. Click **Create app**.
5. Select the GitHub repository.
6. Set the main file path to `app.py`.
7. Deploy.
8. Share the resulting `https://...streamlit.app` URL with the four players.

## Data source

PGA TOUR live leaderboard via the PGA TOUR GraphQL/frontend data service, accessed
with the open-source `pgatourPY` Python client.

Tournament:
https://www.pgatour.com/tournaments/2026/tour-championship/R2026060/overview

## Important

The PGA TOUR interface is not a guaranteed public developer API. PGA TOUR can
change its frontend API or API key. If that happens, the `pgatourPY` package or
this app may need a small update.
