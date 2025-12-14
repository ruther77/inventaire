import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';

export default function MegaSectionNav({ sections, activeItemId, onSelect }) {
  const [openSectionId, setOpenSectionId] = useState(null);
  const [isPinned, setIsPinned] = useState(false);
  const navRef = useRef(null);
  const activeSection = useMemo(() => {
    return (
      sections.find((section) =>
        section.groups?.some((group) => group.items?.some((item) => item.id === activeItemId)),
      ) || sections[0]
    );
  }, [sections, activeItemId]);

  const handleSectionFocus = (sectionId) => {
    setOpenSectionId(sectionId);
  };

  const handleSectionSelect = (section) => {
    const defaultItem = section?.groups?.[0]?.items?.[0];
    setOpenSectionId(section.id);
    setIsPinned(true);
    if (defaultItem) {
      onSelect?.(defaultItem.id);
    }
  };

  const handleItemSelect = (itemId) => {
    onSelect?.(itemId);
    setIsPinned(false);
    setOpenSectionId(null);
  };

  const handleMouseLeave = (event) => {
    if (isPinned) return;
    if (event.currentTarget.contains(event.relatedTarget)) {
      return;
    }
    setOpenSectionId(null);
  };

  const handleNavBlur = (event) => {
    if (isPinned) return;
    if (!event.currentTarget.contains(event.relatedTarget)) {
      setOpenSectionId(null);
    }
  };

  useEffect(() => {
    const handleDocumentPointer = (event) => {
      if (!navRef.current) return;
      if (!navRef.current.contains(event.target)) {
        setIsPinned(false);
        setOpenSectionId(null);
      }
    };
    document.addEventListener('pointerdown', handleDocumentPointer);
    return () => document.removeEventListener('pointerdown', handleDocumentPointer);
  }, []);

  const openedSection = sections.find((section) => section.id === openSectionId);

  return (
    <div
      ref={navRef}
      className="relative hidden flex-col gap-3 lg:flex"
      onMouseLeave={handleMouseLeave}
      onBlur={handleNavBlur}
    >
      <ul className="flex items-center gap-6 text-sm font-semibold uppercase tracking-[0.3em] text-slate-200">
        {sections.map((section) => (
          <li key={section.id}>
            <button
              type="button"
              onMouseEnter={() => handleSectionFocus(section.id)}
              onFocus={() => handleSectionFocus(section.id)}
              onClick={() => handleSectionSelect(section)}
              className={clsx(
                'px-2 py-1 transition-colors focus:outline-none',
                section.id === activeSection?.id ? 'text-white' : 'hover:text-slate-100',
              )}
            >
              {section.label}
            </button>
          </li>
        ))}
      </ul>
      {openedSection && (
        <div className="absolute left-0 right-0 top-full z-30 mt-3 rounded-3xl border border-white/10 bg-slate-900/95 p-8 shadow-2xl backdrop-blur">
          <div className="grid gap-6 lg:grid-cols-3">
            {openedSection.groups?.map((group) => (
              <div key={group.title}>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-300">{group.title}</p>
                <ul className="mt-3 flex flex-col gap-2">
                  {group.items?.map((item) => {
                    const isActive = item.id === activeItemId;
                    return (
                      <li key={item.id}>
                        <button
                          type="button"
                          className={clsx(
                            'w-full rounded-2xl border px-3 py-2 text-left transition focus:outline-none',
                            isActive
                              ? 'border-brand-400 bg-brand-500/10 text-white shadow'
                              : 'border-transparent text-slate-200 hover:border-white/10 hover:bg-white/5',
                          )}
                          onClick={() => handleItemSelect(item.id)}
                        >
                          <p className="text-sm font-semibold">{item.label}</p>
                          {item.description && <p className="text-sm text-slate-300">{item.description}</p>}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
