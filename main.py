from ultralytics import YOLO
import requests
from SPARQLWrapper import SPARQLWrapper, POST, TURTLE, JSON
import networkx as nx
import rdflib
import logging
from datetime import datetime

YOLO_MODEL = 'yolo11x.pt'
FUSEKI_BASE_ENDPOINT = "http://localhost:3030"
DATASET_NAME = "yolo"

# Fonction de détection d'objets
def yolo_detect_objects(image_path):
    logging.info(f"Démarrage de la détection d'objets pour l'image : {image_path}")
    try:
        model = YOLO('models/'+YOLO_MODEL)
        results = model(image_path, verbose=False)
        if not results or not results[0].boxes:
            logging.warning(f"Aucun objet détecté dans l'image : {image_path}")
            return []
        classes = [model.names[int(box.cls)] for box in results[0].boxes]
        logging.info(f"Classes détectées : {classes}")
        return classes
    except Exception as e:
        print(e)
        logging.error(f"Erreur lors de la détection d'objets : {e}")
        return []

# Fonction pour récupérer les relations depuis ConceptNet
def get_relations_from_conceptnet(concepts):
    base_url = "https://api.conceptnet.io/c/en/"
    graph = rdflib.Graph()

    logging.info("Démarrage de la récupération des relations ConceptNet pour les concepts.")
    CN = rdflib.Namespace("http://conceptnet.io")

    for concept in concepts:
        offset = 0
        limit = 2000
        logging.info(f"Récupération des relations pour le concept : {concept}")

        while True:
            # Construction de l'URL avec pagination
            url = f"{base_url}{concept}?limit={limit}&offset={offset}"
            try:
                logging.debug(f"Envoi de la requête à : {url}")
                response = requests.get(url)
                response.raise_for_status()  # Lève une exception si la réponse est une erreur
                data = response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Échec de la requête pour le concept {concept} avec erreur : {e}")
                break
            
            # Parcours des relations récupérées et ajout dans le graphe RDF
            for edge in data.get("edges", []):
                rel = edge.get("rel", {}).get("@id", "")  # Récupération de la relation
                start = edge.get("start", {}).get("@id", "")  # Concept de départ
                end = edge.get("end", {}).get("@id", "")  # Concept d'arrivée

                if not rel or not start or not end:
                    continue

                # Création des URI pour les concepts et la relation dans le graphe RDF
                start_uri = CN[start]
                end_uri = CN[end]
                rel_uri = CN[rel]

                graph.add((start_uri, rel_uri, end_uri))
                logging.debug(f"Relation ajoutée : {start_uri} -> {rel_uri} -> {end_uri}")

            if len(data.get("edges", [])) < limit:
                logging.info(f"Toutes les relations pour le concept {concept} ont été récupérées.")
                break

            offset += limit

    logging.info("Récupération des relations ConceptNet terminée.")
    return graph

# Fonction pour insérer un graphe RDF dans Fuseki
def insert_rdf_to_fuseki(rdf_graph):
    logging.info("Démarrage de l'insertion du RDF dans Fuseki.")

    try:
        fuseki_endpoint = f"{FUSEKI_BASE_ENDPOINT}/{DATASET_NAME}/data"
        rdf_data = rdf_graph.serialize(format='turtle')  # Sérialisation du graphe RDF au format Turtle

        headers = {
            "Content-Type": "text/turtle"
        }

        logging.debug(f"RDF sérialisé : {rdf_data[:200]}...")

        # Envoi de la requête POST à Fuseki avec les données RDF
        response = requests.post(fuseki_endpoint, data=rdf_data, headers=headers)

        if response.status_code == 200:
            logging.info("Données RDF insérées avec succès dans Fuseki.")
        else:
            logging.error(f"Échec de l'insertion des données RDF dans Fuseki. Code de statut : {response.status_code}, Réponse : {response.text}")

    except Exception as e:
        logging.error(f"Erreur lors de l'insertion des données RDF dans Fuseki : {e}")

# Fonction pour extraire un graphe de connaissances (KG) basé sur des concepts
def KnGraph_extract(concepts):
    query = """
    PREFIX cn: <http://conceptnet.io/c/en/>
    SELECT ?subject ?predicate ?object
    WHERE {
        {
            ?subject ?predicate ?object .
            FILTER (?subject IN (""" + ",".join([f"cn:{concept}" for concept in concepts]) + """) ||
                    ?object IN (""" + ",".join([f"cn:{concept}" for concept in concepts]) + """))
        }
        UNION
        {
            ?subject ?predicate ?object .
            ?object ?predicate2 ?subject2 .
            FILTER (?subject IN (""" + ",".join([f"cn:{concept}" for concept in concepts]) + """) ||
                    ?object IN (""" + ",".join([f"cn:{concept}" for concept in concepts]) + """))
        }
    }
    LIMIT 1000
    """

    # Requête SPARQL pour extraire les relations de ConceptNet
    sparql = SPARQLWrapper(f"{FUSEKI_BASE_ENDPOINT}/{DATASET_NAME}/query")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        logging.debug("Envoi de la requête SPARQL pour récupérer les données.")
        results = sparql.query().convert()
        logging.info("Requête SPARQL exécutée avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la requête SPARQL : {e}")
        return

    G = nx.Graph() 
    logging.info("Construction du graphe à partir des résultats de la requête.")

    # Construction du graphe à partir des résultats SPARQL
    for result in results["results"]["bindings"]:
        subject = result["subject"]["value"].split('/')[-1]
        predicate = result["predicate"]["value"].split('/')[-1]
        obj = result["object"]["value"].split('/')[-1]

        G.add_edge(subject, obj, label=predicate)  # Ajout d'une arête avec un label (relation)

    logging.info("Construction du graphe terminée. Suppression des nœuds non pertinents.")

    # Suppression des nœuds non pertinents (ceux qui sont isolés dans le contexte des concepts donnés)
    nodes_to_remove = []
    for node in G.nodes():
        related_concepts = [n for n in G[node] if any(concept == n for concept in concepts)]
        if len(related_concepts) == 1 and not any(concept == node for concept in concepts):
            nodes_to_remove.append(node)

    G.remove_nodes_from(nodes_to_remove)
    
    return G


# Fonction de génération de description RDF
def generate_rdf_description(concepts):
    graph = KnGraph_extract(concepts)
    rdf_graph = rdflib.Graph()
    for u, v, data in graph.edges(data=True):
        subject = rdflib.URIRef(f"http://example.org/{u}")
        obj = rdflib.URIRef(f"http://example.org/{v}")
        predicate = rdflib.URIRef(f"http://example.org/{data['label']}")
        rdf_graph.add((subject, predicate, obj))
    return rdf_graph.serialize(format="turtle")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler('logs/'+datetime.now().strftime("log_%Y-%m-%d_%H-%M-%S.log"), encoding='utf-8')
    ]
)
