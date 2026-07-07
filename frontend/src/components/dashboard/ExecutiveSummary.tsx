// ============================================
// ExecutiveSummary.tsx
// Purpose:
// Displays a concise executive briefing for
// product managers and leadership.
// ============================================

type ExecutiveSummaryProps = {
  healthScore: number;
  biggestRisk: string;
  topPriority: string;
  expectedBusinessImpact: string;
};

function ExecutiveSummary({
  healthScore,
  biggestRisk,
  topPriority,
  expectedBusinessImpact,
}: ExecutiveSummaryProps) {

  const summaryItems = [
    {
      title: "Product Health",
      value: `${healthScore}/100`,
    },
    {
      title: "Biggest Business Risk",
      value: biggestRisk,
    },
    {
      title: "Highest Priority",
      value: topPriority,
    },
    {
      title: "Expected Business Impact",
      value: expectedBusinessImpact,
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

      <div className="mb-6">
        <h2 className="text-2xl font-bold">
          Executive Summary
        </h2>

        <p className="text-slate-400 mt-2">
          A concise briefing for product leaders.
        </p>
      </div>

      <div className="divide-y divide-slate-800">
        {summaryItems.map((item) => (
          <div
            key={item.title}
            className="py-4 first:pt-0 last:pb-0"
          >
            <p className="text-sm text-slate-400">
              {item.title}
            </p>

            <p className="mt-1 text-base font-medium text-white">
              {item.value}
            </p>
          </div>
        ))}
      </div>

    </div>
  );
}

export default ExecutiveSummary;