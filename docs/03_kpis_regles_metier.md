# RetailPulse 360 — KPI et règles métier

## 1. Principes généraux

Chaque KPI doit posséder :

- une définition métier ;
- une formule ;
- une granularité ;
- les statuts inclus ;
- les statuts exclus ;
- une règle de gestion des valeurs nulles.

## 2. Statuts des commandes

Statuts autorisés :

- CREATED ;
- PAID ;
- PROCESSING ;
- SHIPPED ;
- DELIVERED ;
- CANCELLED ;
- REFUNDED.

Les commandes ayant le statut `CANCELLED` sont exclues des ventes.

Les commandes `REFUNDED` restent présentes dans l'historique, mais leur montant remboursé est retiré du chiffre d'affaires net.

## 3. Canaux de vente

Canaux autorisés :

- WEB ;
- MOBILE ;
- STORE ;
- CALL_CENTER.

Toute autre valeur doit être signalée comme invalide.

## 4. Chiffre d'affaires brut

Définition :

Montant des articles avant les réductions et remboursements.

Formule :

```text
gross_sales = quantity × unit_price
```

## 5. Montant de la réduction

Formule :

```text
discount_amount =
quantity × unit_price × discount_percentage
```

La valeur `discount_percentage` doit être comprise entre 0 et 1.

Exemples :

- 0 signifie aucune réduction ;
- 0.10 signifie 10 % ;
- 0.25 signifie 25 %.

## 6. Ventes après réduction

Formule :

```text
sales_after_discount =
gross_sales - discount_amount
```

## 7. Chiffre d'affaires net

Formule :

```text
net_revenue =
sales_after_discount - refunded_amount
```

Les commandes annulées sont exclues.

## 8. Coût des marchandises vendues

Avant les retours :

```text
gross_cogs =
quantity × unit_cost
```

Après les retours :

```text
net_cogs =
gross_cogs - returned_quantity × unit_cost
```

## 9. Marge brute

Formule :

```text
gross_margin =
net_revenue - net_cogs
```

Taux de marge :

```text
gross_margin_rate =
gross_margin / net_revenue
```

Lorsque `net_revenue` est égal à zéro, le taux de marge doit être null.

## 10. Panier moyen

Formule :

```text
average_order_value =
net_revenue / nombre de commandes distinctes
```

Seules les commandes non annulées sont incluses.

## 11. Taux de retour

Formule :

```text
return_rate =
returned_quantity / sold_quantity
```

La quantité retournée cumulée ne doit pas dépasser la quantité vendue.

## 12. Livraison à temps

Une livraison est considérée à temps lorsque :

```text
actual_delivery_date <= expected_delivery_date
```

Formule :

```text
on_time_delivery_rate =
livraisons à temps / livraisons terminées
```

Seules les livraisons ayant le statut `DELIVERED` sont incluses.

## 13. Retard de livraison

Formule :

```text
delivery_delay_days =
actual_delivery_date - expected_delivery_date
```

Lorsqu'une livraison arrive en avance, le retard est égal à zéro.

## 14. Disponibilité du stock

Un produit est disponible lorsque :

```text
available_quantity > 0
```

Formule :

```text
availability_rate =
produits disponibles / produits actifs
```

## 15. Rupture de stock

Un produit est en rupture lorsque :

```text
available_quantity <= 0
```

Formule :

```text
out_of_stock_rate =
produits en rupture / produits actifs
```

## 16. Seuil de réapprovisionnement

Un produit doit être réapprovisionné lorsque :

```text
available_quantity <= reorder_threshold
```

## 17. Client récurrent

Un client est considéré comme récurrent lorsqu'il possède au moins deux commandes non annulées.

Formule :

```text
repeat_customer_rate =
clients avec au moins deux commandes / clients acheteurs
```

## 18. Qualité des clients

- `customer_id` ne doit jamais être null ;
- `customer_id` doit être unique ;
- l'email doit respecter un format valide lorsqu'il est renseigné ;
- `created_at` doit être antérieur ou égal à `updated_at` ;
- `country` ne doit pas être null ;
- les informations personnelles doivent être protégées.

## 19. Qualité des produits

- `product_id` doit être unique ;
- `product_name` ne doit pas être vide ;
- `unit_price` doit être supérieur ou égal à zéro ;
- `unit_cost` doit être supérieur ou égal à zéro ;
- la catégorie doit appartenir à une liste connue ;
- les produits inactifs restent conservés dans l'historique.

## 20. Qualité des commandes

- `order_id` doit être unique ;
- `customer_id` doit exister dans les clients ;
- `store_id` doit exister lorsqu'il est renseigné ;
- `order_date` ne doit pas être dans le futur ;
- la devise doit être `MAD` ;
- le canal doit appartenir à la liste autorisée ;
- le statut doit appartenir à la liste autorisée.

## 21. Qualité des lignes de commande

- `quantity` doit être strictement positive ;
- `unit_price` doit être positif ou nul ;
- `unit_cost` doit être positif ou nul ;
- `discount_percentage` doit être compris entre 0 et 1 ;
- `order_id` doit exister dans les commandes ;
- `product_id` doit exister dans les produits ;
- la combinaison `order_id + order_item_id` doit être unique.

## 22. Qualité des retours

- `return_id` doit être unique ;
- la commande doit exister ;
- la ligne de commande doit exister ;
- la quantité retournée doit être strictement positive ;
- la quantité retournée cumulée ne doit pas dépasser la quantité vendue ;
- la date de retour doit être postérieure ou égale à la date de commande ;
- le montant remboursé doit être positif ou nul.

## 23. Qualité des livraisons

- `delivery_id` doit être unique ;
- la commande doit exister ;
- une livraison terminée doit posséder une date réelle ;
- la date réelle ne doit pas précéder la date d'expédition ;
- le statut doit appartenir à une liste autorisée.

## 24. Qualité de l'inventaire

- `available_quantity` doit être positif ou nul ;
- `reserved_quantity` doit être positif ou nul ;
- `damaged_quantity` doit être positif ou nul ;
- `reorder_threshold` doit être positif ou nul ;
- une seule ligne doit exister par date, magasin et produit.

## 25. Gestion des doublons

Les doublons sont détectés grâce aux clés métier.

Lorsqu'un enregistrement arrive plusieurs fois :

- la version la plus récente est conservée ;
- le nombre de doublons est enregistré ;
- le pipeline ne doit pas créer une nouvelle ligne inutile ;
- une relance doit produire le même résultat.

Ce comportement est appelé idempotence.

## 26. Données personnelles

Les noms, emails et téléphones ne doivent pas apparaître dans les tables analytiques finales.

Un identifiant pseudonymisé sera créé à partir de `customer_id`.

Les dashboards Power BI utiliseront uniquement cet identifiant.
