type Props = {
  healthScore: number;
  problemCount: number;
  rootCauseCount: number;
  decisionCount: number;
};

function KPISection({
  healthScore,
  problemCount,
  rootCauseCount,
  decisionCount,
}: Props) {
  const cards = [
    {
      title: "Health Score",
      value: Math.round(healthScore),
    },
    {
      title: "Problems",
      value: problemCount,
    },
    {
      title: "Root Causes",
      value: rootCauseCount,
    },
    {
      title: "Decisions",
      value: decisionCount,
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
          "
        >
          <p className="text-slate-400 text-sm">
            {card.title}
          </p>

          <h2 className="text-3xl font-bold mt-2">
            {card.value}
          </h2>
        </div>
      ))}
    </div>
  );
}

export default KPISection;