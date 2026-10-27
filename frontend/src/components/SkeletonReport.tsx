export default function SkeletonReport() {
  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div className="skeleton h-[340px]" />
      <div className="skeleton h-[340px]" />
      <div className="skeleton h-[420px] lg:col-span-2" />
      <div className="skeleton h-[300px]" />
      <div className="skeleton h-[300px]" />
    </div>
  );
}
