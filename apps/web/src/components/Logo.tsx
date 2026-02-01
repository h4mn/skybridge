/**
 * Logo Skybridge - Ponte conectando Sky à Terra
 */
export default function Logo({ width = 32, height = 32 }: { width?: number; height?: number }) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      style={{ verticalAlign: 'middle', marginRight: '8px' }}
    >
      <defs>
        <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#667eea" />
          <stop offset="100%" stopColor="#764ba2" />
        </linearGradient>
        <linearGradient id="bridgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#f87171" />
          <stop offset="50%" stopColor="#ef4444" />
          <stop offset="100%" stopColor="#dc2626" />
        </linearGradient>
      </defs>

      {/* Fundo circular */}
      <circle cx="50" cy="50" r="48" fill="url(#skyGrad)" fillOpacity={0.15} />

      {/* Nuvens no topo (Sky) */}
      <g fill="#a78bfa" fillOpacity={0.6}>
        <ellipse cx="25" cy="18" rx="12" ry="6" />
        <ellipse cx="35" cy="15" rx="8" ry="5" />
        <ellipse cx="65" cy="17" rx="10" ry="5" />
        <ellipse cx="75" cy="19" rx="9" ry="5" />
      </g>

      {/* Torres de suspensão */}
      <rect x="18" y="28" width="5" height="45" fill="url(#bridgeGrad)" rx="1" />
      <rect x="16" y="26" width="9" height="3" fill="url(#bridgeGrad)" rx="1" />

      <rect x="47" y="22" width="6" height="55" fill="url(#bridgeGrad)" rx="1" />
      <rect x="45" y="20" width="10" height="3" fill="url(#bridgeGrad)" rx="1" />

      <rect x="77" y="28" width="5" height="45" fill="url(#bridgeGrad)" rx="1" />
      <rect x="75" y="26" width="9" height="3" fill="url(#bridgeGrad)" rx="1" />

      {/* Cabos de suspensão */}
      <path d="M 20 29 Q 50 12 80 29" stroke="url(#bridgeGrad)" strokeWidth="2.5" fill="none" />
      <path d="M 20 29 Q 35 20 50 20" stroke="url(#bridgeGrad)" strokeWidth="1.5" fill="none" />
      <path d="M 80 29 Q 65 20 50 20" stroke="url(#bridgeGrad)" strokeWidth="1.5" fill="none" />

      {/* Tabuleiro da ponte */}
      <path d="M 12 52 L 12 58 L 88 58 L 88 52 Z" fill="url(#bridgeGrad)" />
      <line x1="12" y1="55" x2="88" y2="55" stroke="#991b1b" strokeWidth="1" />

      {/* Verticais (cabos) */}
      <line x1="25" y1="33" x2="25" y2="52" stroke="url(#bridgeGrad)" strokeWidth="1.5" />
      <line x1="35" y1="27" x2="35" y2="52" stroke="url(#bridgeGrad)" strokeWidth="1.5" />
      <line x1="50" y1="22" x2="50" y2="52" stroke="url(#bridgeGrad)" strokeWidth="1.5" />
      <line x1="65" y1="27" x2="65" y2="52" stroke="url(#bridgeGrad)" strokeWidth="1.5" />
      <line x1="75" y1="33" x2="75" y2="52" stroke="url(#bridgeGrad)" strokeWidth="1.5" />

      {/* Terra/Base */}
      <rect x="10" y="75" width="80" height="8" fill="#374151" rx="2" />
      <rect x="15" y="83" width="70" height="4" fill="#1f2937" rx="1" />

      {/* Pilares */}
      <rect x="17" y="58" width="7" height="20" fill="#6b7280" />
      <rect x="47" y="58" width="8" height="20" fill="#6b7280" />
      <rect x="76" y="58" width="7" height="20" fill="#6b7280" />

      {/* Data flow dots */}
      <circle cx="30" cy="50" r="1.5" fill="#fbbf24" />
      <circle cx="45" cy="48" r="1.5" fill="#fbbf24" />
      <circle cx="55" cy="49" r="1.5" fill="#fbbf24" />
      <circle cx="70" cy="50" r="1.5" fill="#fbbf24" />
    </svg>
  );
}
