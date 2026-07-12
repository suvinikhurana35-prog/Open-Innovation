import { ExternalLink } from "lucide-react";
import { getSchemeUrl } from "@/lib/schemeLinks";

interface SourceBadgeProps {
  source: string;
  ministry?: string;
  lastUpdated?: string;
  confidence?: string;
  className?: string;
  /** Official page of THIS scheme. When given, the badge links here instead
   *  of falling back to a MyScheme search (fix: never link to listings). */
  officialUrl?: string;
}

export function SourceBadge({ source, ministry, lastUpdated, confidence, className = "", officialUrl }: SourceBadgeProps) {
  const url = officialUrl || getSchemeUrl(source);
  const confColor = confidence === 'High' ? 'text-green-600' : confidence === 'Medium' ? 'text-yellow-600' : 'text-red-600';

  return (
    <span className={`inline-flex flex-wrap items-center gap-x-2 gap-y-1 ${className}`}>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 rounded-full border border-green-200 bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 hover:bg-green-100 transition-colors"
      >
        <ExternalLink className="h-3 w-3 shrink-0" />
        {source}
      </a>
      {ministry && <span className="text-xs text-gray-500">{ministry}</span>}
      {lastUpdated && <span className="text-xs text-gray-400">Updated: {lastUpdated}</span>}
      {confidence && <span className={`text-xs font-medium ${confColor}`}>{confidence}</span>}
    </span>
  );
}

export default SourceBadge;
