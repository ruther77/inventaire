import clsx from 'clsx';

export default function Card({
  as: Component = 'section',
  className,
  children,
  padding = 'p-6',
}) {
  return (
    <Component className={clsx('glass-panel', padding, className)}>
      {children}
    </Component>
  );
}
