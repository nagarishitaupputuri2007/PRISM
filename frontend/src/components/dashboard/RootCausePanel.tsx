type RootCause = {
  problem_id: string;
  problem_type: string;
  root_cause: string;
};

type Props = {
  rootCauses: RootCause[];
};

function RootCausePanel({
  rootCauses,
}: Props) {
  return (
    <div
      className="
        bg-slate-900
        border
        border-slate-800
        rounded-2xl
        p-6
        mb-6
      "
    >
      <h2 className="text-2xl font-bold mb-6">
        Root Cause Analysis
      </h2>

      <div className="space-y-4">
        {rootCauses.map((cause) => (
          <div
            key={cause.problem_id}
            className="
              bg-slate-800
              rounded-xl
              p-4
            "
          >
            <p
              className="
                text-red-400
                text-sm
                font-semibold
                mb-2
              "
            >
              {cause.problem_type}
            </p>

            <p className="text-slate-200">
              {cause.root_cause}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RootCausePanel;