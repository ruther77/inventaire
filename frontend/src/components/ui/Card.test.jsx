import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Card from './Card';

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders as section by default', () => {
    const { container } = render(<Card>Content</Card>);
    expect(container.querySelector('section')).toBeInTheDocument();
  });

  it('can render as a custom component', () => {
    const { container } = render(<Card as="div">Content</Card>);
    expect(container.querySelector('div')).toBeInTheDocument();
  });

  it('applies glass-panel class', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    expect(card.className).toContain('glass-panel');
  });

  it('applies default p-6 padding', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    expect(card.className).toContain('p-6');
  });

  it('applies custom padding', () => {
    const { container } = render(<Card padding="p-4">Content</Card>);
    const card = container.firstChild;
    expect(card.className).toContain('p-4');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const card = container.firstChild;
    expect(card.className).toContain('custom-class');
  });

  it('renders nested elements', () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Description</p>
      </Card>
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
  });
});
