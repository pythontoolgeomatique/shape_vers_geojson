# Convertisseur et Extracteur SHP vers GeoJSON

Un outil de bureau puissant en Python avec une interface graphique moderne pour convertir et extraire des données de fichiers Shapefile (.shp) vers GeoJSON (.geojson).

*(Pensez à remplacer ce lien par une capture d'écran de votre application \!)*

## 📖 À propos

Cet outil a été conçu pour deux scénarios principaux :

1.  **Conversion simple :** Transformer rapidement un fichier Shapefile en un unique fichier GeoJSON.
2.  **Extraction avancée :** Agir comme un mini-ETL en vous permettant de filtrer un Shapefile volumineux en plusieurs fichiers GeoJSON plus petits, basés sur des requêtes complexes.

L'interface est construite en Python à l'aide de **`ttkbootstrap`** (pour un look moderne), et la logique géospatiale est gérée par **`geopandas`** et **`fiona`**.

## 🚀 Fonctionnalités

  * **Interface Moderne :** Une interface utilisateur claire et facile à utiliser grâce à `ttkbootstrap`.
  * **Deux Modes de Travail :**
    1.  **Conversion Simple :** 1 fichier SHP → 1 fichier GeoJSON.
    2.  **Extraction par Requête :** 1 fichier SHP → Plusieurs fichiers GeoJSON.
  * **Constructeur de Requêtes Avancé (Mode Extraction) :**
      * Créez des filtres complexes avec les opérateurs `AND`, `OR` et des parenthèses `( )`.
      * Langage de requête basé sur `pandas.query()` (très puissant).
      * **Conversion de type automatique :** L'outil détecte intelligemment les comparaisons numériques (ex: `> 50`) et convertit les colonnes de texte (ex: `"50"`) en nombres à la volée pour éviter les erreurs de type.
  * **Nommage Personnalisé :**
      * Nommez vos fichiers de sortie extraits comme vous le souhaitez (ex: `zones_urbaines.geojson`).
      * Si aucun nom n'est fourni, l'outil numérote automatiquement les fichiers (`1.geojson`, `2.geojson`, etc.) pour éviter les conflits.

## 🛠️ Installation

Pour utiliser cet outil, vous avez besoin de Python 3.x installé sur votre machine.

1.  **Clonez ce dépôt :**

    ```bash
    git clone https://github.com/VOTRE_NOM_UTILISATEUR/VOTRE_PROJET.git
    cd VOTRE_PROJET
    ```

2.  **(Recommandé) Créez un environnement virtuel :**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installez les dépendances :**
    *Créez un fichier `requirements.txt` avec le contenu ci-dessous, puis exécutez `pip install -r requirements.txt`.*

    ```
    geopandas
    pandas
    ttkbootstrap
    fiona
    ```

    *(Alternative : `pip install geopandas pandas ttkbootstrap fiona`)*

## ⚡ Utilisation

Une fois les dépendances installées, lancez simplement le script principal :

```bash
python votre_script.py
```

*(Remplacez `votre_script.py` par le nom de votre fichier, ex: `convert_and_query_v4.py`)*

### Workflow

1.  **Chargez un fichier SHP** (bouton "Parcourir...").

2.  **Choisissez votre mode :**

      * **Onglet "Conversion Simple" :**

        1.  Choisissez un emplacement de sortie ("Enregistrer sous...").
        2.  Cliquez sur "Lancer la Conversion Simple".

      * **Onglet "Extraction par Requête" :**

        1.  Cliquez sur **"Charger les attributs"**.
        2.  Utilisez le **constructeur** pour créer votre requête (ex: `(`POPULATION`  > 1000) and ( `SUPERFICIE`  < 50) `).
        3.  (Optionnel) Donnez un **nom de fichier** personnalisé (ex: `grandes_villes`).
        4.  Cliquez sur **"Ajouter la requête... ⬇️"**.
        5.  Répétez l'opération pour toutes les extractions souhaitées.
        6.  Choisissez un **dossier** de sortie ("Parcourir...").
        7.  Cliquez sur **"Générer les Fichiers par Requête"**.

