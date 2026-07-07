type Problem = {
  problem_type: string;
  description: string;
  severity: number;
};

type Props = {
  problems: Problem[];
};

function getSeverityColor(
  severity: number
) {
  if (severity >= 8) {
    return "text-red-400";
  }

  if (severity >= 5) {
    return "text-yellow-400";
  }

  return "text-green-400";
}

function ProblemsTable({
  problems,
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
      <h2
        className="
          text-2xl
          font-bold
          mb-6
        "
      >
        Detected Problems
      </h2>

      <div className="overflow-x-auto">

        <table className="w-full">

          <thead>

            <tr className="border-b border-slate-800">

              <th className="text-left pb-4">
                Severity
              </th>

              <th className="text-left pb-4">
                Problem Type
              </th>

              <th className="text-left pb-4">
                Description
              </th>

            </tr>

          </thead>

          <tbody>

            {problems.map(
              (
                problem,
                index
              ) => (
                <tr
                  key={index}
                  className="
                    border-b
                    border-slate-800
                  "
                >
                  <td
                    className={`
                      py-4
                      font-bold
                      ${getSeverityColor(
                        problem.severity
                      )}
                    `}
                  >
                    {problem.severity}
                  </td>

                  <td className="py-4">
                    {problem.problem_type}
                  </td>

                  <td className="py-4 text-slate-300">
                    {problem.description}
                  </td>

                </tr>
              )
            )}

          </tbody>

        </table>

      </div>

    </div>
  );
}

export default ProblemsTable;