import { Link, useLocation } from "react-router-dom";
import { Target } from "lucide-react";

const Navigation = () => {
  const location = useLocation();
  
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <nav className="container mx-auto flex items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <Target className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold tracking-tight">TACTIFIT</span>
        </Link>
        
        <div className="flex gap-8">
          <Link 
            to="/" 
            className={`text-sm font-medium transition-colors hover:text-primary ${
              location.pathname === "/" ? "text-primary" : "text-muted-foreground"
            }`}
          >
            Home
          </Link>
          <Link 
            to="/scouting-tool" 
            className={`text-sm font-medium transition-colors hover:text-primary ${
              location.pathname === "/scouting-tool" ? "text-primary" : "text-muted-foreground"
            }`}
          >
            Scouting Tool
          </Link>
        </div>
      </nav>
    </header>
  );
};

export default Navigation;
