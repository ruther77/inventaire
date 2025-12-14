import FilterBar from './FilterBar.jsx';
import TagPill from './TagPill.jsx';

export default {
  title: 'newCMS/FilterBar',
  component: FilterBar,
};

export const Default = {
  render: () => (
    <FilterBar
      filters={[{ active: true }, { active: false }]}
      onClear={() => {}}
    >
      <TagPill label="Critique" active />
      <TagPill label="Alerte" />
      <TagPill label="Info" />
    </FilterBar>
  ),
};
