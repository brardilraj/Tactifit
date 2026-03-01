import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search } from "lucide-react";

const clubs = [
  { name: "Liverpool", logo: "/club-crests/liverpool.png" },
  { name: "Manchester United", logo: "/club-crests/manchester-united.png" },
  { name: "Manchester City", logo: "/club-crests/manchester-city.png" },
  { name: "Arsenal", logo: "/club-crests/arsenal.png" },
  { name: "Chelsea", logo: "/club-crests/chelsea.png" },
  { name: "Tottenham Hotspur", logo: "/club-crests/tottenham.png" },
  { name: "Aston Villa", logo: "/club-crests/aston-villa.png" },
  { name: "Newcastle United", logo: "/club-crests/newcastle.png" },
  { name: "Real Madrid", logo: "/club-crests/real-madrid.png" },
  { name: "Atletico Madrid", logo: "/club-crests/atletico-madrid.png" },
  { name: "Barcelona", logo: "/club-crests/barcelona.png" },
  { name: "Juventus", logo: "/club-crests/juventus.png" },
  { name: "AC Milan", logo: "/club-crests/ac-milan.png" },
  { name: "AS Roma", logo: "/club-crests/as-roma.png" },
  { name: "Inter Milan", logo: "/club-crests/inter-milan.png" },
  { name: "Napoli", logo: "/club-crests/napoli.png" },
  { name: "Bayern Munich", logo: "/club-crests/bayern-munich.png" },
  { name: "Borussia Dortmund", logo: "/club-crests/borussia-dortmund.png" },
  { name: "Bayer Leverkusen", logo: "/club-crests/bayer-leverkusen.png" },
  { name: "Paris Saint-Germain", logo: "/club-crests/psg.png" },
];

const positions = [
  "Strikers",
  "Left Winger",
  "Right Winger",
  "Attacking Midfielder",
  "Defensive Midfielder",
  "Center Midfielder",
  "Left Back",
  "Right Back",
  "Center Back",
  "Goalkeepers",
];

const ScoutingTool = () => {
  const navigate = useNavigate();
  const [club, setClub] = useState("");
  const [budget, setBudget] = useState([100]);
  const [ageRange, setAgeRange] = useState([18, 28]);
  const [position, setPosition] = useState("");

  const handleSearch = () => {
    const searchParams = new URLSearchParams({
      club,
      budget: budget[0].toString(),
      minAge: ageRange[0].toString(),
      maxAge: ageRange[1].toString(),
      position,
    });
    navigate(`/player-results?${searchParams.toString()}`);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />
      
      <main className="flex-1 pt-20">
        <div className="container mx-auto max-w-3xl px-6 py-16">
          <div className="mb-12 text-center">
            <h1 className="mb-4 text-5xl font-bold tracking-tight">
              Find Your Next{" "}
              <span className="glow-text text-primary">Star</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Use our advanced filters to discover the perfect player for your squad
            </p>
          </div>

          <div className="space-y-8 rounded-2xl border border-border bg-card p-8 shadow-card">
            {/* Club Selection */}
            <div className="space-y-3 animate-fade-in">
              <Label htmlFor="club" className="text-base font-semibold">
                Select your club
              </Label>
              <Select value={club} onValueChange={setClub}>
                <SelectTrigger id="club" className="h-12 bg-muted">
                  <SelectValue placeholder="Choose a club..." />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  {clubs.map((c) => (
                    <SelectItem key={c.name} value={c.name}>
                      <span className="flex items-center gap-3">
                        <img 
                          src={c.logo} 
                          alt={`${c.name} crest`}
                          className="h-6 w-6 object-contain"
                        />
                        {c.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Budget Slider */}
            <div className="space-y-3" style={{ animationDelay: "0.1s" }}>
              <Label className="text-base font-semibold">
                Select your budget
              </Label>
              <div className="space-y-2">
                <Slider
                  value={budget}
                  onValueChange={setBudget}
                  max={200}
                  step={5}
                  className="py-4"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>€0M</span>
                  <span className="font-semibold text-primary">€{budget[0]}M</span>
                  <span>€200M</span>
                </div>
              </div>
            </div>

            {/* Age Range Slider */}
            <div className="space-y-3" style={{ animationDelay: "0.2s" }}>
              <Label className="text-base font-semibold">
                Select the ideal age range
              </Label>
              <div className="space-y-2">
                <Slider
                  value={ageRange}
                  onValueChange={setAgeRange}
                  min={16}
                  max={40}
                  step={1}
                  className="py-4"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>16</span>
                  <span className="font-semibold text-primary">
                    {ageRange[0]} - {ageRange[1]} years
                  </span>
                  <span>40</span>
                </div>
              </div>
            </div>

            {/* Position Selection */}
            <div className="space-y-3" style={{ animationDelay: "0.3s" }}>
              <Label htmlFor="position" className="text-base font-semibold">
                Select the position you are looking for
              </Label>
              <Select value={position} onValueChange={setPosition}>
                <SelectTrigger id="position" className="h-12 bg-muted">
                  <SelectValue placeholder="Choose a position..." />
                </SelectTrigger>
                <SelectContent className="bg-popover">
                  {positions.map((pos) => (
                    <SelectItem key={pos} value={pos}>
                      {pos}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Search Button */}
            <Button
              onClick={handleSearch}
              disabled={!club || !position}
              className="h-14 w-full gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground shadow-glow transition-all hover:scale-[1.02] hover:shadow-glow disabled:opacity-50"
              style={{ animationDelay: "0.4s" }}
            >
              <Search className="h-5 w-5" />
              Find Players
            </Button>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default ScoutingTool;
