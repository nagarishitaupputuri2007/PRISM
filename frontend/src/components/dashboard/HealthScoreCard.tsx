type Props = {
  score: number;
};

function HealthScoreCard({ score }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <p className="text-slate-400 text-sm mb-2">
        Product Health Score
      </p>

      <h2 className="text-5xl font-bold text-green-400">
        {score.toFixed(0)}
      </h2>

      <p className="text-slate-500 mt-2">
        Overall Product Health
      </p>
    </div>
  );
}

export default HealthScoreCard;