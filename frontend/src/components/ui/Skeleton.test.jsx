import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  Skeleton,
  SkeletonText,
  SkeletonCircle,
  MetricCardSkeleton,
  CardSkeleton,
  TableRowSkeleton,
  TableSkeleton,
  ListItemSkeleton,
  ListSkeleton,
  ChartSkeleton,
  ProductCardSkeleton,
  FormFieldSkeleton,
} from './Skeleton';

describe('Skeleton', () => {
  it('renders with base animation class', () => {
    render(<Skeleton data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('animate-pulse');
    expect(skeleton).toHaveClass('bg-slate-200');
    expect(skeleton).toHaveClass('rounded');
  });

  it('applies custom className', () => {
    render(<Skeleton className="h-4 w-full" data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('h-4');
    expect(skeleton).toHaveClass('w-full');
  });

  it('passes through additional props', () => {
    render(<Skeleton data-testid="skeleton" aria-hidden="true" />);
    expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-hidden', 'true');
  });
});

describe('SkeletonText', () => {
  it('renders single line by default', () => {
    const { container } = render(<SkeletonText />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(1);
  });

  it('renders multiple lines', () => {
    const { container } = render(<SkeletonText lines={3} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3);
  });

  it('applies shorter width to last line when multiple lines', () => {
    const { container } = render(<SkeletonText lines={3} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    const lastLine = skeletons[2];
    expect(lastLine).toHaveClass('w-3/4');
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonText className="my-4" />);
    expect(container.firstChild).toHaveClass('my-4');
  });
});

describe('SkeletonCircle', () => {
  it('renders with medium size by default', () => {
    const { container } = render(<SkeletonCircle />);
    const circle = container.querySelector('.animate-pulse');
    expect(circle).toHaveClass('h-12');
    expect(circle).toHaveClass('w-12');
    expect(circle).toHaveClass('rounded-full');
  });

  it('renders small size', () => {
    const { container } = render(<SkeletonCircle size="sm" />);
    const circle = container.querySelector('.animate-pulse');
    expect(circle).toHaveClass('h-8');
    expect(circle).toHaveClass('w-8');
  });

  it('renders large size', () => {
    const { container } = render(<SkeletonCircle size="lg" />);
    const circle = container.querySelector('.animate-pulse');
    expect(circle).toHaveClass('h-16');
    expect(circle).toHaveClass('w-16');
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonCircle className="mx-auto" />);
    const circle = container.querySelector('.animate-pulse');
    expect(circle).toHaveClass('mx-auto');
  });
});

describe('MetricCardSkeleton', () => {
  it('renders with metric class', () => {
    const { container } = render(<MetricCardSkeleton />);
    expect(container.firstChild).toHaveClass('metric');
  });

  it('renders multiple skeleton elements', () => {
    const { container } = render(<MetricCardSkeleton />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(1);
  });

  it('applies custom className', () => {
    const { container } = render(<MetricCardSkeleton className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});

describe('CardSkeleton', () => {
  it('renders with glass-panel class', () => {
    const { container } = render(<CardSkeleton />);
    expect(container.firstChild).toHaveClass('glass-panel');
  });

  it('applies custom className', () => {
    const { container } = render(<CardSkeleton className="my-8" />);
    expect(container.firstChild).toHaveClass('my-8');
  });
});

describe('TableRowSkeleton', () => {
  it('renders 4 columns by default', () => {
    const { container } = render(<TableRowSkeleton />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(4);
  });

  it('renders specified number of columns', () => {
    const { container } = render(<TableRowSkeleton columns={6} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(6);
  });

  it('applies custom className', () => {
    const { container } = render(<TableRowSkeleton className="border-b" />);
    expect(container.firstChild).toHaveClass('border-b');
  });
});

describe('TableSkeleton', () => {
  it('renders 5 rows with 4 columns by default', () => {
    const { container } = render(<TableSkeleton />);
    const rows = container.querySelectorAll('.flex.items-center.gap-4');
    expect(rows).toHaveLength(5);
  });

  it('renders specified number of rows', () => {
    const { container } = render(<TableSkeleton rows={3} />);
    const rows = container.querySelectorAll('.flex.items-center.gap-4');
    expect(rows).toHaveLength(3);
  });

  it('applies custom className', () => {
    const { container } = render(<TableSkeleton className="mt-4" />);
    expect(container.firstChild).toHaveClass('mt-4');
  });
});

describe('ListItemSkeleton', () => {
  it('renders with border', () => {
    const { container } = render(<ListItemSkeleton />);
    expect(container.firstChild).toHaveClass('border');
    expect(container.firstChild).toHaveClass('rounded-2xl');
  });

  it('applies custom className', () => {
    const { container } = render(<ListItemSkeleton className="mb-2" />);
    expect(container.firstChild).toHaveClass('mb-2');
  });
});

describe('ListSkeleton', () => {
  it('renders 5 items by default', () => {
    const { container } = render(<ListSkeleton />);
    const items = container.querySelectorAll('.rounded-2xl.border');
    expect(items).toHaveLength(5);
  });

  it('renders specified number of items', () => {
    const { container } = render(<ListSkeleton items={3} />);
    const items = container.querySelectorAll('.rounded-2xl.border');
    expect(items).toHaveLength(3);
  });

  it('applies custom className', () => {
    const { container } = render(<ListSkeleton className="my-4" />);
    expect(container.firstChild).toHaveClass('my-4');
  });
});

describe('ChartSkeleton', () => {
  it('renders bar-like elements', () => {
    const { container } = render(<ChartSkeleton />);
    const bars = container.querySelectorAll('.animate-pulse.flex-1');
    expect(bars.length).toBeGreaterThan(0);
  });

  it('applies custom className', () => {
    const { container } = render(<ChartSkeleton className="h-80" />);
    expect(container.firstChild).toHaveClass('h-80');
  });
});

describe('ProductCardSkeleton', () => {
  it('renders with rounded border', () => {
    const { container } = render(<ProductCardSkeleton />);
    expect(container.firstChild).toHaveClass('rounded-2xl');
    expect(container.firstChild).toHaveClass('border');
  });

  it('renders image placeholder', () => {
    const { container } = render(<ProductCardSkeleton />);
    const imagePlaceholder = container.querySelector('.h-48');
    expect(imagePlaceholder).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<ProductCardSkeleton className="shadow-lg" />);
    expect(container.firstChild).toHaveClass('shadow-lg');
  });
});

describe('FormFieldSkeleton', () => {
  it('renders label and input placeholders', () => {
    const { container } = render(<FormFieldSkeleton />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(2);
  });

  it('renders input with rounded-2xl', () => {
    const { container } = render(<FormFieldSkeleton />);
    const input = container.querySelector('.rounded-2xl');
    expect(input).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<FormFieldSkeleton className="mb-4" />);
    expect(container.firstChild).toHaveClass('mb-4');
  });
});
