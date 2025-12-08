## Modules legacy (Streamlit / PHP)

Les anciens clients (Streamlit, mini-PHP) ont été déplacés sous `legacy/` afin de ne
pas polluer la nouvelle API FastAPI + SPA React.

| Dossier | Description | Statut |
| --- | --- | --- |
| `legacy/streamlit` | Ancienne appli Streamlit (scanner, extraction, maintenance). | Lecture seule, non buildée. |
| `legacy/php` | Restes du dashboard PHP/HTML historique. | Non supporté, gardé pour référence. |

Ces sources ne sont **plus** consommées par le pipeline actuel : elles servent uniquement
de documentation (structures SQL, templates). Si besoin de fonctionnalités manquantes,
porter le flux côté `backend/` ou `frontend/` puis supprimer définitivement la portion
legacy correspondante.

> Astuce : ajoute `legacy/` à ton IDE comme dossier exclu pour éviter d’indexer les
> anciens assets (CSS/JS).***
