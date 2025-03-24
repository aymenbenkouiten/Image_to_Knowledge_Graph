# Image_to_Knowledge_Graph

# Détection d'Objets & Visualisation de Graphes de Connaissances

Ce projet combine la détection d’objets via YOLO avec l’extraction et la représentation de connaissances sémantiques sous forme de graphes RDF. Les relations entre concepts sont enrichies en interrogeant ConceptNet, puis stockées dans une base RDF gérée par Apache Jena Fuseki (version 5.2.0). Une interface utilisateur interactive, développée avec Streamlit, permet de visualiser les résultats sous forme de tableau et de graphe.

---

## Table des Matières

- [Présentation du Projet](#présentation-du-projet)
- [Prérequis](#prérequis)
- [Installation et Configuration](#installation-et-configuration)
- [Structure du Code](#structure-du-code)
  - [main.py](#mainpy)
  - [UI.py](#uipy)
- [Exécution du Projet](#exécution-du-projet)
- [Détails Techniques et Choix Architecturaux](#détails-techniques-et-choix-architecturaux)
- [Références et Sources](#références-et-sources)

---

## Présentation du Projet

Ce projet vise à extraire des informations sémantiques à partir d’images en détectant les objets présents avec un modèle YOLO. Les classes d’objets détectées sont ensuite utilisées pour interroger ConceptNet afin d’obtenir des relations entre ces concepts. Les données récupérées sont transformées en triplets RDF et stockées dans un serveur Apache Jena Fuseki. Un graphe de connaissances est construit et visualisé à l’aide de NetworkX et matplotlib dans une application Streamlit.

---

## Prérequis

- **Python**
- Les bibliothèques Python suivantes :
  - `ultralytics` (pour YOLO)
  - `requests`
  - `SPARQLWrapper`
  - `networkx`
  - `rdflib`
  - `logging`
  - `matplotlib`
  - `streamlit`
- **Apache Jena Fuseki 5.2.0**  
  Vous devez installer et lancer Fuseki pour gérer le triplestore RDF. Assurez-vous qu’il est accessible à l’adresse [http://localhost:3030](http://localhost:3030).

---

## Installation et Configuration

1. **Installation des dépendances Python :**

   Utilisez pip pour installer toutes les bibliothèques nécessaires. Par exemple :

   ```bash
   pip install ultralytics requests SPARQLWrapper networkx rdflib matplotlib streamlit
   ```

2. **Installation d’Apache Jena Fuseki 5.2.0 :**

   Téléchargez Apache Jena Fuseki depuis le site officiel et suivez la documentation. Pour lancer le serveur, utilisez la commande :

   ```bash
   fuseki-server
   ```

   Le serveur sera alors accessible à l’adresse [http://localhost:3030](http://localhost:3030).

3. **Configuration des dossiers :**

   - **Modèles YOLO :** Placez le modèle YOLO (par exemple `yolo11x.pt`) dans le dossier `models/`.
   - **Images et Logs :**  
     - Les images temporaires seront enregistrées dans le dossier `temp_images/`.
     - Les logs seront stockés dans le dossier `logs/` avec un nom de fichier incluant la date et l’heure.

---

## Structure du Code

### main.py

Ce fichier contient la logique principale du projet. Il se compose de plusieurs fonctions clés :

- **yolo_detect_objects(image_path) :**  
  Lance la détection d’objets sur une image donnée en utilisant le modèle YOLO. Les classes détectées sont extraites et retournées.

- **get_relations_from_conceptnet(concepts) :**  
  Pour chaque concept détecté, cette fonction interroge l’API de ConceptNet et construit un graphe RDF en récupérant les relations entre les concepts. Les requêtes sont paginées pour récupérer un grand nombre de relations.

- **insert_rdf_to_fuseki(rdf_graph) :**  
  Sérialise le graphe RDF au format Turtle et l’insère dans le triplestore Apache Jena Fuseki via une requête POST sur l’endpoint `/data`.

- **KnGraph_extract(concepts) :**  
  Exécute une requête SPARQL pour extraire un sous-graphe des relations des concepts depuis Fuseki et construit un graphe NetworkX à partir des résultats.

- **generate_rdf_description(concepts) :**  
  Génère une description RDF en convertissant le graphe extrait en triplets RDF sérialisés au format Turtle.

Chaque étape du traitement est loguée avec différents niveaux (info, debug, warning) afin de faciliter le suivi de l’exécution.

### UI.py

Ce fichier implémente l’interface utilisateur avec Streamlit. Ses fonctionnalités incluent :

- **Options de traitement :**  
  Possibilité d’uploader une image ou d’utiliser la webcam. Plusieurs options de configuration sont proposées dans la sidebar (algorithme de détection, seuil de confiance, personnalisation du graphe).

- **Visualisation des résultats :**  
  Affichage des concepts détectés dans un tableau personnalisé. Possibilité de télécharger la liste des concepts.  
  Deux modes d’affichage sont disponibles :
  - **Knowledge Graph :** Récupère les relations via ConceptNet, insère les données dans Fuseki, et affiche le graphe de connaissances.
  - **RDF Description :** Affiche le contenu RDF généré à partir des concepts détectés.

---

## Exécution du Projet

1. **Lancer Apache Jena Fuseki :**  
   Dans un terminal, exécutez :

   ```bash
   fuseki-server
   ```

   Cela démarre le serveur Fuseki sur [http://localhost:3030](http://localhost:3030).

2. **Lancer l'interface utilisateur :**  
   Dans un autre terminal, exécutez :

   ```bash
   streamlit run UI.py
   ```

   L’interface Streamlit s’ouvrira dans votre navigateur. Vous pourrez alors uploader une image ou utiliser la webcam, lancer la détection, visualiser le graphe de connaissances ou obtenir la description RDF.

3. **Vérification des logs et fichiers générés :**  
   Consultez le dossier `logs/` pour suivre l’exécution du projet. Les images uploadées seront sauvegardées temporairement dans `temp_images/`.

---

## Détails Techniques et Choix Architecturaux

- **Détection d’Objets avec YOLO :**  
  Le choix de YOLO permet une détection rapide et efficace en temps réel. Le modèle utilisé est chargé dynamiquement depuis le dossier `models/`.

- **Enrichissement Sémantique avec ConceptNet :**  
  Après la détection, chaque classe d’objet est utilisée pour interroger ConceptNet et récupérer des relations sémantiques. Ces informations enrichissent le contexte des objets détectés.

- **Stockage RDF et Fuseki :**  
  Les triplets RDF générés sont stockés dans Apache Jena Fuseki via une requête POST. Le choix de Fuseki 5.2.0 permet une intégration avec des fonctionnalités SPARQL robustes pour l’interrogation des données.

- **Visualisation des Graphes :**  
  Le graphe des connaissances est construit à partir des résultats d’une requête SPARQL exécutée sur Fuseki. NetworkX et matplotlib sont utilisés pour la représentation graphique, tandis que Streamlit offre une interface utilisateur moderne et interactive.


---

## Références et Sources

- **Apache Jena Fuseki :** [Documentation Fuseki](https://jena.apache.org/documentation/fuseki2/)
- **ConceptNet :** [ConceptNet API](https://conceptnet.io/)
- **YOLO (You Only Look Once) :** [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
