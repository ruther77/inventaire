/**
 * Exemple d'intégration du système de feedback de catégorisation
 * Phase 4 - CATÉGORISATION
 *
 * Ce composant montre comment:
 * 1. Afficher une transaction avec sa catégorie prédite
 * 2. Permettre à l'utilisateur de corriger la catégorie
 * 3. Enregistrer le feedback pour l'apprentissage ML
 * 4. Afficher les statistiques de feedback
 */

import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

// =============================================================================
// 1. Composant principal: Éditeur de catégorie avec feedback
// =============================================================================

export function TransactionCategoryEditor({ transaction, categories, onUpdate }) {
  const [selectedCategory, setSelectedCategory] = useState(transaction.category_id);
  const [saving, setSaving] = useState(false);

  const handleCategoryChange = async (newCategoryId) => {
    if (newCategoryId === transaction.category_id) {
      return; // Pas de changement
    }

    setSaving(true);

    try {
      // 1. Mettre à jour la catégorie de la transaction
      await fetch(`/api/finance/transactions/${transaction.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: newCategoryId })
      });

      // 2. Enregistrer le feedback pour l'apprentissage ML
      await fetch(`/api/finance/transactions/${transaction.id}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          actual_category_id: newCategoryId,
          predicted_category_id: transaction.category_id,
          confidence_score: transaction.category_confidence,
          correction_source: 'manual'
        })
      });

      setSelectedCategory(newCategoryId);
      toast.success('Catégorie mise à jour et feedback enregistré');

      if (onUpdate) {
        onUpdate({ ...transaction, category_id: newCategoryId });
      }
    } catch (error) {
      console.error('Error updating category:', error);
      toast.error('Erreur lors de la mise à jour de la catégorie');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="transaction-category-editor">
      <select
        value={selectedCategory || ''}
        onChange={(e) => handleCategoryChange(parseInt(e.target.value))}
        disabled={saving}
        className="category-select"
      >
        <option value="">-- Sélectionner une catégorie --</option>
        {categories.map(cat => (
          <option key={cat.id} value={cat.id}>
            {cat.name}
          </option>
        ))}
      </select>

      {transaction.category_confidence !== null && (
        <div className="confidence-indicator">
          <ConfidenceBar confidence={transaction.category_confidence} />
          <span className="confidence-text">
            {(transaction.category_confidence * 100).toFixed(0)}% confiance
          </span>
        </div>
      )}

      {saving && <span className="saving-indicator">Enregistrement...</span>}
    </div>
  );
}

// =============================================================================
// 2. Indicateur visuel de confiance
// =============================================================================

function ConfidenceBar({ confidence }) {
  const getColorClass = (conf) => {
    if (conf >= 0.9) return 'confidence-high';
    if (conf >= 0.7) return 'confidence-medium';
    return 'confidence-low';
  };

  return (
    <div className="confidence-bar">
      <div
        className={`confidence-fill ${getColorClass(confidence)}`}
        style={{ width: `${confidence * 100}%` }}
      />
    </div>
  );
}

// =============================================================================
// 3. Composant de statistiques de feedback
// =============================================================================

