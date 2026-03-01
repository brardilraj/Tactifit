import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import HeroAnimation from "@/components/HeroAnimation";
import { ArrowRight } from "lucide-react";

const Home = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative flex min-h-screen items-center justify-center overflow-hidden">
          <HeroAnimation />
          
          <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
            <h1 className="mb-6 text-6xl font-bold tracking-tight md:text-7xl lg:text-8xl">
              Welcome to{" "}
              <span className="glow-text bg-gradient-primary bg-clip-text text-transparent">
                TACTIFIT
              </span>
            </h1>
            
            <p className="mb-12 text-xl text-muted-foreground md:text-2xl">
              A one-stop destination for all your scouting needs, powered by Opta.
            </p>
            
            <Link to="/scouting-tool">
              <Button 
                size="lg" 
                className="group h-14 gap-2 rounded-full bg-primary px-8 text-lg font-semibold text-primary-foreground shadow-glow transition-all hover:scale-105 hover:shadow-glow"
              >
                Start Scouting
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </div>
          
          {/* Bottom gradient fade */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
        </section>
      </main>
      
      <Footer />
    </div>
  );
};

export default Home;
