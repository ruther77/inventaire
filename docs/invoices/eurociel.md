EUROCIEL (NOUTAM / L'INCONTOURNABLE)
====================================

- Sources : PDF dans `EUROCIEL/` (`Documents 23 ET 24 NOUTAM.pdf`, `Documents 24 ET 25 L INCONTOURNABLE.pdf`, etc.).
- Format : lignes `Qté | PU | Montant | Code + Désignation`. TVA déduite via la section récap (5,5 % partout dans les échantillons).
- Identifiants facture : `FA`/`AV` collés à la date (`05/11/25FA20296730`).

Extraction / import
-------------------

- `supplier_hint` à utiliser : `eurociel` (détection auto si le texte contient "eurociel").
- Exemple d'import complet (catalogue + mouvements) :
  ```
  python -m scripts.import_invoice_files EUROCIEL \
    --supplier EUROCIEL \
    --tenant epicerie \
    --username import_bot \
    --margin 40 \
    --initialize-stock
  ```
- Le parseur retourne `prix_achat`, `qte_init`, `tva` (5,5 par défaut), `invoice_id`/`facture_date`. Les libellés sont nettoyés des numéros de ligne/poids en fin de chaîne.

Catalogue fournisseur
---------------------

- Le PDF `EUROCIEL/CATALOGUE  EURO CIEL.pdf` peut être converti en liste de libellés exploitable via :
  ```
  python -m scripts.eurociel_catalogue_to_csv --pdf "EUROCIEL/CATALOGUE  EURO CIEL.pdf"
  ```
  Cela génère `data/eurociel_catalogue_candidates.csv` (libellés dédoublonnés, à compléter avec prix/poids).
- Une fois le CSV nettoyé/complété, on peut importer les produits avec `core.products_loader.load_products_from_df`
  ou en passant le CSV dans l'interface admin habituelle.
