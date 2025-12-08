import Button from './Button';

export default {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'subtle', 'ghost', 'brand'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['md', 'lg'],
      description: 'Button size',
    },
    iconOnly: {
      control: 'boolean',
      description: 'Compact mode for icon-only buttons',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
  },
};

export const Primary = {
  args: {
    children: 'Primary Button',
    variant: 'primary',
  },
};

export const Subtle = {
  args: {
    children: 'Subtle Button',
    variant: 'subtle',
  },
};

export const Ghost = {
  args: {
    children: 'Ghost Button',
    variant: 'ghost',
  },
};

export const Brand = {
  args: {
    children: 'Brand Button',
    variant: 'brand',
  },
};

export const Large = {
  args: {
    children: 'Large Button',
    size: 'lg',
  },
};

export const IconOnly = {
  args: {
    children: '+',
    iconOnly: true,
  },
};

export const AsLink = {
  args: {
    children: 'Link Button',
    as: 'a',
    href: '#',
  },
};

export const AllVariants = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <Button variant="primary">Primary</Button>
        <Button variant="subtle">Subtle</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="brand">Brand</Button>
      </div>
      <div className="flex gap-2">
        <Button size="md">Medium</Button>
        <Button size="lg">Large</Button>
      </div>
    </div>
  ),
};
