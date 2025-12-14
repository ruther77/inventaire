# Workflow n8n : Inventaire API + IA locale

Ce dossier contient le workflow `inventaire-api-ia.json` importé automatiquement au démarrage du conteneur `n8n`.

## Utilisation
- Lancer `docker compose up n8n ollama api` (ou l'ensemble des services) pour démarrer l'API, Ollama et n8n.
- Endpoint d'entrée : `POST http://localhost:5678/webhook/analyse`
- Payload recommandé :

```json
{
  "endpoint": "/inventaire",   // chemin API à appeler sur le service `api`
  "question": "Quelles priorités pour aujourd'hui ?",
  "user": "manager-restaurant"
}
```

## Sécurité & configuration
- Authentification basique n8n activée par défaut. Surcharger via variables d'environnement :
  - `N8N_BASIC_AUTH_USER`
  - `N8N_BASIC_AUTH_PASSWORD`
  - désactiver via `N8N_BASIC_AUTH_ACTIVE=false` (déconseillé).
- Vérifier les droits d'écriture du volume `n8n_data` pour l'utilisateur `node` dans le conteneur si des erreurs de persistance apparaissent (`chown -R 1000:1000 n8n_data`).

## Comportement du workflow
1. Valide/sanétise le `endpoint` et limite la question à 600 caractères.
2. Appelle l'API interne `http://api:8000{endpoint}` (tolère les codes non-2xx).
3. Fusionne la question + réponse API puis construit un prompt concis (sections Analyse + Actions).
4. Envoie le prompt à Ollama (modèle `llama3.1`) et retourne un JSON `{ answer, endpoint, apiStatus, model, generatedAt }` en réponse HTTP.
