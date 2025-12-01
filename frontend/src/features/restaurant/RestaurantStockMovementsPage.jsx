import StockMovementsPage from '../stock/StockMovementsPage.jsx';

// Proxy pour réutiliser la page mouvements en mode restaurant.
export default function RestaurantStockMovementsPage() {
  return <StockMovementsPage context="restaurant" />;
}
