# Runbook — Diagnostic des pannes RetailPulse 360

Ce document explique comment diagnostiquer et résoudre les pannes rencontrées sur ce pipeline. Chaque entrée suit le même format : **symptôme → cause → diagnostic → solution**.

## Méthode générale de diagnostic

1. Identifier la couche concernée : réseau, authentification, code applicatif, ou logique métier.
2. Lire le traceback complet, pas seulement la dernière ligne — la cause racine est souvent plusieurs niveaux au-dessus de l'erreur finale affichée.
3. Isoler : tester le composant en échec seul, hors du pipeline complet (ex: une connexion Snowflake isolée avant de relancer tout un DAG).
4. Corriger une seule chose à la fois, puis retester.

## Panne : `ImportError: cannot import name 'URL' from 'sqlalchemy'`

**Contexte :** survient uniquement dans le conteneur Airflow, jamais en local.

**Cause :** Airflow 2.10.5 impose en interne SQLAlchemy 1.4 pour son propre fonctionnement (metastore), alors que le projet utilise SQLAlchemy 2.0. L'import direct `from sqlalchemy import URL` n'existe qu'en 2.0.

**Diagnostic :**
```powershell
docker compose exec airflow-scheduler python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

**Solution :**
```python
# Compatible SQLAlchemy 1.4 et 2.0
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
```
Et ajouter la contrainte officielle Airflow dans `airflow/Dockerfile` :
```dockerfile
RUN pip install --no-cache-dir -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
```

## Panne : `File doesn't exist` lors d'un `PUT` Snowflake sur Windows

**Symptôme :**
```
ProgrammingError: 253006: File doesn't exist: ['.../ingestion_date%3D2026-08-09/...']
```

**Cause :** les chemins MinIO contiennent des caractères `=` (convention de partitionnement Hive). `pathlib.Path.as_uri()` encode `=` en `%3D` dans l'URI `file://`, mais le connecteur Snowflake sur Windows ne le décode pas correctement avant de vérifier l'existence du fichier.

**Solution :** aplatir le nom du fichier local temporaire pour supprimer tout caractère spécial avant de construire l'URI :
```python
safe_name = object_key.replace("/", "__").replace("=", "-").replace(":", "-")
local_path = temporary_root / safe_name
```
⚠️ Effet de bord à corriger en même temps : le nom de fichier utilisé par le `COPY INTO` doit correspondre au nom réellement uploadé (`local_path.name`), pas être recalculé depuis `object_key`.

## Panne : `NameResolutionError` / `getaddrinfo failed`

**Symptôme :**
```
NameResolutionError: Failed to resolve '<account>.snowflakecomputing.com'
```

**Cause :** panne du serveur DNS local (souvent celui fourni par la box internet), indépendante du code ou de Snowflake.

**Diagnostic :**
```powershell
nslookup <account>.snowflakecomputing.com
```
Si la requête timeout, c'est confirmé : panne DNS, pas applicative.

**Solution :** changer de serveur DNS vers un service public fiable :
```powershell
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses ("8.8.8.8","1.1.1.1")
ipconfig /flushdns
```

## Panne : `MFA is required` / `JWT token is invalid`

**Contexte :** après création d'un nouveau compte Snowflake trial.

**Cause :** Snowflake impose le MFA sur l'authentification par mot de passe pour tout nouveau compte — incompatible avec un script automatisé non interactif.

**Solution :** authentification par paire de clés RSA plutôt que mot de passe. Non soumise au MFA (authentification machine-à-machine).

**Piège rencontré :** `JWT token is invalid` après mise en place de la clé — cause possible 1 : horloge système désynchronisée (`Get-Date` vs heure réelle) ; cause possible 2 (la plus fréquente) : la clé publique n'a pas été réellement enregistrée côté serveur. Vérifier avec :
```sql
DESC USER <username>;
```
Si `RSA_PUBLIC_KEY_FP` est `null`, la clé n'est pas enregistrée — relancer :
```sql
ALTER USER <username> SET RSA_PUBLIC_KEY='<clé_publique_sans_BEGIN_END>';
```
Comparer ensuite l'empreinte SHA256 affichée avec celle calculée localement pour confirmer la correspondance.

**Piège supplémentaire pour dbt :** contrairement au connecteur Python brut, l'adaptateur `dbt-snowflake` nécessite de déclarer explicitement `authenticator: snowflake_jwt` dans `profiles.yml`, sinon il retombe sur l'authentification par mot de passe par défaut.

## Panne : `ModuleNotFoundError` lors d'un script lancé directement

**Symptôme :**
```
uv run python scripts/reconcile_counts.py
ModuleNotFoundError: No module named 'snowflake_load'
```

**Cause :** lancer un fichier par chemin direct (`python chemin/fichier.py`) ajoute le dossier du fichier à `sys.path`, pas la racine du projet.

**Solution :** toujours invoquer les scripts comme des modules :
```powershell
uv run python -m scripts.reconcile_counts
```

## Panne : dbt échoue avec `RAW_STAGING does not exist`

**Cause :** dbt préfixe automatiquement tout `target_schema` custom avec le schéma par défaut du profil (comportement natif de `generate_schema_name`).

**Solution :** surcharger la macro dans `macros/generate_schema_name.sql` pour utiliser le nom de schéma exact fourni, sans préfixe.

## Scénarios de panne à tester volontairement (démonstration)

- **API indisponible** : arrêter `delivery_api` pendant un run Airflow → la tâche `check_sources` doit échouer proprement avant toute extraction.
- **Fichier dupliqué** : relancer l'ingestion sans changement de données → aucun nouveau fichier ne doit être rechargé côté Snowflake (vérifier `AUDIT.FILE_LOADS`).
- **Test dbt en échec** : introduire une valeur négative dans `quantity` côté source → `dbt test` doit échouer sur `dbt_utils.accepted_range`, et `AUDIT.DATA_QUALITY_RESULTS` doit enregistrer `status = FAIL`.