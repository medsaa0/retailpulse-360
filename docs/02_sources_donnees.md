# RetailPulse 360 — Sources de données

## 1. Vue générale

RetailPulse 360 utilise plusieurs sources de données afin de reproduire une architecture Data Engineering réaliste.

| Source | Technologie | Données principales | Fréquence |
|---|---|---|---|
| Base transactionnelle | PostgreSQL | clients, produits, magasins et commandes | quotidienne |
| Fichiers de retours | CSV | retours et remboursements | quotidienne |
| Fichiers d'inventaire | CSV | stock par magasin et produit | quotidienne |
| Suivi logistique | API REST / JSON | événements de livraison | horaire |

## 2. Base transactionnelle PostgreSQL

PostgreSQL représente le système opérationnel de l'entreprise.

### 2.1 Table customers

Granularité :

```text
Une ligne par client
```

Clé primaire :

```text
customer_id
```

Colonnes principales :

- customer_id ;
- first_name ;
- last_name ;
- email ;
- phone ;
- city ;
- country ;
- customer_segment ;
- created_at ;
- updated_at.

### 2.2 Table products

Granularité :

```text
Une ligne par produit
```

Clé primaire :

```text
product_id
```

Colonnes principales :

- product_id ;
- product_name ;
- category ;
- subcategory ;
- brand ;
- unit_price ;
- unit_cost ;
- active ;
- created_at ;
- updated_at.

### 2.3 Table stores

Granularité :

```text
Une ligne par magasin
```

Clé primaire :

```text
store_id
```

Colonnes principales :

- store_id ;
- store_name ;
- city ;
- region ;
- opening_date ;
- active ;
- created_at ;
- updated_at.

### 2.4 Table orders

Granularité :

```text
Une ligne par commande
```

Clé primaire :

```text
order_id
```

Colonnes principales :

- order_id ;
- customer_id ;
- store_id ;
- channel ;
- order_status ;
- order_date ;
- currency ;
- payment_method ;
- created_at ;
- updated_at.

Canaux autorisés :

- WEB ;
- MOBILE ;
- STORE ;
- CALL_CENTER.

### 2.5 Table order_items

Granularité :

```text
Une ligne par article présent dans une commande
```

Clé composée :

```text
order_id + order_item_id
```

Colonnes principales :

- order_item_id ;
- order_id ;
- product_id ;
- quantity ;
- unit_price ;
- unit_cost ;
- discount_percentage ;
- created_at ;
- updated_at.

## 3. Fichiers CSV de retours

Les retours sont reçus quotidiennement sous forme de fichiers CSV.

Convention de nommage :

```text
returns_YYYY_MM_DD.csv
```

Exemple :

```text
returns_2026_08_05.csv
```

Granularité :

```text
Une ligne par événement de retour
```

Colonnes principales :

- return_id ;
- order_id ;
- order_item_id ;
- product_id ;
- returned_quantity ;
- return_reason ;
- return_status ;
- return_date ;
- refund_amount.

Motifs possibles :

- DAMAGED_PRODUCT ;
- WRONG_PRODUCT ;
- CUSTOMER_CHANGED_MIND ;
- SIZE_OR_COMPATIBILITY ;
- DELIVERY_DELAY ;
- OTHER.

## 4. Fichiers CSV d'inventaire

Les stocks sont reçus sous forme de snapshots quotidiens.

Convention de nommage :

```text
inventory_YYYY_MM_DD.csv
```

Exemple :

```text
inventory_2026_08_05.csv
```

Granularité :

```text
Une ligne par date, magasin et produit
```

Colonnes principales :

- snapshot_date ;
- store_id ;
- product_id ;
- available_quantity ;
- reserved_quantity ;
- damaged_quantity ;
- reorder_threshold.

## 5. API REST de livraison

Une API REST simulée fournit les événements de livraison.

Endpoint prévu :

```text
GET /api/v1/deliveries
```

Granularité :

```text
Une ligne par événement logistique
```

Colonnes principales :

- delivery_id ;
- order_id ;
- carrier ;
- delivery_status ;
- event_timestamp ;
- shipping_date ;
- expected_delivery_date ;
- actual_delivery_date ;
- destination_city.

Statuts possibles :

- CREATED ;
- PICKED_UP ;
- IN_TRANSIT ;
- OUT_FOR_DELIVERY ;
- DELIVERED ;
- FAILED ;
- RETURNED.

## 6. Zone de stockage brute

Pendant le développement local, les données brutes seront stockées dans MinIO.

Nom du bucket :

```text
retailpulse-raw
```

Organisation prévue :

```text
retailpulse-raw/
├── postgresql/
│   ├── customers/
│   ├── products/
│   ├── stores/
│   ├── orders/
│   └── order_items/
├── csv/
│   ├── returns/
│   └── inventory/
└── api/
    └── deliveries/
```

Exemple de chemin :

```text
postgresql/orders/extraction_date=2026-08-05/orders.parquet
```

## 7. Métadonnées techniques

Chaque extraction devra enregistrer :

- source_name ;
- dataset_name ;
- extraction_timestamp ;
- ingestion_timestamp ;
- run_id ;
- source_file_name ;
- source_file_path ;
- row_count ;
- checksum ;
- pipeline_status.

Ces métadonnées permettront de :

- tracer les exécutions ;
- détecter les fichiers déjà traités ;
- éviter les doublons ;
- identifier les anomalies ;
- reprendre un pipeline après une erreur.

## 8. Stratégies de chargement

| Dataset | Premier chargement | Chargements suivants |
|---|---|---|
| customers | complet | incrémental selon updated_at |
| products | complet | incrémental selon updated_at |
| stores | complet | incrémental selon updated_at |
| orders | complet | incrémental selon updated_at |
| order_items | complet | incrémental selon updated_at |
| returns | fichiers quotidiens | ajout des nouveaux fichiers |
| inventory | snapshot quotidien | ajout des nouveaux snapshots |
| deliveries | extraction complète | incrémental selon event_timestamp |

## 9. Format de stockage

Les extractions seront converties au format Parquet lorsque cela est pertinent.

Parquet apporte :

- une meilleure compression ;
- une lecture rapide par colonnes ;
- un typage plus fiable que CSV ;
- une bonne compatibilité avec Snowflake ;
- une réduction du volume de stockage.

Les fichiers CSV originaux seront également conservés afin de garantir la traçabilité.

## 10. Données sensibles

Les colonnes suivantes sont considérées comme sensibles :

- first_name ;
- last_name ;
- email ;
- phone.

Elles ne devront pas apparaître directement dans les tables analytiques ou dans Power BI.

Un identifiant pseudonymisé sera utilisé pour les analyses clients.
