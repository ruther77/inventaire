import { NavLink } from 'react-router-dom';
import {
  Gauge,
  ShoppingBag,
  Wallet,
  Utensils,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/', label: 'Cockpit', icon: Gauge },
  { to: '/operations', label: 'Ops', icon: ShoppingBag },
  { to: '/finances', label: 'Finance', icon: Wallet },
  { to: '/restaurant', label: 'Resto', icon: Utensils },
  { to: '/intelligence', label: 'Intel', icon: Brain },
];

export default function BottomNav() {
  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 border-t border-white/10 bg-slate-900/90 backdrop-blur-md">
      <div className="grid grid-cols-5 text-xs">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  'flex flex-col items-center justify-center gap-1 py-2 text-slate-400 transition',
                  isActive && 'text-white'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={clsx(
                      'flex h-10 w-10 items-center justify-center rounded-full border',
                      isActive
                        ? 'border-white/30 bg-white/10 text-white'
                        : 'border-white/5 bg-white/5'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
