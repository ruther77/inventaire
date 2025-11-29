import { describe, it, expect } from 'vitest';
import { aggregateTimeline, buildCategoryBuckets } from './banking.js';

const sampleTransactions = [
  { date: '2024-07-01', mois: '2024-07', type: 'Entrée', montant: 100 },
  { date: '2024-07-02', mois: '2024-07', type: 'Sortie', montant: 40, categorie: 'Charges fixes' },
  { date: '2024-07-08', mois: '2024-07', type: 'Sortie', montant: 10, categorie: 'Charges fixes' },
  { date: '2024-08-03', mois: '2024-08', type: 'Entrée', montant: 50 },
  { date: '2024-08-03', mois: '2024-08', type: 'Sortie', montant: 20, categorie: 'Fournisseur' },
];

describe('aggregateTimeline', () => {
  it('agrège par mois avec calcul net', () => {
    const result = aggregateTimeline(sampleTransactions, 'monthly');
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual(
      expect.objectContaining({
        mois: '2024-07',
        entrees: 100,
        sorties: 50,
        net: 50,
      }),
    );
  });

  it('agrège par jour avec tri chronologique', () => {
    const result = aggregateTimeline(sampleTransactions, 'daily');
    expect(result[0].jour).toBe('2024-07-01');
    expect(result.at(-1).jour).toBe('2024-08-03');
  });
});

describe('buildCategoryBuckets', () => {
  it('cumule les sorties par période et catégorie', () => {
    const buckets = buildCategoryBuckets(sampleTransactions, 'monthly');
    const july = buckets.get('2024-07');
    expect(july['Charges fixes']).toBe(50);
    const august = buckets.get('2024-08');
    expect(august.Fournisseur).toBe(20);
  });
});
