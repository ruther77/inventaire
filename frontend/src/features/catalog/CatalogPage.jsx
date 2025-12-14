/**
 * CatalogPage - Vue catalogue Next-Gen "Inline Everything"
 * Raccroche la démo intelligente (SmartTable + Drawer) pour refléter le scénario 3.3.
 */

import CatalogSmartDemo from './CatalogSmartDemo.jsx';

export default function CatalogPage({ embedded = false }) {
  return <CatalogSmartDemo embedded={embedded} />;
}
