import { useParams } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Card } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchPlayerDetail, type PlayerDetail } from "@/lib/api";

const PlayerProfile = () => {
  const { id } = useParams();
  const { data, isLoading, isError, error } = useQuery<PlayerDetail>({
    queryKey: ["player", id],
    queryFn: () => fetchPlayerDetail(id as string),
    enabled: Boolean(id),
  });

  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />

      <main className="flex-1 pt-20">
        <div className="container mx-auto px-6 py-16">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold tracking-tight">Player Profile</h1>
          </div>

          {isLoading && (
            <div className="text-center text-muted-foreground">Loading...</div>
          )}
          {isError && (
            <div className="text-center text-red-500">{(error as Error)?.message ?? "Failed to load player"}</div>
          )}

          {!isLoading && !isError && data && (
            <Card className="p-6 space-y-6">
              <div>
                <div className="text-2xl font-semibold">{data.name}</div>
                <div className="text-sm text-muted-foreground">{data.club} | {data.league}</div>
              </div>

              <div>
                <h2 className="mb-2 text-lg font-semibold">Key Metrics</h2>
                <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                  {Object.entries(data.key_metrics).map(([k, v]) => (
                    <div key={k} className="rounded-md border p-3">
                      <div className="text-xs uppercase text-muted-foreground">{k}</div>
                      <div className="text-lg font-semibold">{String(v)}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="mb-2 text-lg font-semibold">Signing Rating</h2>
                <div className="rounded-md border p-4 text-center text-2xl font-bold">{data.signing_rating} / 10</div>
              </div>
            </Card>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default PlayerProfile;


