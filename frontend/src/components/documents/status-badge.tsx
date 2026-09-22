import type { DocumentStatus } from "@/lib/api";
import { Badge, type BadgeTone } from "@/components/ui/badge";

const TONES: Record<DocumentStatus, BadgeTone> = {
  pending: "amber",
  processing: "blue",
  indexed: "emerald",
  failed: "rose",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const tone = TONES[status] ?? "amber";
  return (
    <Badge tone={tone} dot={status === "processing" ? "pulse" : true} uppercase>
      {status}
    </Badge>
  );
}
