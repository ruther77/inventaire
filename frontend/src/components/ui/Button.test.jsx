import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from './Button';

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('type', 'button');
  });

  it('applies primary variant styles by default', () => {
    render(<Button>Primary</Button>);
    const button = screen.getByRole('button');
    // Dark theme uses gradient instead of bg-slate-900
    expect(button.className).toContain('bg-gradient-to-r');
  });

  it('applies subtle variant styles', () => {
    render(<Button variant="subtle">Subtle</Button>);
    const button = screen.getByRole('button');
    // Dark theme uses bg-white/10 instead of bg-white
    expect(button.className).toContain('bg-white/10');
  });

  it('applies ghost variant styles', () => {
    render(<Button variant="ghost">Ghost</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-transparent');
  });

  it('applies brand variant styles', () => {
    render(<Button variant="brand">Brand</Button>);
    const button = screen.getByRole('button');
    // Dark theme uses gradient instead of bg-brand-600
    expect(button.className).toContain('bg-gradient-to-r');
  });

  it('applies md size by default', () => {
    render(<Button>Medium</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('px-5'); // md: px-5 py-2.5
  });

  it('applies lg size', () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('px-6'); // lg: px-6 py-3
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('can render as a custom component', () => {
    render(<Button as="a" href="/test">Link Button</Button>);
    const link = screen.getByRole('link', { name: /link button/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/test');
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('custom-class');
  });

  it('applies iconOnly styles', () => {
    render(<Button iconOnly>Icon</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('p-2');
  });

  it('sets submit type when specified', () => {
    render(<Button type="submit">Submit</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
  });
});
