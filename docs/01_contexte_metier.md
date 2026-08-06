# RetailPulse 360 — Contexte métier

## 1. Présentation

RetailPulse 360 est une plateforme analytique destinée à une entreprise marocaine de vente omnicanale.

L'entreprise vend ses produits à travers :

- un site e-commerce ;
- une application mobile ;
- plusieurs magasins physiques ;
- des commandes assistées par le service client.

Les informations sont actuellement réparties entre plusieurs systèmes :

- une base PostgreSQL transactionnelle ;
- des fichiers CSV produits quotidiennement ;
- une API de suivi des livraisons ;
- des exports d'inventaire provenant des magasins.

Cette fragmentation empêche les équipes métier d'obtenir une vision fiable et unifiée des ventes, des clients, des retours, des livraisons et des stocks.

## 2. Problème métier

Les responsables rencontrent plusieurs difficultés :

- les chiffres de ventes diffèrent selon les fichiers ;
- les rapports sont créés manuellement ;
- les données contiennent des doublons ;
- certains retours ne sont pas associés à une commande ;
- il est difficile de suivre les ruptures de stock ;
- le calcul de la marge n'est pas uniforme ;
- la performance des canaux n'est pas clairement mesurée ;
- les données clients historiques sont écrasées lors des modifications ;
- les dashboards sont actualisés tardivement.

## 3. Objectif du projet

Construire une plateforme Data Engineering capable de :

1. collecter les données de plusieurs sources ;
2. conserver les fichiers bruts dans une zone de stockage ;
3. charger les données dans Snowflake ;
4. nettoyer et transformer les données avec dbt ;
5. créer un modèle dimensionnel ;
6. garantir la qualité et la traçabilité des données ;
7. orchestrer les pipelines avec Apache Airflow ;
8. alimenter un dashboard Power BI ;
9. automatiser les tests avec GitHub Actions.

## 4. Utilisateurs cibles

### Direction générale

Elle souhaite connaître :

- le chiffre d'affaires ;
- la marge ;
- la croissance ;
- la performance globale des magasins et canaux.

### Équipe commerciale

Elle souhaite analyser :

- les ventes par produit ;
- les ventes par catégorie ;
- les performances par magasin ;
- les performances par canal.

### Équipe marketing

Elle souhaite analyser :

- les nouveaux clients ;
- les clients récurrents ;
- la fréquence d'achat ;
- la valeur moyenne des commandes.

### Équipe logistique

Elle souhaite analyser :

- les retards de livraison ;
- les stocks disponibles ;
- les ruptures de stock ;
- les produits fréquemment retournés.

## 5. Périmètre fonctionnel

Le projet couvre :

- clients ;
- produits ;
- catégories ;
- magasins ;
- commandes ;
- lignes de commande ;
- paiements ;
- retours ;
- livraisons ;
- inventaire journalier.

## 6. Périmètre géographique

Les données simulées représenteront des ventes réalisées au Maroc.

Les villes principales seront notamment :

- Casablanca ;
- Rabat ;
- Marrakech ;
- Tanger ;
- Oujda ;
- Fès ;
- Agadir ;
- Meknès.

## 7. Devise et fuseau horaire

- Devise analytique principale : MAD
- Fuseau horaire métier : Africa/Casablanca
- Fuseau de stockage technique : UTC
- Langue principale de la documentation : français

## 8. Résultat attendu

La plateforme doit permettre à un utilisateur métier de consulter des KPI fiables sans retraiter manuellement les données.

Elle doit également permettre à un Data Engineer de :

- relancer un pipeline sans dupliquer les données ;
- détecter une anomalie ;
- identifier le fichier ou lot responsable ;
- restaurer les traitements après une panne ;
- consulter les logs et résultats de qualité.
