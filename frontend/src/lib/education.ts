/* ========================================
   Veritas — Educational Content
   Facts, terminology, and safety tips
   ======================================== */

export interface DidYouKnowFact {
  id: string;
  title: string;
  text: string;
  source: string;
}

export interface TermDefinition {
  term: string;
  definition: string;
}

export interface SafetyTip {
  id: string;
  tip: string;
}

// ── Dark Pattern Facts ──
export const DARK_PATTERN_FACTS: DidYouKnowFact[] = [
  {
    id: "f1",
    title: "The $12.8 Billion Problem",
    text: "Dark patterns cost consumers an estimated $12.8 billion per year through deceptive design choices that trick people into unintended purchases.",
    source: "FTC Consumer Reports, 2023",
  },
  {
    id: "f2",
    title: "11,000 Websites, 1,818 Dark Patterns",
    text: "A Princeton University study crawled 11,000 shopping websites and found 1,818 instances of dark patterns. Nearly 1 in 6 websites used at least one.",
    source: "Princeton Web Transparency & Accountability Project",
  },
  {
    id: "f3",
    title: "The EU Strikes Back",
    text: "The European Union's Digital Services Act explicitly bans dark patterns, making deceptive UX design illegal with fines up to 6% of global revenue.",
    source: "EU Digital Services Act, Article 25",
  },
  {
    id: "f4",
    title: "Roach Motel: Easy In, Hard Out",
    text: "One of the most common dark patterns is the 'Roach Motel' — signing up takes one click, but canceling requires calling a phone number during business hours.",
    source: "darkpatterns.org",
  },
  {
    id: "f5",
    title: "The Fake Timer Trick",
    text: "Fake countdown timers on e-commerce sites create artificial urgency. Studies show they increase conversion by 332%, but the timer simply resets when it reaches zero.",
    source: "Journal of Marketing Research",
  },
  {
    id: "f6",
    title: "Amazon's Dark Secret",
    text: "Internal Amazon documents revealed the company deliberately made it difficult to cancel Prime subscriptions. The project was internally named 'Iliad' — after Homer's epic about a war that dragged on forever.",
    source: "FTC v. Amazon.com, Inc., 2023",
  },
  {
    id: "f7",
    title: "Confirmshaming",
    text: "Many websites use guilt-tripping language on decline buttons: 'No thanks, I don't want to save money' or 'I prefer to pay full price.' This psychological manipulation is called confirmshaming.",
    source: "UX Research Institute",
  },
  {
    id: "f8",
    title: "The Pre-Selected Checkbox",
    text: "Studies show that pre-checked boxes have a 70–90% opt-in rate, compared to 10–30% when unchecked. That's why hidden subscriptions and add-ons are pre-selected by default.",
    source: "Behavioral Economics Research",
  },
];

// ── Phase-specific terminology ──
export const PHASE_TERMS: Record<string, TermDefinition[]> = {
  scout: [
    {
      term: "Browser Fingerprinting",
      definition:
        "Websites can identify your browser by its unique combination of settings, fonts, and plugins — even without cookies. Our Browser Agent uses stealth techniques to avoid detection.",
    },
    {
      term: "SSL/TLS Certificate",
      definition:
        "The padlock icon in your browser. It encrypts data between you and the website. But a valid SSL doesn't mean the site is trustworthy — even phishing sites can have SSL certificates.",
    },
    {
      term: "DOM Analysis",
      definition:
        "The DOM is the website's internal structure — like an X-ray of the page. We analyze it to find hidden elements, invisible buttons, and deceptive form fields.",
    },
  ],
  security: [
    {
      term: "Content Security Policy (CSP)",
      definition:
        "A security header that tells the browser which scripts are allowed to run. Without CSP, attackers can inject malicious code into the page.",
    },
    {
      term: "Phishing Database",
      definition:
        "Databases like Google Safe Browsing maintain lists of known phishing websites. We cross-reference every audited URL against these global databases.",
    },
    {
      term: "HTTP Security Headers",
      definition:
        "When your browser visits a website, the server sends invisible 'headers' with security instructions. Missing headers mean potential vulnerabilities.",
    },
  ],
  vision: [
    {
      term: "AI Vision Analysis",
      definition:
        "Our AI 'sees' the website exactly like a human would — analyzing colors, button sizes, text contrast, and layout to detect visual manipulation.",
    },
    {
      term: "Visual Hierarchy Manipulation",
      definition:
        "Making the 'Accept' button large and colorful while the 'Decline' button is tiny and gray. This design trick guides your clicks toward the business-preferred action.",
    },
    {
      term: "Drip Pricing",
      definition:
        "Showing a low price initially, then adding fees, taxes, and surcharges at checkout. The final price can be 30–50% higher than what was advertised.",
    },
  ],
  graph: [
    {
      term: "WHOIS Lookup",
      definition:
        "A public database that shows who registered a domain name, when, and where. Fraudulent sites often use privacy services to hide their identity.",
    },
    {
      term: "Domain Age",
      definition:
        "How long a website has existed. Scam sites are often brand new (registered days ago), while legitimate businesses typically have older domains.",
    },
    {
      term: "Entity Verification",
      definition:
        "Cross-checking the company name, address, and claims on the website against business registries, DNS records, and public databases.",
    },
  ],
  judge: [
    {
      term: "Trust Score",
      definition:
        "A 0–100 score computed from 6 independent signals. Like a credit score for websites — higher means more trustworthy.",
    },
    {
      term: "Signal Weighting",
      definition:
        "Not all evidence is equal. Our Intelligence Network verification (hard to fake) is weighted more heavily than visual analysis (can be subjective).",
    },
    {
      term: "Override Rules",
      definition:
        "Some findings are so severe they override the calculated score. For example: a website found in phishing databases is automatically marked as high risk.",
    },
  ],
};

