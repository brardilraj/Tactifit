from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
import hashlib
import os
import glob
import json as _json

try:
  import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
  pd = None  # Will fallback to in-memory data

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


class PlayerListItem(BaseModel):
  id: int
  name: str
  club: str
  league: str
  similarity_score: float


class PlayerDetail(BaseModel):
  id: int
  name: str
  club: str
  league: str
  key_metrics: Dict[str, Any]
  signing_rating: int


# Temporary in-memory data. Used if CSV-based outputs are unavailable.
_PLAYERS: List[PlayerDetail] = []  # Placeholder fallback disabled to avoid confusion


def _position_to_globs(position: Optional[str]) -> List[str]:
  """Return file glob patterns inside Team_analysis for the given position.
  Falls back to generic *.csv when position not recognized."""
  analysis_root = os.environ.get("ANALYSIS_DIR", "Team_analysis")
  if not os.path.isdir(analysis_root):
    # If Team_analysis doesn't exist, still search legacy directories generically
    return [os.path.join("Team_analysis", "**", "*.csv")]

  p = (position or "").lower()
  def patterns(names: List[str]) -> List[str]:
    return [os.path.join(analysis_root, f"**/{name}.csv") for name in names] + [
      os.path.join(analysis_root, f"**/{name}*.csv") for name in names
    ]

  # Exact filenames you provided (all CSVs) under Team_analysis
  if "goal" in p or "keeper" in p or "gk" in p:
    return patterns(["gk_clusters_results"])  # Goalkeepers
  if "striker" in p or "st" in p:
    return patterns(["striker_clusters_results"])  # Strikers
  if "wing" in p:
    return patterns(["winger_clusters_results"])  # Wingers
  if "mid" in p:
    return patterns(["midfielder_clusters_results"])  # Midfielders
  if "full" in p or ("back" in p and "center" not in p and "centre" not in p):
    return patterns(["fb_clusters_results"])  # Fullbacks
  if "center" in p or "centre" in p or "cb" in p:
    return patterns(["cb_clusters_results"])  # Center Backs

  # Unknown position -> any CSV under Team_analysis
  return [os.path.join(analysis_root, "**", "*.csv")]


def _find_latest_csv(globs: List[str]) -> Optional[str]:
  candidates: List[Tuple[float, str]] = []
  for pattern in globs:
    for path in glob.glob(pattern, recursive=True):
      try:
        mtime = os.path.getmtime(path)
        candidates.append((mtime, path))
      except OSError:
        continue
  if not candidates:
    return None
  candidates.sort(key=lambda t: t[0], reverse=True)
  return candidates[0][1]


