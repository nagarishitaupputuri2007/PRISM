type Props = {
  decisions: any[];
};

function DecisionBoard({ decisions }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6">
      <h2 className="text-xl font-bold mb-4">
        Recommended Decisions
      </h2>

      <div className="space-y-3">
        {decisions.map((decision, index) => (
          <div
            key={index}
            className="p-4 bg-slate-800 rounded-lg"
          >
            <p className="font-semibold">
              {decision.action}
            </p>

            <p className="text-slate-400 text-sm mt-1">
              Impact Score:
              {" "}
              {decision.business_impact}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DecisionBoard;