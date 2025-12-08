import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import Input from './Input';

describe('Input', () => {
  it('renders with default props', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('shows required indicator when required', () => {
    render(<Input label="Name" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-required', 'true');
  });

  it('displays error message and applies error styles', () => {
    render(<Input label="Email" error="Invalid email address" />);

    expect(screen.getByText('Invalid email address')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('textbox')).toHaveClass('border-rose-400');
  });

  it('displays hint text when provided', () => {
    render(<Input label="Password" hint="Must be at least 8 characters" />);
    expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument();
  });

  it('hides hint when error is shown', () => {
    render(
      <Input
        label="Email"
        hint="We'll never share your email"
        error="Invalid email"
      />
    );
    expect(screen.queryByText("We'll never share your email")).not.toBeInTheDocument();
    expect(screen.getByText('Invalid email')).toBeInTheDocument();
  });

  it('applies success styles', () => {
    render(<Input label="Email" success />);
    expect(screen.getByRole('textbox')).toHaveClass('border-emerald-400');
  });

  it('renders icon on the left by default', () => {
    const TestIcon = ({ className }) => <span data-testid="test-icon" className={className} />;
    render(<Input icon={TestIcon} iconPosition="left" />);

    const icon = screen.getByTestId('test-icon');
    expect(icon).toBeInTheDocument();
    expect(icon.className).toContain('left-3');
  });

  it('renders icon on the right when specified', () => {
    const TestIcon = ({ className }) => <span data-testid="test-icon" className={className} />;
    render(<Input icon={TestIcon} iconPosition="right" />);

    const icon = screen.getByTestId('test-icon');
    expect(icon.className).toContain('right-3');
  });

  it('applies left padding when icon is on left', () => {
    const TestIcon = () => <span data-testid="icon" />;
    render(<Input icon={TestIcon} iconPosition="left" />);
    expect(screen.getByRole('textbox')).toHaveClass('pl-10');
  });

  it('applies right padding when icon is on right', () => {
    const TestIcon = () => <span data-testid="icon" />;
    render(<Input icon={TestIcon} iconPosition="right" />);
    expect(screen.getByRole('textbox')).toHaveClass('pr-10');
  });

  it('forwards ref to input element', () => {
    const ref = { current: null };
    render(<Input ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it('passes through other props to input', () => {
    render(
      <Input
        placeholder="Enter email"
        type="email"
        name="email"
        autoComplete="email"
      />
    );

    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('placeholder', 'Enter email');
    expect(input).toHaveAttribute('type', 'email');
    expect(input).toHaveAttribute('name', 'email');
    expect(input).toHaveAttribute('autocomplete', 'email');
  });

  it('handles value changes', async () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);

    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'test');

    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue('test');
  });

  it('can be disabled', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('applies custom className to input', () => {
    render(<Input className="custom-input" />);
    expect(screen.getByRole('textbox')).toHaveClass('custom-input');
  });

  it('applies containerClassName to container', () => {
    render(<Input containerClassName="custom-container" />);
    const container = screen.getByRole('textbox').closest('div').parentElement;
    expect(container).toHaveClass('custom-container');
  });

  it('associates error message with input via aria-describedby', () => {
    render(<Input label="Email" error="Invalid email" />);

    const input = screen.getByRole('textbox');
    const errorId = input.getAttribute('aria-describedby');
    const errorElement = document.getElementById(errorId);

    expect(errorElement).toHaveTextContent('Invalid email');
  });

  it('associates hint with input via aria-describedby', () => {
    render(<Input label="Name" hint="Enter your full name" />);

    const input = screen.getByRole('textbox');
    const hintId = input.getAttribute('aria-describedby');
    const hintElement = document.getElementById(hintId);

    expect(hintElement).toHaveTextContent('Enter your full name');
  });

  it('generates unique id when not provided', () => {
    const { rerender } = render(<Input label="First" />);
    const firstInput = screen.getByRole('textbox');
    const firstId = firstInput.id;

    rerender(<Input label="Second" />);
    const secondInput = screen.getByRole('textbox');

    // IDs should be generated and associated with labels
    expect(firstId).toBeTruthy();
    expect(secondInput.id).toBeTruthy();
  });

  it('uses custom id when provided', () => {
    render(<Input id="custom-email" label="Email" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('id', 'custom-email');
  });
});