def _players_from_csv(position: Optional[str]) -> Optional[List[PlayerDetail]]:
  if pd is None:
    return None
  search_globs = _position_to_globs(position)
  if not search_globs:
    search_globs = _position_to_globs(None)
  csv_path = _find_latest_csv(search_globs)
  if not csv_path:
    return None
  try:
    df = pd.read_csv(csv_path)
  except Exception:
    return None

  # Heuristics for expected columns
  name_col = next((c for c in df.columns if c.lower() in ("player", "player name", "name")), None)
  club_col = next((c for c in df.columns if c.lower() == "club"), None)
  league_col = next((c for c in df.columns if c.lower() in ("league", "competition")), None)
  sim_col = next((c for c in df.columns if c.lower() in ("similarity", "similarity_score", "score")), None)
  # age and value columns for filtering
  age_col = next((c for c in df.columns if "age" in c.lower()), None)
  value_col = next((c for c in df.columns if any(k in c.lower() for k in ("market value", "market_value", "value", "price"))), None)

  # attach metadata for later filtering
  df.__csv_meta__ = {  # type: ignore[attr-defined]
    "name_col": name_col,
    "club_col": club_col,
    "league_col": league_col,
    "sim_col": sim_col,
    "age_col": age_col,
    "value_col": value_col,
    "csv_path": csv_path,
  }

  if not name_col:
    # Not compatible
    return None

  players: List[PlayerDetail] = []
  for idx, row in df.iterrows():
    name = str(row.get(name_col, "")).strip()
    if not name:
      continue
    club = str(row.get(club_col, "Unknown")) if club_col else "Unknown"
    league = str(row.get(league_col, "")) if league_col else ""
    # Build key_metrics from numeric columns that look relevant
    key_metrics: Dict[str, Any] = {}
    for col in df.columns:
      if col in (name_col, club_col, league_col, sim_col):
        continue
      val = row.get(col)
      if isinstance(val, (int, float)):
        key_metrics[col] = float(val)
    # Signing rating heuristic (1-10) based on similarity if present
    signing_rating = 7
    if sim_col is not None:
      try:
        s = float(row.get(sim_col))
        if s <= 1.0:
          signing_rating = max(1, min(10, int(round(s * 10))))
        else:
          signing_rating = max(1, min(10, int(round(s))))
      except Exception:
        pass
    # Stable id from name+club+league
    stable_id = int(hashlib.md5(f"{name}|{club}|{league}".encode("utf-8")).hexdigest()[:8], 16)
    players.append(
      PlayerDetail(
        id=stable_id,
        name=name,
        club=club,
        league=league,
        key_metrics=key_metrics,
        signing_rating=signing_rating,
      )
    )
  return players or None


@app.get("/players", response_model=List[PlayerListItem])
def get_players(
  club: Optional[str] = Query(None),
  position: Optional[str] = Query(None),
  budget: Optional[int] = Query(100),
  minAge: Optional[int] = Query(18),
  maxAge: Optional[int] = Query(28),
):
  # Try CSV-backed results first
  csv_players = _players_from_csv(position)

  # If CSV exists, re-read with metadata for filtering
  if pd is not None:
    search_globs = _position_to_globs(position)
    csv_path = _find_latest_csv(search_globs)
    if csv_path:
      try:
        df = pd.read_csv(csv_path)
      except Exception:
        df = None  # type: ignore
      if df is not None:
        # Determine column names again
        name_col = next((c for c in df.columns if c.lower() in ("player", "player name", "name")), None)
        club_col = next((c for c in df.columns if c.lower() == "club"), None)
        league_col = next((c for c in df.columns if c.lower() in ("league", "competition")), None)
        sim_col = next((c for c in df.columns if c.lower() in ("similarity", "similarity_score", "score")), None)
        age_col = next((c for c in df.columns if "age" in c.lower()), None)
        value_col = next((c for c in df.columns if any(k in c.lower() for k in ("market value", "market_value", "value", "price"))), None)

        # Helper to parse value (string like "€45.0M") to millions (float)
        def parse_to_millions(v: Any) -> Optional[float]:
          try:
            if v is None or (isinstance(v, float) and pd.isna(v)):
              return None
            if isinstance(v, (int, float)):
              # assume raw currency; if too large, convert to millions
              x = float(v)
              if x > 1000:  # likely raw euros
                return x / 1_000_000.0
              return x
            s = str(v)
            s = s.replace("€", "").replace(",", "").strip()
            if s.endswith("m") or s.endswith("M"):
              s = s[:-1]
              return float(s)
            if s.endswith("k") or s.endswith("K"):
              s = s[:-1]
              return float(s) / 1000.0
            x = float(s)
            if x > 1000:
              return x / 1_000_000.0
            return x
          except Exception:
            return None

        # Apply filters
        if age_col is not None:
          try:
            if minAge is not None:
              df = df[df[age_col] >= int(minAge)]
            if maxAge is not None:
              df = df[df[age_col] <= int(maxAge)]
          except Exception:
            pass
        if value_col is not None and budget is not None:
          try:
            values_m = df[value_col].apply(parse_to_millions)
            df = df[values_m.isna() | (values_m <= float(budget))]
          except Exception:
            pass
        if club and club_col is not None:
          try:
            df = df[df[club_col].astype(str).str.contains(str(club), case=False, na=False)]
          except Exception:
            pass

        # Build list
        results: List[PlayerListItem] = []
        if name_col is None:
          # fallback to previous path
          pass
        else:
          # Use similarity if available; else default score
          for i, row in df.reset_index(drop=True).iterrows():
            score = 0.9 - (i * 0.01)
            if sim_col is not None:
              try:
                s = float(row.get(sim_col))
                score = s if s <= 1.0 else min(1.0, s / 10.0)
              except Exception:
                pass
            # Stable id based on name/club/league
            r_name = str(row.get(name_col, "")).strip()
            r_club = str(row.get(club_col, "Unknown")) if club_col else "Unknown"
            r_league = str(row.get(league_col, "")) if league_col else ""
            stable_id = int(hashlib.md5(f"{r_name}|{r_club}|{r_league}".encode("utf-8")).hexdigest()[:8], 16)
            results.append(
              PlayerListItem(
                id=stable_id,
                name=r_name,
                club=r_club,
                league=r_league,
                similarity_score=max(0.0, min(1.0, float(score))),
              )
            )
          return results

  # Fallback to in-memory
  source_players = csv_players if csv_players else _PLAYERS
  ranked: List[PlayerListItem] = []
  for i, p in enumerate(source_players):
    score = 0.9 - (i * 0.01)
    ranked.append(PlayerListItem(id=p.id, name=p.name, club=p.club, league=p.league, similarity_score=max(0.0, min(1.0, score))))
  return ranked


