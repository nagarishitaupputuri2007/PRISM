import { useState } from "react";
import { analyzeProduct } from "../api/prismApi";
import type { AnalyzeResponse } from "../types/prism";
import DecisionBoard from
"../components/dashboard/DecisionBoard";
import ProductSummaryCard from
"../components/dashboard/ProductSummaryCard";
import KPISection from
"../components/dashboard/KPISection";
import ProblemsTable from
"../components/dashboard/ProblemsTable";
import RootCausePanel from
"../components/dashboard/RootCausePanel";
import ExecutiveSummary from "../components/dashboard/ExecutiveSummary";



function Home() {
  const [productName, setProductName] = useState("");

  const [loading, setLoading] = useState(false);

  const [analysis, setAnalysis] =
    useState<AnalyzeResponse | null>(null);

  const handleAnalyze = async () => {
    if (!productName.trim()) return;

    try {
      setLoading(true);

      const result = await analyzeProduct({
        product_name: productName,
      });

      console.log(result);

      setAnalysis(result);

    } catch (error) {
      console.error(error);

      alert("Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="max-w-6xl mx-auto px-6 py-20">

        <h1 className="text-6xl font-bold mb-6">
          PRISM
        </h1>

        <p className="text-xl text-slate-300 mb-10">
          Product Intelligence & Decision Intelligence System
        </p>

        <div className="flex gap-4">

          <input
            type="text"
            placeholder="Enter product name"
            value={productName}
            onChange={(e) =>
              setProductName(e.target.value)
            }
            className="
              px-4
              py-3
              rounded-lg
              bg-slate-800
              border
              border-slate-700
              w-96
            "
          />

          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="
              px-6
              py-3
              bg-blue-600
              hover:bg-blue-700
              rounded-lg
              font-semibold
              transition
            "
          >
            {loading
              ? "Analyzing..."
              : "Analyze"}
          </button>

        </div>
        {analysis && (
          <div className="mt-12 space-y-6">2T

            <ProductSummaryCard
              product={analysis.data.product}
            />
            <ExecutiveSummary
                healthScore={analysis.data.decisions.product_health_score}
                biggestRisk={
                    analysis.data.problems.problems[0]?.description ??
                    "No significant business risks detected."
                }
                topPriority={
                    analysis.data.decisions.decisions[0]?.action ??
                    "No immediate priorities."
                }
                expectedBusinessImpact={
                    analysis.data.decisions.decisions[0]?.business_outcome ??
                    "No expected business impact available."
                }
            />
            <KPISection
              healthScore={
                analysis.data.decisions.product_health_score
              }
              problemCount={
                analysis.data.problems.problems.length
              }
              rootCauseCount={
                analysis.data.root_causes.root_causes.length
              }
              decisionCount={
                analysis.data.decisions.decisions.length
              }
            />
            <RootCausePanel
              rootCauses={
                analysis.data.root_causes.root_causes
              }
            />
            <ProblemsTable
              problems={
                analysis.data.problems.problems
              }
            />


            {
              analysis?.data?.decisions?.decisions && (
                <DecisionBoard
                  decisions={
                    analysis.data.decisions.decisions
                  }
                />
              )
            }

          </div>
        )}
        

      </div>
    </div>
  );
}

export default Home;