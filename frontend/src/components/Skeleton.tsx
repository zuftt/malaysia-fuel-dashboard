type SkeletonProps = {
  className?: string;
  width?: string | number;
  height?: string | number;
};

export function Skeleton({ className = '', width, height }: SkeletonProps) {
  const style: React.CSSProperties = {};
  if (width != null) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height != null) style.height = typeof height === 'number' ? `${height}px` : height;
  return <span aria-hidden className={`rr-skeleton inline-block ${className}`} style={style} />;
}

export function PageSkeleton() {
  return (
    <div className="bg-[#fafaf7] text-[#0a0a0a] min-h-screen flex flex-col">
      <div className="fixed top-0 w-full z-50 border-b border-[#1a1a1a] bg-[#fafaf7] h-12" />
      <main className="flex-1 px-3 sm:px-6 max-w-7xl mx-auto w-full pb-24 sm:pb-12 pt-16 space-y-10">
        <div className="pt-6 pb-4 border-b border-[#1a1a1a]">
          <Skeleton className="block mb-3" width={220} height={12} />
          <Skeleton className="block mb-2" width="80%" height={36} />
          <Skeleton className="block" width="60%" height={36} />
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Skeleton className="block" height={36} />
            <Skeleton className="block" height={36} />
            <Skeleton className="block" height={36} />
          </div>
        </div>

        <section>
          <Skeleton className="block mb-2" width={140} height={12} />
          <Skeleton className="block mb-4" width={280} height={26} />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="panel p-4">
                <Skeleton className="block mb-3" width="50%" height={16} />
                <Skeleton className="block mb-3" width="70%" height={42} />
                <Skeleton className="block" width="60%" height={12} />
              </div>
            ))}
          </div>
        </section>

        <section>
          <Skeleton className="block mb-2" width={140} height={12} />
          <Skeleton className="block mb-4" width={280} height={26} />
          <div className="panel p-5">
            <Skeleton className="block" height={320} />
          </div>
        </section>

        <section>
          <Skeleton className="block mb-2" width={140} height={12} />
          <Skeleton className="block mb-4" width={280} height={26} />
          <div className="panel p-5">
            <Skeleton className="block" height={280} />
          </div>
        </section>
      </main>
    </div>
  );
}