@app.get("/players/{player_id}", response_model=PlayerDetail)
def get_player_detail(player_id: int):
  # Search all known CSVs under Team_analysis and return the matching player by stable id
  search_globs = _position_to_globs(None)
  csv_path = _find_latest_csv(search_globs)
  # Prefer scanning all CSVs to ensure we find the exact player
  patterns = search_globs
  found: Optional[PlayerDetail] = None
  if pd is not None:
    for pattern in patterns:
      for path in glob.glob(pattern, recursive=True):
        try:
          df = pd.read_csv(path)
        except Exception:
          continue
        name_col = next((c for c in df.columns if c.lower() in ("player", "player name", "name")), None)
        club_col = next((c for c in df.columns if c.lower() == "club"), None)
        league_col = next((c for c in df.columns if c.lower() in ("league", "competition")), None)
        sim_col = next((c for c in df.columns if c.lower() in ("similarity", "similarity_score", "score")), None)
        if not name_col:
          continue
        for _, row in df.iterrows():
          r_name = str(row.get(name_col, "")).strip()
          r_club = str(row.get(club_col, "Unknown")) if club_col else "Unknown"
          r_league = str(row.get(league_col, "")) if league_col else ""
          stable_id = int(hashlib.md5(f"{r_name}|{r_club}|{r_league}".encode("utf-8")).hexdigest()[:8], 16)
          if stable_id == player_id:
            # Build key metrics (numeric columns)
            key_metrics: Dict[str, Any] = {}
            for col in df.columns:
              if col in (name_col, club_col, league_col, sim_col):
                continue
              val = row.get(col)
              if isinstance(val, (int, float)):
                key_metrics[col] = float(val)
            signing_rating = 7
            if sim_col is not None:
              try:
                s = float(row.get(sim_col))
                if s <= 1.0:
                  signing_rating = max(1, min(10, int(round(s * 10))))
                else:
                  signing_rating = max(1, min(10, int(round(s))))
              except Exception:
                pass
            found = PlayerDetail(
              id=player_id,
              name=r_name,
              club=r_club,
              league=r_league,
              key_metrics=key_metrics,
              signing_rating=signing_rating,
            )
            break
        if found:
          break
      if found:
        break
  if found:
    return found
  raise HTTPException(status_code=404, detail="Player not found")


