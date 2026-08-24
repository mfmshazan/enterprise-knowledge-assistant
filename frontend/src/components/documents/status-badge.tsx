import type { DocumentStatus } from "@/lib/api";

const STYLES: Record<DocumentStatus, string> = {
  pending: "bg-yellow-500/15 text-yellow-300",
  processing: "bg-blue-500/15 text-blue-300",
  indexed: "bg-green-500/15 text-green-300",
  failed: "bg-red-500/15 text-red-300",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {status}
    </span>
  );
}
