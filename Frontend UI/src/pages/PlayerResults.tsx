import { useNavigate, useSearchParams } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { fetchPlayers, type PlayerListItem } from "@/lib/api";

const PlayerResults = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const position = searchParams.get("position") || "Players";
  const minAge = searchParams.get("minAge") || "18";
  const maxAge = searchParams.get("maxAge") || "28";
  const budget = searchParams.get("budget") || "100";
  const club = searchParams.get("club") || "";

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["players", { position, minAge, maxAge, budget, club }],
    queryFn: () =>
      fetchPlayers({
        position,
        minAge,
        maxAge,
        budget,
        club,
      }),
  });

  const players: PlayerListItem[] = data ?? [];

  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />
      
      <main className="flex-1 pt-20">
        <div className="container mx-auto px-6 py-16">
          <div className="mb-12 text-center">
            <h1 className="mb-4 text-5xl font-bold tracking-tight">
              Recommended{" "}
              <span className="glow-text text-primary">Players</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Showing results for:{" "}
              <span className="font-semibold text-primary">{position}</span>
              {" | "}
              Age: <span className="font-semibold text-primary">{minAge}-{maxAge}</span>
              {" | "}
              Budget: <span className="font-semibold text-primary">&lt; €{budget}M</span>
            </p>
          </div>

          {isLoading && (
            <div className="text-center text-muted-foreground">Loading players...</div>
          )}
          {isError && (
            <div className="text-center text-red-500">{(error as Error)?.message ?? "Failed to load players"}</div>
          )}

          {!isLoading && !isError && (
            <div className="space-y-3">
              {players.map((player) => (
                <Card key={player.id} className="flex items-center justify-between p-4">
                  <div>
                    <div className="text-lg font-semibold">{player.name}</div>
                    <div className="text-sm text-muted-foreground">{player.club} | {player.league}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-muted-foreground">Similarity: {(player.similarity_score * 100).toFixed(0)}%</div>
                    <Button onClick={() => navigate(`/player/${player.id}`)}>
                      View
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default PlayerResults;


