import { ParticleField } from "@/components/ambient/ParticleField";
import { DarkPatternCarousel } from "@/components/landing/DarkPatternCarousel";
import { HeroSection } from "@/components/landing/HeroSection";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { SignalShowcase } from "@/components/landing/SignalShowcase";
import { SiteTypeGrid } from "@/components/landing/SiteTypeGrid";

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[var(--v-deep)]">
      {/* Ambient particle background */}
      <ParticleField color="cyan" particleCount={60} />

      <main className="relative z-10">
        <HeroSection />
        <SignalShowcase />
        <DarkPatternCarousel />
        <HowItWorks />
        <SiteTypeGrid />

        {/* Footer */}
        <footer className="py-16 text-center border-t border-white/5">
          <p className="text-sm text-[var(--v-text-tertiary)]">
            Veritas — Trust, Verified.
          </p>
        </footer>
      </main>
    </div>
  );
}
