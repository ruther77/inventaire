# Planification du job `generate_capital_snapshot.py`

Ce script (dans `scripts/generate_capital_snapshot.py`) agrémente quotidiennement la table `capital_snapshot` à partir des derniers prix connus et des relevés bancaires. Voici comment le planifier sans toucher aux modules productifs :

## 1. Prérequis
- Environnement Python activé (`.venv`) avec les dépendances (`requirements.txt`).
- Base PostgreSQL accessible (même queue, variables `.env` renseignées).
- Migration `c1d2f3_price_snapshot` appliquée.

## 2. Cron / système Unix
```cron
0 2 * * * cd /chemin/vers/inventaire-epicerienew && source .venv/bin/activate && python scripts/generate_capital_snapshot.py >> logs/capital_snapshot.log 2>&1
```
Ce cron s’exécute tous les jours à 2h du matin (heure locale). Adapte le chemin et l’heure selon ton planning. Les logs peuvent être conservés pour audit.

## 3. Alternative systemd (Linux)
Créer `/etc/systemd/system/capital-snapshot.service` :
```ini
[Unit]
Description=Snapshot capital quotidien
After=network.target

[Service]
WorkingDirectory=/chemin/vers/inventaire-epicerienew
ExecStart=/bin/bash -lc 'source .venv/bin/activate && python scripts/generate_capital_snapshot.py'
User=tu_user
```
Puis `/etc/systemd/system/capital-snapshot.timer` :
```ini
[Unit]
Description=Timer quotidien du snapshot capital

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```
Active la timer avec `sudo systemctl enable --now capital-snapshot.timer`.

## 4. Monitoring
- Vérifier `capital_snapshot` après chaque run (`SELECT * FROM capital_snapshot ORDER BY snapshot_date DESC LIMIT 5`).
- Surveiller `logs/capital_snapshot.log` ou `journalctl -u capital-snapshot`.
- En bonus : `scripts/check_capital_snapshot.sh` (exécutable) affiche les 20 dernières lignes de log et les derniers snapshots ; utile pour valider après chaque exécution.

Après coup, la page “Portefeuille” et l’endpoint `/capital/overview` auront des données fraîches chaque matin.
