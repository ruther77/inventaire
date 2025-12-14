import ActionBar from './ActionBar.jsx';
import TagPill from './TagPill.jsx';

export default {
  title: 'newCMS/ActionBar',
  component: ActionBar,
};

export const Default = {
  render: () => (
    <ActionBar
      primary={<button className="px-3 py-2 rounded-lg bg-blue-500 text-white text-sm">Action</button>}
      secondary={<button className="px-3 py-2 rounded-lg bg-white/10 text-slate-200 text-sm">Secondary</button>}
    >
      <TagPill label="Filtre actif" active />
    </ActionBar>
  ),
};
