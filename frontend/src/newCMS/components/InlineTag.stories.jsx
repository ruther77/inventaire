import InlineTag from './InlineTag.jsx';

export default {
  title: 'newCMS/InlineTag',
  component: InlineTag,
};

export const Default = {
  args: { label: 'INFO', tone: 'info' },
};

export const Danger = {
  args: { label: 'CRITICAL', tone: 'danger' },
};
