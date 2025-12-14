import PageHeader from '../components/PageHeader.jsx';

export default function PageLayout({
  title,
  description,
  icon,
  actions = [],
  header,
  children,
  aside,
}) {
  return (
    <div className="space-y-6">
      {header || <PageHeader icon={icon} title={title} description={description} actions={actions} />}

      <div className={aside ? 'grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]' : 'space-y-6'}>
        <div className="space-y-6">{children}</div>
        {aside && <div className="space-y-4">{aside}</div>}
      </div>
    </div>
  );
}