export function FeedbackStatsPanel() {
  const [stats, setStats] = useState(null);
  const [commonCorrections, setCommonCorrections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeedbackData();
  }, []);

  const loadFeedbackData = async () => {
    try {
      // Charger les stats globales
      const statsResponse = await fetch('/api/finance/categorization/feedback/stats');
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Charger les corrections communes
      const correctionsResponse = await fetch('/api/finance/categorization/feedback/common-corrections?limit=10');
      const correctionsData = await correctionsResponse.json();
      setCommonCorrections(correctionsData);
    } catch (error) {
      console.error('Error loading feedback data:', error);
      toast.error('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Chargement des statistiques...</div>;
  }

  if (!stats) {
    return <div>Aucune donnée disponible</div>;
  }

  return (
    <div className="feedback-stats-panel">
      <h2>Statistiques de Catégorisation</h2>

      {/* Stats globales */}
      <div className="stats-grid">
        <StatCard
          title="Total Corrections"
          value={stats.total_corrections}
          icon="🔄"
        />
        <StatCard
          title="Transactions Corrigées"
          value={stats.unique_transactions}
          icon="📝"
        />
        <StatCard
          title="Confiance Moyenne (Erreurs)"
          value={stats.avg_wrong_confidence ? `${(stats.avg_wrong_confidence * 100).toFixed(1)}%` : 'N/A'}
          icon="📊"
        />
        <StatCard
          title="Corrections Manuelles"
          value={stats.manual_corrections}
          icon="👤"
        />
      </div>

      {/* Corrections communes */}
      {commonCorrections.length > 0 && (
        <div className="common-corrections">
          <h3>Corrections les Plus Fréquentes</h3>
          <p className="help-text">
            Ces patterns peuvent être utilisés pour créer de nouvelles règles de catégorisation.
          </p>

          <table className="corrections-table">
            <thead>
              <tr>
                <th>Catégorie Prédite</th>
                <th>→</th>
                <th>Catégorie Correcte</th>
                <th>Occurrences</th>
                <th>Confiance Moy.</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {commonCorrections.map((correction, idx) => (
                <tr key={idx}>
                  <td>
                    <span className="category-badge category-predicted">
                      {correction.predicted_name || 'N/A'}
                    </span>
                  </td>
                  <td className="arrow">→</td>
                  <td>
                    <span className="category-badge category-actual">
                      {correction.actual_name}
                    </span>
                  </td>
                  <td className="count">{correction.correction_count}</td>
                  <td className="confidence">
                    {correction.avg_confidence ? `${(correction.avg_confidence * 100).toFixed(0)}%` : 'N/A'}
                  </td>
                  <td>
                    <button
                      className="btn-create-rule"
                      onClick={() => handleCreateRuleFromCorrection(correction)}
                    >
                      Créer une règle
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// 4. Composant de carte de statistique
// =============================================================================

function StatCard({ title, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
      </div>
    </div>
  );
}

// =============================================================================
// 5. Fonction pour créer une règle à partir d'une correction
// =============================================================================

async function handleCreateRuleFromCorrection(correction) {
  // Cette fonction pourrait ouvrir un modal pour créer une règle
  // basée sur le pattern de correction identifié
  const confirmed = window.confirm(
    `Voulez-vous créer une règle pour catégoriser automatiquement ` +
    `"${correction.predicted_name}" en "${correction.actual_name}"?\n\n` +
    `Cette correction a été faite ${correction.correction_count} fois.`
  );

  if (!confirmed) return;

  try {
    // Ouvrir un modal ou naviguer vers la page de création de règle
    // avec les données pré-remplies
    toast.info('Fonctionnalité à venir: Création automatique de règles');

    // Exemple de ce qui pourrait être fait:
    /*
    const response = await fetch('/api/finance/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: `Auto-règle: ${correction.predicted_name} → ${correction.actual_name}`,
        category_id: correction.actual_category_id,
        keywords: [], // À remplir par l'utilisateur
        is_active: true,
        priority: 100
      })
    });

    if (response.ok) {
      toast.success('Règle créée avec succès');
    }
    */
  } catch (error) {
    console.error('Error creating rule:', error);
    toast.error('Erreur lors de la création de la règle');
  }
}

// =============================================================================
// 6. Composant de batch correction avec feedback
// =============================================================================

export function BatchCategoryEditor({ transactions, categories, onUpdate }) {
  const [selectedTransactions, setSelectedTransactions] = useState([]);
  const [targetCategory, setTargetCategory] = useState('');
  const [saving, setSaving] = useState(false);

  const handleBatchCorrection = async () => {
    if (!targetCategory || selectedTransactions.length === 0) {
      toast.warning('Sélectionnez des transactions et une catégorie cible');
      return;
    }

    setSaving(true);

    try {
      // Mettre à jour toutes les transactions sélectionnées
      const updates = selectedTransactions.map(txId =>
        fetch(`/api/finance/transactions/${txId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category_id: parseInt(targetCategory) })
        })
      );

      await Promise.all(updates);

      // Enregistrer le feedback en masse
      const feedbacks = selectedTransactions.map(txId => {
        const transaction = transactions.find(t => t.id === txId);
        return fetch(`/api/finance/transactions/${txId}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            actual_category_id: parseInt(targetCategory),
            predicted_category_id: transaction?.category_id,
            confidence_score: transaction?.category_confidence,
            correction_source: 'bulk_action'
          })
        });
      });

      await Promise.all(feedbacks);

      toast.success(`${selectedTransactions.length} transactions mises à jour avec feedback`);
      setSelectedTransactions([]);

      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      console.error('Error in batch correction:', error);
      toast.error('Erreur lors de la correction en masse');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="batch-category-editor">
      <h3>Correction en Masse</h3>

      <div className="batch-controls">
        <div className="selection-info">
          {selectedTransactions.length} transaction(s) sélectionnée(s)
        </div>

        <select
          value={targetCategory}
          onChange={(e) => setTargetCategory(e.target.value)}
          className="category-select"
        >
          <option value="">-- Catégorie cible --</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>

        <button
          onClick={handleBatchCorrection}
          disabled={saving || selectedTransactions.length === 0 || !targetCategory}
          className="btn-batch-apply"
        >
          {saving ? 'Enregistrement...' : 'Appliquer la Correction'}
        </button>
      </div>

      <div className="transactions-list">
        {transactions.map(tx => (
          <label key={tx.id} className="transaction-checkbox">
            <input
              type="checkbox"
              checked={selectedTransactions.includes(tx.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedTransactions([...selectedTransactions, tx.id]);
                } else {
                  setSelectedTransactions(selectedTransactions.filter(id => id !== tx.id));
                }
              }}
            />
            <span className="transaction-label">
              {tx.libelle} - {tx.montant}€
              {tx.category_name && (
                <span className="current-category">({tx.category_name})</span>
              )}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// 7. Styles CSS (à ajouter dans votre fichier CSS)
// =============================================================================

const styles = `
.transaction-category-editor {
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.category-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-bar {
  width: 100px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.confidence-high { background: #10b981; }
.confidence-medium { background: #f59e0b; }
.confidence-low { background: #ef4444; }

.confidence-text {
  font-size: 12px;
  color: #666;
}

.feedback-stats-panel {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.stat-title {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.common-corrections {
  margin-top: 32px;
}

.corrections-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.corrections-table th {
  padding: 12px;
  text-align: left;
  background: #f3f4f6;
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.corrections-table td {
  padding: 12px;
  border-top: 1px solid #e5e7eb;
}

.category-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.category-predicted {
  background: #fef3c7;
  color: #92400e;
}

.category-actual {
  background: #d1fae5;
  color: #065f46;
}

.arrow {
  color: #9ca3af;
  font-size: 18px;
  text-align: center;
}

.btn-create-rule {
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-create-rule:hover {
  background: #2563eb;
}

.batch-category-editor {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.batch-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.selection-info {
  font-size: 14px;
  color: #6b7280;
}

.btn-batch-apply {
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-batch-apply:hover:not(:disabled) {
  background: #059669;
}

.btn-batch-apply:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transaction-checkbox {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.transaction-checkbox:hover {
  background: #f9fafb;
}

.transaction-label {
  font-size: 14px;
  color: #374151;
}

.current-category {
  margin-left: 8px;
  color: #6b7280;
  font-size: 13px;
}
`;

// Export styles pour documentation
export { styles as categorizationFeedbackStyles };
