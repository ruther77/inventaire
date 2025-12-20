# Schemas d’architecture (applicative, reseau, securite)

## 1. Architecture applicative
```mermaid
flowchart LR
  UI[SPA React] --> API[FastAPI]
  API --> DB[(PostgreSQL)]
  API --> Cache[(Redis)]
  API --> Traitements[Traitements asynchrones]
  Traitements --> DB
  API --> Files[Exports CSV/PDF]
```

## 2. Architecture reseau (vue simplifiee)
```mermaid
flowchart TB
  Internet --> LB[Reverse proxy / Equilibreur de charge]
  LB --> App[Interface SPA]
  LB --> API[API backend]
  API --> DB[(PostgreSQL)]
  API --> Traitements[Traitements]
  API --> Cache[(Redis)]
```

## 2.1 Arbre reseau (ASCII)
```
Internet
`-- Reverse proxy / LB
    |-- Interface SPA
    `-- API FastAPI
        |-- PostgreSQL
        `-- Redis
```

## 3. Architecture securite
- TLS termine au reverse proxy.
- OAuth2/JWT sur l’API.
- RBAC par module.
- Isolation logique par tenant.
- Journal d’audit.

```mermaid
flowchart LR
  User[Utilisateur] --> TLS[HTTPS]
  TLS --> API[FastAPI]
  API --> Auth[RBAC + JWT]
  API --> DB[(PostgreSQL)]
```

## 3.1 Zones de securite (ASCII)
```
[Zone publique]
  |
  v
[Reverse proxy / TLS]
  |
  v
[Zone applicative]
  |-- API FastAPI
  `-- Traitements
  |
  v
[Zone donnees]
  |-- PostgreSQL
  `-- Redis
```

## 4. Diagramme de flux securise (DFD)
```mermaid
flowchart LR
  User((Utilisateur)) -->|HTTPS| Proxy[Reverse proxy]
  Proxy -->|JWT| API[API FastAPI]
  API -->|SQL| DB[(PostgreSQL)]
  API -->|Cache| Cache[(Redis)]
  API -->|Taches| Traitement[Traitements asynchrones]
  Traitement --> DB
```
