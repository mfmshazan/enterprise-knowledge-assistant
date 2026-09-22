interface SkeletonProps {
  className?: string;
}

/** Shimmering placeholder block for loading states. */
export function Skeleton({ className = "" }: SkeletonProps) {
  return <div aria-hidden className={`eka-skeleton ${className}`} />;
}

/** Convenience: a stack of text-line skeletons. */
export function SkeletonLines({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-3.5 ${i === lines - 1 ? "w-2/3" : "w-full"}`} />
      ))}
    </div>
  );
}
