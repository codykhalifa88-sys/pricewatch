import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export type PricePoint = { price: number; checked_at: string };

export default function PriceChart({ data }: { data: PricePoint[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-xs text-ink-400">
        No price history yet — the next scheduled check will record one.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    label: new Date(d.checked_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
  }));

  return (
    <ResponsiveContainer width="100%" height={128}>
      <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#8a8a97" }} axisLine={false} tickLine={false} />
        <YAxis hide domain={["auto", "auto"]} />
        <Tooltip
          formatter={(value) => [`£${Number(value).toFixed(2)}`, "Price"]}
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #eeeef0" }}
        />
        <Line type="monotone" dataKey="price" stroke="#059669" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
