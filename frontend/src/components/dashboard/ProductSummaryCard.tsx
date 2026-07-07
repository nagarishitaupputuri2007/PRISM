type Props = {
  product: {
    product_name: string;
    category: string;
    business_model: string;
    confidence_level: string;
    confidence_score: number;
    competitors: string[];
    target_users: string[];
  };
};

function ProductSummaryCard({ product }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">

      <h2 className="text-2xl font-bold mb-4">
        Product Summary
      </h2>

      <div className="grid grid-cols-2 gap-6">

        <div>
          <p className="text-slate-400 text-sm">
            Product Name
          </p>

          <p className="font-semibold">
            {product.product_name}
          </p>
        </div>

        <div>
          <p className="text-slate-400 text-sm">
            Category
          </p>

          <p className="font-semibold">
            {product.category}
          </p>
        </div>

        <div>
          <p className="text-slate-400 text-sm">
            Business Model
          </p>

          <p className="font-semibold">
            {product.business_model}
          </p>
        </div>

        <div>
          <p className="text-slate-400 text-sm">
            Confidence Level
          </p>

          <p className="font-semibold text-green-400">
            {product.confidence_level}
          </p>
        </div>

      </div>

      <div className="mt-6">

        <p className="text-slate-400 text-sm mb-2">
          Target Users
        </p>

        <div className="flex flex-wrap gap-2">
          {product.target_users.map((user) => (
            <span
              key={user}
              className="px-3 py-1 rounded-full bg-slate-800 text-sm"
            >
              {user}
            </span>
          ))}
        </div>

      </div>

      <div className="mt-6">

        <p className="text-slate-400 text-sm mb-2">
          Competitors
        </p>

        <div className="flex flex-wrap gap-2">
          {product.competitors.map((competitor) => (
            <span
              key={competitor}
              className="px-3 py-1 rounded-full bg-slate-800 text-sm"
            >
              {competitor}
            </span>
          ))}
        </div>

      </div>

    </div>
  );
}

export default ProductSummaryCard;