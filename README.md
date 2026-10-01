# RetailPulse 360

Plateforme analytique ELT pour une entreprise retail omnicanale marocaine, construite comme projet portfolio de Data Engineering.

![CI](https://github.com/medsaa0/retailpulse-360/actions/workflows/ci.yml/badge.svg)

## Le problème métier

Une entreprise retail omnicanale (web, magasins, livraisons) a ses données éclatées entre un ERP, une base transactionnelle, des exports CSV et une API de livraison. Résultat : rapports lents, chiffres incohérents entre services, aucune vue fiable sur les ventes, les ruptures de stock ou la rentabilité par canal.

RetailPulse 360 centralise ces sources dans un entrepôt de données unique, modélisé en étoile, avec historisation des changements (SCD Type 2), tests de qualité automatisés et orchestration planifiée.

## Architecture

```
PostgreSQL ─┐
CSV ERP     ├─► Ingestion Python ─► MinIO (raw, Parquet) ─► Snowflake RAW
API livraison┘                                                    │
                                                                    ▼
                                                          dbt (staging → snapshots → marts)
                                                                    │
                                   ┌────────────────────────────────┤
                                   ▼                                ▼
                            Power BI                          dbt docs

                    Airflow orchestre l'ensemble du pipeline.
                    GitHub Actions valide le code à chaque push.
```

## Stack technique

| Domaine | Outil |
|---|---|
| Langage | Python 3.12 |
| Orchestration | Apache Airflow |
| Stockage brut | MinIO (S3-compatible) |
| Entrepôt de données | Snowflake |
| Transformation | dbt Core |
| Sources simulées | PostgreSQL, CSV, API FastAPI, générateur Faker |
| Tests | Pytest, dbt tests, dbt_utils |
| CI/CD | GitHub Actions |
| Conteneurisation | Docker Compose |

## Modèle de données

Modèle en étoile avec historisation SCD Type 2 sur les dimensions client et produit.

**Faits :** `fct_orders`, `fct_order_items`
**Dimensions :** `dim_customer` (SCD2), `dim_product` (SCD2), `dim_store`, `dim_date`

Détails complets : [`docs/architecture/modele_dimensionnel.md`](docs/architecture/modele_dimensionnel.md)

## Démarrage local

### Prérequis

- Docker Desktop
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)
- Un compte Snowflake (trial gratuit suffisant)

### 1. Cloner et installer

```bash
git clone https://github.com/medsaa0/retailpulse-360.git
cd retailpulse-360
uv sync --all-groups
```

### 2. Configurer l'environnement

Copie `.env.example` vers `.env` et renseigne tes identifiants Postgres/MinIO/Snowflake.

L'authentification Snowflake se fait par clé RSA (pas de mot de passe), voir la section *Authentification Snowflake* ci-dessous.

### 3. Démarrer l'infrastructure locale

```bash
docker compose up -d
```

Démarre PostgreSQL, MinIO, et Airflow (webserver sur `localhost:8080`, identifiants `admin`/`admin`).

### 4. Démarrer l'API de livraison simulée

```bash
uv run uvicorn delivery_api.main:app --host 127.0.0.1 --port 8002
```

### 5. Initialiser Snowflake (une seule fois)

```bash
uv run python -m scripts.bootstrap_snowflake
```

### 6. Lancer le pipeline complet

```bash
uv run python -m ingestion.run_ingestion
uv run python -m scripts.load_raw_to_snowflake
cd dbt_retailpulse
uv run dbt deps
uv run dbt run --select staging
uv run dbt snapshot
uv run dbt run --select marts
uv run dbt test
cd ..
uv run python -m scripts.reconcile_counts
```

Ou via Airflow : ouvre `localhost:8080`, déclenche le DAG `retailpulse_elt_pipeline`.

## Authentification Snowflake (clé RSA, pas de mot de passe)

Les comptes Snowflake imposent le MFA sur les connexions par mot de passe, incompatible avec un pipeline automatisé. Ce projet utilise l'authentification par paire de clés :

```bash
uv run python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

with open('snowflake_rsa_key.p8', 'wb') as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open('snowflake_rsa_key.pub', 'wb') as f:
    f.write(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
"
```

Puis associe la clé publique à ton utilisateur dans Snowsight :
```sql
ALTER USER <ton_user> SET RSA_PUBLIC_KEY='<contenu_de_snowflake_rsa_key.pub_sans_BEGIN_END>';
```

## Tests

```bash
uv run pytest
uv run ruff check .
```

## État d'avancement

| Phase | Statut |
|---|---|
| Fondations (Git, Docker, CI) | ✅ |
| Conception métier et modèle dimensionnel | ✅ |
| Génération et ingestion (idempotente) | ✅ |
| Chargement Snowflake RAW | ✅ |
| Transformation dbt (staging, SCD2, marts) | ✅ |
| Orchestration Airflow | ✅ |
| Qualité et observabilité | 🚧 |
| Dashboard Power BI | ⏳ |
| CI/CD GitHub Actions | ✅ |

## Limites connues et pistes de production

- L'API de livraison tourne en dehors de Docker Compose ; à conteneuriser pour un vrai démarrage en une commande.
- Pas de gestion des suppressions physiques côté sources (extraction incrémentale par `updated_at` uniquement).
- Authentification par clé RSA stockée en fichier local ; en production, utiliser un secret manager dédié.