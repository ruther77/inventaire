# Workflows n8n - Inventaire

Ce dossier contient les workflows n8n importes automatiquement au demarrage du conteneur.

## Workflows disponibles

### 1. inventaire-api-ia.json
**Assistant IA pour l'inventaire**

Combine l'API Inventaire avec Ollama pour analyser les donnees.

- Endpoint : `POST http://localhost:5678/webhook/analyse`
- Payload :
```json
{
  "endpoint": "/inventaire",
  "question": "Quelles priorites pour aujourd'hui ?",
  "user": "manager-restaurant"
}
```

### 2. bank-import-orchestrator.json
**Orchestrateur principal d'import bancaire**

- Endpoint : `POST http://localhost:5678/webhook/bank-import`
- Payload :
```json
{
  "bank_type": "bnp|lcl_noutam|lcl_incontournable|sumup",
  "account_id": 1
}
```

**Mapping des comptes:**
| bank_type | Account ID | Description |
|-----------|------------|-------------|
| `bnp` | 1 | BNP - Angele |
| `lcl_noutam` | 2 | LCL - Noutam |
| `lcl_incontournable` | 3 | LCL - L'Incontournable |
| `sumup` | 4 | SumUp - L'Incontournable |

### 3. sumup-import.json
**Import simplifie pour SumUp**

- Endpoint : `POST http://localhost:5678/webhook/import-sumup`
- Importe directement vers le compte SumUp (ID 4)

## Exemples d'utilisation

```bash
# Import releve BNP
curl -X POST http://localhost:5678/webhook/bank-import \
  -F "bank_type=bnp" \
  -F "file=@releve_bnp.pdf"

# Import releve SumUp (simplifie)
curl -X POST http://localhost:5678/webhook/import-sumup \
  -F "file=@sumup_releve.pdf"

# Import LCL Noutam
curl -X POST http://localhost:5678/webhook/bank-import \
  -F "bank_type=lcl_noutam" \
  -F "file=@releve_lcl.pdf"

# Analyse IA
curl -X POST http://localhost:5678/webhook/analyse \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/finance/accounts", "question": "Quel est le solde total?"}'
```

## Configuration

### Authentification n8n
- `N8N_BASIC_AUTH_USER` : utilisateur (defaut: admin)
- `N8N_BASIC_AUTH_PASSWORD` : mot de passe (defaut: changeme)
- `N8N_BASIC_AUTH_ACTIVE` : activer/desactiver (defaut: true)

### Permissions
Si erreurs de persistance :
```bash
chown -R 1000:1000 n8n_data
```

## Architecture

```
n8n (localhost:5678)
  |
  +-- /webhook/analyse --> API + Ollama --> Reponse IA
  |
  +-- /webhook/bank-import --> API /finance/bank-statements/import-pdf
  |
  +-- /webhook/import-sumup --> API (account_id=4)
```
