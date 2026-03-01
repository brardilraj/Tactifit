const HeroAnimation = () => {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Radial gradient background */}
      <div className="absolute inset-0 bg-gradient-hero" />
      
      {/* Animated grid */}
      <div className="absolute inset-0" style={{
        backgroundImage: `
          linear-gradient(to right, hsl(var(--primary) / 0.05) 1px, transparent 1px),
          linear-gradient(to bottom, hsl(var(--primary) / 0.05) 1px, transparent 1px)
        `,
        backgroundSize: '80px 80px',
        animation: 'pulse-glow 4s ease-in-out infinite'
      }} />
      
      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-primary/20 animate-pulse-glow"
          style={{
            width: Math.random() * 4 + 2 + 'px',
            height: Math.random() * 4 + 2 + 'px',
            left: Math.random() * 100 + '%',
            top: Math.random() * 100 + '%',
            animationDelay: Math.random() * 3 + 's',
            animationDuration: Math.random() * 3 + 3 + 's',
          }}
        />
      ))}
      
      {/* Larger glowing orbs */}
      {[...Array(5)].map((_, i) => (
        <div
          key={`orb-${i}`}
          className="absolute rounded-full blur-3xl animate-float"
          style={{
            width: Math.random() * 200 + 100 + 'px',
            height: Math.random() * 200 + 100 + 'px',
            left: Math.random() * 100 + '%',
            top: Math.random() * 100 + '%',
            background: `radial-gradient(circle, hsl(var(--primary) / ${Math.random() * 0.15 + 0.05}), transparent)`,
            animationDelay: Math.random() * 6 + 's',
            animationDuration: Math.random() * 4 + 6 + 's',
          }}
        />
      ))}
    </div>
  );
};

export default HeroAnimation;