// ── Safety Tips ──
export const SAFETY_TIPS: SafetyTip[] = [
  { id: "s1", tip: "Always check the URL bar for the correct domain name before entering credentials." },
  { id: "s2", tip: "A padlock icon (SSL) doesn't guarantee the site is safe — it only means the connection is encrypted." },
  { id: "s3", tip: "Read cancellation and refund policies before subscribing to any service." },
  { id: "s4", tip: "If a deal seems too good to be true, it probably is. Verify the seller independently." },
  { id: "s5", tip: "Check website reviews on independent platforms, not just testimonials on the site itself." },
  { id: "s6", tip: "Be suspicious of countdown timers and 'limited stock' warnings — they're often fake." },
  { id: "s7", tip: "Never enter credit card details on a website that doesn't use HTTPS." },
  { id: "s8", tip: "If a website makes it hard to find the cancel button, that's a deliberate design choice." },
];

// ── Dark Pattern Categories for Landing Page ──
export const DARK_PATTERN_CATEGORIES = [
  {
    id: "visual_interference",
    name: "Visual Interference",
    icon: "🎭",
    description: "UI elements designed to mislead users through visual hierarchy manipulation — making desired actions prominent and undesired actions hidden.",
    examples: [
      "'Accept All' is a huge green button, 'Decline' is tiny gray text",
      "Unsubscribe link hidden in footer at 8px font size",
      "Download button that's actually an advertisement",
    ],
    severity: "High",
    subTypes: 5,
  },
  {
    id: "false_urgency",
    name: "False Urgency",
    icon: "⏰",
    description: "Fake time pressure designed to force hasty decisions — countdown timers that reset, fake scarcity messages, fabricated social proof.",
    examples: [
      "'Sale ends in 00:04:59' — resets to 5:00 on refresh",
      "'Only 2 left in stock!' — always says 2",
      "'15 people are viewing this right now' — static number",
    ],
    severity: "Critical",
    subTypes: 4,
  },
  {
    id: "forced_continuity",
    name: "Forced Continuity",
    icon: "🚪",
    description: "Making it deliberately difficult to cancel, unsubscribe, or delete an account — the 'Roach Motel' pattern.",
    examples: [
      "Online signup but must call to cancel",
      "'Are you sure? You'll lose all your progress!'",
      "Cancel button buried 5 levels deep in settings",
    ],
    severity: "Critical",
    subTypes: 4,
  },
  {
    id: "sneaking",
    name: "Sneaking",
    icon: "🐍",
    description: "Adding items, charges, or commitments without explicit user consent — hidden costs, pre-selected options, bait-and-switch pricing.",
    examples: [
      "Service fee added only at checkout",
      "Extended warranty checkbox pre-selected",
      "'From $9.99' but actual price is $19.99 with fees",
    ],
    severity: "Critical",
    subTypes: 4,
  },
  {
    id: "social_engineering",
    name: "Social Engineering",
    icon: "🎯",
    description: "Manipulating trust signals to appear more legitimate — fake reviews, unverifiable trust badges, fabricated authority claims.",
    examples: [
      "Norton Secured badge — just an image, no verification link",
      "Testimonials with stock photo headshots",
      "'As seen on CNN/Forbes' with no actual coverage",
    ],
    severity: "High",
    subTypes: 4,
  },
];

// ── Signal Definitions for Landing Page ──
export const TRUST_SIGNALS = [
  {
    id: "visual",
    label: "Visual Intelligence",
    icon: "👁️",
    weight: 0.2,
    description: "AI vision analyzes every screenshot for dark patterns, deceptive buttons, and visual manipulation.",
  },
  {
    id: "structural",
    label: "Page Structure",
    icon: "🔍",
    weight: 0.15,
    description: "Deep analysis of the website's DOM — hidden elements, invisible buttons, deceptive forms.",
  },
  {
    id: "temporal",
    label: "Time Analysis",
    icon: "⏱️",
    weight: 0.1,
    description: "Detects fake countdown timers, scarcity messages that reset, and time-based manipulation.",
  },
  {
    id: "graph",
    label: "Identity Verification",
    icon: "🌐",
    weight: 0.25,
    description: "Cross-references domain records, WHOIS data, business registries, and DNS for entity verification.",
  },
  {
    id: "meta",
    label: "Basic Verification",
    icon: "🔒",
    weight: 0.1,
    description: "Checks SSL certificates, domain age, metadata consistency, and basic trust indicators.",
  },
  {
    id: "security",
    label: "Security Audit",
    icon: "🛡️",
    weight: 0.2,
    description: "Scans HTTP headers, checks phishing databases, validates forms, and analyzes JavaScript.",
  },
];

// ── Site Types ──
export const SITE_TYPES = [
  { id: "ecommerce", label: "E-commerce", icon: "🛒", description: "Online stores and marketplaces" },
  { id: "company_portfolio", label: "Corporate", icon: "🏢", description: "Business and portfolio sites" },
  { id: "financial", label: "Financial", icon: "🏦", description: "Banking and fintech platforms" },
  { id: "saas_subscription", label: "SaaS", icon: "☁️", description: "Software subscription services" },
  { id: "darknet_suspicious", label: "Suspicious", icon: "🕶️", description: "Unverified or dark web sites" },
];
