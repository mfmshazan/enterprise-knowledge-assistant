import type { DocumentStatus } from "@/lib/api";

const STYLES: Record<DocumentStatus, { bg: string; dot: string }> = {
  pending: { bg: "bg-amber-50 text-amber-700 border-amber-200", dot: "bg-amber-400" },
  processing: { bg: "bg-blue-50 text-blue-700 border-blue-200", dot: "bg-blue-500 animate-pulse" },
  indexed: { bg: "bg-emerald-50 text-emerald-700 border-emerald-200", dot: "bg-emerald-500" },
  failed: { bg: "bg-rose-50 text-rose-700 border-rose-200", dot: "bg-rose-500" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const conf = STYLES[status] || STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${conf.bg}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${conf.dot}`} />
      {status}
    </span>
  );
}
