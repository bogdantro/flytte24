type StepKey = 1 | 2 | 3 | 4 | 5 | 6;

export function Illustration({ step }: { step: StepKey }) {
  const stroke = "#1a1a1a";
  const accent = "#5c5c5c";

  switch (step) {
    case 1:
      // Globus med forstørrelsesglass
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          <circle cx="160" cy="200" r="90" stroke={stroke} strokeWidth="3" />
          <ellipse cx="160" cy="200" rx="90" ry="38" stroke={stroke} strokeWidth="2" />
          <ellipse cx="160" cy="200" rx="38" ry="90" stroke={stroke} strokeWidth="2" />
          <line x1="70" y1="200" x2="250" y2="200" stroke={stroke} strokeWidth="2" />
          <line x1="160" y1="110" x2="160" y2="290" stroke={stroke} strokeWidth="2" />
          <ellipse cx="140" cy="180" rx="22" ry="14" fill="#cfcfcf" opacity="0.6" />
          <ellipse cx="180" cy="220" rx="18" ry="12" fill="#cfcfcf" opacity="0.6" />
          {/* Forstørrelsesglass */}
          <circle cx="290" cy="180" r="42" stroke={stroke} strokeWidth="3" />
          <circle cx="290" cy="180" r="42" fill="white" fillOpacity="0.4" />
          <line x1="320" y1="210" x2="345" y2="240" stroke={stroke} strokeWidth="6" strokeLinecap="round" />
          {/* Sparkles */}
          <circle cx="80" cy="120" r="3" fill={stroke} />
          <circle cx="100" cy="100" r="2" fill={accent} />
          <circle cx="240" cy="280" r="2" fill={accent} />
          <circle cx="320" cy="280" r="3" fill={stroke} />
          <circle cx="340" cy="120" r="2" fill={accent} />
        </svg>
      );

    case 2:
      // Kart med to pin-merker
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          {/* Kart */}
          <path d="M60 100 L160 80 L260 110 L340 90 L340 320 L260 300 L160 330 L60 310 Z" stroke={stroke} strokeWidth="3" fill="white" />
          <line x1="160" y1="80" x2="160" y2="330" stroke={stroke} strokeWidth="1.5" strokeDasharray="4 4" />
          <line x1="260" y1="110" x2="260" y2="300" stroke={stroke} strokeWidth="1.5" strokeDasharray="4 4" />
          {/* Fra-pin */}
          <circle cx="120" cy="180" r="14" fill={stroke} />
          <circle cx="120" cy="180" r="5" fill="white" />
          <path d="M120 194 L120 215" stroke={stroke} strokeWidth="3" />
          {/* Til-pin */}
          <circle cx="290" cy="220" r="14" fill="white" stroke={stroke} strokeWidth="3" />
          <circle cx="290" cy="220" r="5" fill={stroke} />
          <path d="M290 234 L290 255" stroke={stroke} strokeWidth="3" />
          {/* Stiplet linje mellom */}
          <path d="M134 180 Q200 130 280 220" stroke={stroke} strokeWidth="2" strokeDasharray="6 6" fill="none" />
        </svg>
      );

    case 3:
      // Hus / leilighet med vinduer
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          <path d="M200 80 L120 150 L120 320 L280 320 L280 150 Z" stroke={stroke} strokeWidth="3" />
          <path d="M120 150 L200 80 L280 150" stroke={stroke} strokeWidth="3" fill="#cfcfcf" fillOpacity="0.3" />
          <rect x="150" y="180" width="40" height="50" stroke={stroke} strokeWidth="2" />
          <line x1="170" y1="180" x2="170" y2="230" stroke={stroke} strokeWidth="1" />
          <line x1="150" y1="205" x2="190" y2="205" stroke={stroke} strokeWidth="1" />
          <rect x="210" y="180" width="40" height="50" stroke={stroke} strokeWidth="2" />
          <line x1="230" y1="180" x2="230" y2="230" stroke={stroke} strokeWidth="1" />
          <line x1="210" y1="205" x2="250" y2="205" stroke={stroke} strokeWidth="1" />
          <rect x="180" y="260" width="40" height="60" stroke={stroke} strokeWidth="2" />
          <circle cx="212" cy="290" r="2" fill={stroke} />
        </svg>
      );

    case 4:
      // Kalender
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          <rect x="80" y="120" width="240" height="200" rx="8" stroke={stroke} strokeWidth="3" fill="white" />
          <line x1="80" y1="170" x2="320" y2="170" stroke={stroke} strokeWidth="3" />
          <rect x="120" y="100" width="14" height="40" rx="4" fill={stroke} />
          <rect x="266" y="100" width="14" height="40" rx="4" fill={stroke} />
          {/* Datapunkter */}
          {[0, 1, 2, 3, 4, 5, 6].map((c) =>
            [0, 1, 2, 3].map((r) => (
              <circle
                key={`${c}-${r}`}
                cx={110 + c * 30}
                cy={195 + r * 30}
                r={c === 3 && r === 1 ? 12 : 3}
                fill={c === 3 && r === 1 ? stroke : accent}
              />
            )),
          )}
        </svg>
      );

    case 5:
      // Stack med tilleggsbokser
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          <rect x="100" y="220" width="200" height="100" stroke={stroke} strokeWidth="3" fill="white" />
          <path d="M100 220 L150 180 L350 180 L300 220" stroke={stroke} strokeWidth="3" fill="#cfcfcf" fillOpacity="0.3" />
          <path d="M300 220 L350 180 L350 280 L300 320" stroke={stroke} strokeWidth="3" fill="#cfcfcf" fillOpacity="0.2" />
          <line x1="200" y1="230" x2="200" y2="300" stroke={stroke} strokeWidth="2" strokeDasharray="4 4" />
          {/* Sjekkmerker */}
          <circle cx="120" cy="120" r="18" stroke={stroke} strokeWidth="3" fill="#d6e8a8" />
          <path d="M111 120 L118 127 L130 113" stroke={stroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="170" cy="100" r="14" stroke={stroke} strokeWidth="3" fill="white" />
          <path d="M163 100 L168 105 L177 95" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="220" cy="125" r="16" stroke={stroke} strokeWidth="3" fill="#d6e8a8" />
          <path d="M212 125 L218 131 L228 119" stroke={stroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );

    case 6:
      // Telefon/snakkeboble
      return (
        <svg viewBox="0 0 400 400" fill="none" className="h-full w-full">
          <rect x="140" y="100" width="140" height="240" rx="22" stroke={stroke} strokeWidth="3" fill="white" />
          <rect x="156" y="120" width="108" height="180" rx="6" stroke={stroke} strokeWidth="2" fill="#f7f5ef" />
          <circle cx="210" cy="320" r="6" fill={stroke} />
          {/* Chatbobler */}
          <rect x="170" y="150" width="60" height="22" rx="11" fill="#d6e8a8" />
          <rect x="190" y="180" width="64" height="22" rx="11" stroke={stroke} strokeWidth="2" fill="white" />
          <rect x="170" y="210" width="50" height="22" rx="11" fill="#d6e8a8" />
          <circle cx="320" cy="160" r="14" fill={stroke} />
          <path d="M313 160 L317 165 L327 155" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
  }
}
