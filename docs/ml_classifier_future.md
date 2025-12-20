# Classificateur ML (futur) pour les 14 catégories Épicerie

Objectif : proposer un classifieur robuste (et améliorable) pour catégoriser produits/transactions avec suggestion si confiance < 0,7, en utilisant les données `/releve` et la BDD `epicerie`.

## Données d’entrée
- Tables BDD : `produits` (nom, catégorie actuelle, prix_achat, fournisseur), `produits_price_history` (fournisseur, facture_date), `mouvements_stock` (source), `processed_invoices` (supplier, invoice_id).
- Fichiers `/releve` : libellés de lignes, montants, dates, fournisseurs.  
- Cible : 14 catégories Épicerie (mapping propre, ex: boissons, frais, épicerie salée, sucrée, hygiène, etc.).

## Features proposées
- Texte : `nom` produit, `libelle`/`description` des lignes, fournisseur, source (concaténés et normalisés).
- Numériques : montant HT/TTC, TVA, quantités, prix unitaire, saisonnalité (mois).
- Fournisseur : one-hot / embedding fournisseur (top N).
- Historique prix : dernier prix_achat, dispersion (écart-type).
- Contexte : canal d’achat (source mouvements), fréquence d’apparition.

## Modèle (recommandé)
- Backbone : modèle de langue FR (ex: CamemBERT) fine-tuné en classification 14 classes.
- Complément tabulaire : gradient boosting (LightGBM/XGBoost) sur features numériques + encodage texte TF-IDF pour baseline rapide.
- Fusion : soit single transformer (texte + valeurs concaténées en embedding), soit late-fusion (moyenne pondérée des logits transformer + GBDT).

## Pipeline
1) Prétraitement : nettoyage texte (minuscule, strip, accents), normalisation montants, encodage fournisseurs (top N + “other”).
2) Split : train/val/test stratifié par catégorie, groupe par produit/fournisseur pour éviter fuite.
3) Entraînement :
   - Baseline rapide : TF-IDF + LinearSVM/LogReg (pour itérer vite).
   - Modèle cible : CamemBERT fine-tuné (epochs courtes, early stopping), calibrage des probabilités (Platt/Temp scaling).
4) Seuils :
   - Prédiction haute confiance : prob >= 0,7 → auto-class.
   - Sinon : suggestions (top 3) et feedback utilisateur.
5) Active learning :
   - Collecter les corrections utilisateurs (feedback) et re-trainer périodiquement.
   - Prioriser les échantillons basse confiance / désaccords modèle vs. règles heuristiques.
6) Déploiement :
   - Export artefact (ONNX ou .pt) + dictionnaire encodage fournisseurs.
   - Endpoint `/ml/classify` → retourne {classe, proba, top_k}.
   - Logging des décisions pour monitoring.

## Évaluation
- Métriques : macro-F1, weighted-F1, confusion matrix par catégorie.
- Seuil 0,7 validé sur set de validation (calibrage).
- A/B test : comparer baseline TF-IDF vs. CamemBERT sur mêmes splits.

## Implémentation (pseudo-code)
```python
# Prétraitement texte
def preprocess(row):
    text = " ".join(filter(None, [
        row.get("nom"), row.get("libelle"), row.get("fournisseur"), row.get("source")
    ])).lower()
    return normalize_text(text)

# Inference (CamemBERT)
inputs = tokenizer(preprocess(row), return_tensors="pt", truncation=True, max_length=128)
with torch.no_grad():
    logits = model(**inputs).logits
probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
top = probs.argmax()
if probs[top] >= 0.7:
    decision = {"label": id2label[top], "confidence": float(probs[top]), "suggestions": []}
else:
    suggestions = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:3]
    decision = {
        "label": None,
        "confidence": float(probs[top]),
        "suggestions": [{"label": id2label[i], "p": float(probs[i])} for i in suggestions],
    }
```

## Boucle d’amélioration continue
- Stocker chaque prédiction + feedback dans une table `ml_classification_log` (classe prédite, confiance, correction).
- Re-entraîner mensuellement avec les corrections (et ajuster le seuil si besoin).
- Alertes si drift : baisse du F1 > X% sur un échantillon de contrôle.

## Livrables à prévoir
- Notebook d’entraînement + script `train_classifier.py`.
- Artefact modèle + tokenizer + mapping id2label.
- Tests unitaires (pipeline de prétraitement, calibration, top-k).
- Documentation d’API `/ml/classify` (contrat JSON, top_k, gestion du seuil). 
