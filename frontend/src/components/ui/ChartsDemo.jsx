/**
 * ChartsDemo - Page de démonstration des composants de graphiques
 * Design System Next-Gen 2025
 */

import {
  BarChart,
  AreaChart,
  DonutChart,
  ProgressRings,
  SparklineCard,
  ChartCard,
} from './Charts.jsx';

// Données de démonstration
const barChartData = [
  { label: 'Lun', value: 120, color: 'emerald' },
  { label: 'Mar', value: 180, color: 'emerald' },
  { label: 'Mer', value: 140, color: 'emerald' },
  { label: 'Jeu', value: 160, color: 'emerald' },
  { label: 'Ven', value: 200, color: 'emerald' },
  { label: 'Sam', value: 190, color: 'teal' },
  { label: 'Dim', value: 100, color: 'slate' },
];

const areaChartData = [180, 160, 140, 100, 80, 60, 40];
const areaChartLabels = ['1 Déc', '8 Déc', '15 Déc', '22 Déc', '24 Déc'];

const donutChartData = [
  { label: 'Épicerie', value: 40, color: 'emerald' },
  { label: 'Restaurant', value: 24, color: 'amber' },
  { label: 'Boissons', value: 16, color: 'blue' },
  { label: 'Autres', value: 20, color: 'violet' },
];

const progressRingsData = [
  { label: 'CA Mensuel', value: 75, color: 'emerald' },
  { label: 'Marge', value: 50, color: 'amber' },
  { label: 'Stock', value: 90, color: 'teal' },
];

const sparklineData = [10, 15, 12, 18, 14, 22, 19, 25, 21, 28];

export default function ChartsDemo() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-10">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2 font-['Sora']">Charts Components</h1>
        <p className="text-slate-400 mb-10">Visualisations de données pour tableaux de bord</p>

        <h2 className="text-lg font-semibold mb-5 pb-3 border-b border-white/15">
          Graphiques principaux
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <ChartCard>
            <BarChart
              data={barChartData}
              title="Ventes par jour"
              legend={[
                { label: 'Cette semaine', color: 'emerald' },
                { label: 'Semaine dernière', color: 'slate' },
              ]}
              height={200}
            />
          </ChartCard>

          {/* Area Chart */}
          <ChartCard>
            <AreaChart
              data={areaChartData}
              labels={areaChartLabels}
              title="Évolution CA (30 jours)"
              color="emerald"
              height={200}
              showDots
            />
          </ChartCard>

          {/* Donut Chart */}
          <ChartCard>
            <DonutChart
              data={donutChartData}
              title="Répartition des ventes"
              centerValue="€45K"
              centerLabel="Total"
              size={160}
            />
          </ChartCard>

          {/* Progress Rings */}
          <ChartCard>
            <ProgressRings
              rings={progressRingsData}
              title="Objectifs"
              size={80}
            />
          </ChartCard>
        </div>

        <h2 className="text-lg font-semibold mt-10 mb-5 pb-3 border-b border-white/15">
          Sparkline Cards
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SparklineCard
            title="Chiffre d'affaires"
            subtitle="Ce mois"
            value="€12,450"
            data={sparklineData}
            color="emerald"
            trend="up"
            trendValue="+12%"
          />

          <SparklineCard
            title="Marge brute"
            subtitle="Ce mois"
            value="32%"
            data={[20, 22, 18, 25, 23, 28, 26, 30, 28, 32]}
            color="blue"
            trend="up"
            trendValue="+3%"
          />

          <SparklineCard
            title="Commandes"
            subtitle="Cette semaine"
            value="156"
            data={[12, 15, 18, 14, 22, 19, 25]}
            color="amber"
            trend="down"
            trendValue="-5%"
          />
        </div>

        <h2 className="text-lg font-semibold mt-10 mb-5 pb-3 border-b border-white/15">
          Variantes de couleurs
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['emerald', 'blue', 'amber', 'rose'].map((color) => (
            <ChartCard key={color}>
              <AreaChart
                data={[10, 25, 15, 30, 20, 35, 28]}
                title={color.charAt(0).toUpperCase() + color.slice(1)}
                color={color}
                height={120}
              />
            </ChartCard>
          ))}
        </div>
      </div>
    </div>
  );
}
