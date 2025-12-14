import StatCard from './StatCard.jsx';

export default function MetricGrid({ metrics = [], fallback = [] }) {
  const items = metrics.length ? metrics : fallback;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {items.map((metric, idx) => (
        <StatCard
          key={idx}
          label={metric.label}
          value={metric.value}
          trend={metric.trend}
          trendValue={metric.trendValue}
          icon={metric.icon}
          color={metric.color}
        />
      ))}
    </div>
  );
}
