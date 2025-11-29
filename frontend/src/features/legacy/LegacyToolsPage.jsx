import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';

export default function LegacyToolsPage() {
  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">mode expert</p>
          <h2 className="text-2xl font-semibold text-slate-900">Outils Streamlit historiques</h2>
          <p className="text-sm text-slate-500">
            Extraction de factures, audit inventaire et modules avancés restent accessibles pendant la
            migration.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button as="a" href="http://localhost:8501" target="_blank" rel="noreferrer">
            Ouvrir dans un nouvel onglet
          </Button>
          <Button variant="ghost" as="a" href="mailto:ops@epicerie.fr">
            Demander un portage
          </Button>
        </div>
      </Card>

      <Card className="p-0">
        <iframe
          className="legacy-iframe"
          title="Application Streamlit"
          src="http://localhost:8501"
          allow="camera; microphone"
        />
      </Card>
    </div>
  );
}
