const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type PlayerListItem = {
  id: number;
  name: string;
  club: string;
  league: string;
  similarity_score: number;
};

export type PlayerDetail = {
  id: number;
  name: string;
  club: string;
  league: string;
  key_metrics: Record<string, unknown>;
  signing_rating: number;
};

export async function fetchPlayers(params: {
  position?: string | null;
  minAge?: string | null;
  maxAge?: string | null;
  budget?: string | null;
  club?: string | null;
}): Promise<PlayerListItem[]> {
  const url = new URL("/players", API_URL);
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== "") url.searchParams.set(k, String(v));
  });
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch players: ${res.status}`);
  return res.json();
}

export async function fetchPlayerDetail(id: string | number): Promise<PlayerDetail> {
  const res = await fetch(`${API_URL}/players/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch player: ${res.status}`);
  return res.json();
}


