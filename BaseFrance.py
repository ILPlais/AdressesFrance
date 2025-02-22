#!/bin/python3
import os
import googlemaps.client
import googlemaps.elevation
import requests
from colorama import Fore, Style
import gzip
import sqlite3
import pandas
from dotenv import load_dotenv
import googlemaps
from tqdm import tqdm

# Charger les variables d'environnement
load_dotenv(".env")

# Initialiser le client Google Maps
gmaps = googlemaps.Client(key = os.getenv("GOOGLE_API_KEY"))

# Données à traiter
scope = os.getenv("SCOPE")

def recupCSV():
	"""
	Récupère le fichier CSV des adresses de toute la France.
	"""
	# Télécharger le fichier CSV
	url = f"https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{scope}.csv.gz"

	print(Fore.BLUE + "[*] Téléchargement du fichier CSV..." + Style.RESET_ALL)

	response = requests.get(url)
	with open(f"adresses-{scope}.csv.gz", "wb") as f:
		f.write(response.content)

	print(Fore.GREEN + "[+] Fichier CSV téléchargé avec succès." + Style.RESET_ALL)

	print(Fore.BLUE + "[*] Décompression du fichier CSV..." + Style.RESET_ALL)

	# Décompresser le fichier CSV
	with gzip.open(f"adresses-{scope}.csv.gz", "rb") as f:
		csv_data = f.read()

	# Enregistrer le fichier CSV décompressé
	with open(f"adresses-{scope}.csv", "wb") as f:
		f.write(csv_data)

	print(Fore.GREEN + "[+] Fichier CSV décompressé avec succès." + Style.RESET_ALL)

def creerBDD():
	"""
	Créer la base de données pour les adresses de toute la France.
	"""
	# Créer la base de données
	print(Fore.BLUE + "[*] Création de la base de données..." + Style.RESET_ALL)
	conn = sqlite3.connect(f"adresses-{scope}.sqlite")
	cursor = conn.cursor()

	# Créer la table des villes
	cursor.execute("""
	CREATE TABLE IF NOT EXISTS VILLES (
		VIL_CODE_INSEE    TEXT PRIMARY KEY,
		VIL_NOM           TEXT NOT NULL,
		VIL_CODE_POSTAL   TEXT NOT NULL
	);
	""")

	# Créer la table des adresses
	cursor.execute("""
	CREATE TABLE IF NOT EXISTS ADRESSES (
		ADR_ID              TEXT PRIMARY KEY,
		ADR_NUMERO          INTEGER NOT NULL,
		ADR_REP             TEXT,
		ADR_NOM_VOIE        TEXT NOT NULL,
		ADR_LATITUDE        REAL,
		ADR_LONGITUDE       REAL,
		ADR_ALTITUDE        REAL,
		ADR_VIL_CODE_INSEE  INTEGER NOT NULL,
		FOREIGN KEY (ADR_VIL_CODE_INSEE)
			REFERENCES VILLES (VIL_CODE_INSEE) 
				ON DELETE CASCADE 
				ON UPDATE CASCADE
	);
	""")

	# Valider les modifications
	conn.commit()

	# Fermer la connexion et le curseur
	cursor.close()
	conn.close()

	print(Fore.GREEN + "[+] Base de données créée avec succès." + Style.RESET_ALL)

def remplirBDD():
	"""
	Remplit la base de données avec les adresses contenues dans le fichier CSV.
	"""
	# Ouvrir la connexion à la base de données
	conn = sqlite3.connect(f"adresses-{scope}.sqlite")
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()

	# Lire le fichier CSV en utilisant pandas
	print(Fore.BLUE + "[*] Lecture du fichier CSV..." + Style.RESET_ALL)
	donneesCSV = pandas.read_csv(f"adresses-{scope}.csv",
		sep = ";",
		encoding = "utf-8",
		index_col = "id",
		usecols = ["id", "numero", "rep", "nom_voie", "code_postal", "code_insee", "nom_commune", "lon", "lat"],
		dtype = {
			"id": str,
			"numero": int,
			"nom_voie": str,
			"code_postal": str,
			"code_insee": str,
			"nom_commune": str,
			"lon": float,
			"lat": float
		}
	)

	# Nombre total d'adresses
	print(Fore.BLUE + "[*] Comptage des adresses..." + Style.RESET_ALL)
	nombre_adresses = len(donneesCSV)
	print(Fore.GREEN + f"[+] Nombre d'adresses : {nombre_adresses:_}.".replace("_", " ") + Style.RESET_ALL)

	print(Fore.BLUE + "[*] Remplissage de la base de données..." + Style.RESET_ALL)

	# Initialiser la ville en cours
	ville_en_cours = None

	# Parcours les données du fichier CSV
	for ligne in tqdm(donneesCSV.itertuples(),
			desc = "Remplissage de la base de données",
			unit = " adresses",
			total = nombre_adresses):
		# Récupérer les données de la ligne
		adr_id = ligne.Index
		adr_numero = ligne.numero
		adr_rep = ligne.rep
		adr_nom_voie = ligne.nom_voie
		vil_code_postal = ligne.code_postal
		vil_code_insee = ligne.code_insee
		vil_nom = ligne.nom_commune
		adr_longitude = ligne.lon
		adr_latitude = ligne.lat

		# Affichage de la ville en cours
		if vil_code_insee != ville_en_cours:
			ville_en_cours = vil_code_insee
			tqdm.write(Fore.BLUE + f"[*] Ville en cours : {vil_nom} ({vil_code_postal})..." + Style.RESET_ALL)

			# Insérer les données dans la table des villes si elles n'existent pas
			cursor.execute("""
				INSERT OR IGNORE INTO VILLES (VIL_CODE_INSEE, VIL_NOM, VIL_CODE_POSTAL)
				VALUES (?, ?, ?)
			""", (vil_code_insee, vil_nom, vil_code_postal))

			# Valider les modifications
			conn.commit()

		# Vérifier si l'adresse existe déjà dans la base de données
		cursor.execute("""
			SELECT COUNT(*) AS EXISTE, ADR_ALTITUDE
			FROM ADRESSES
			WHERE ADR_ID = ?;
		""", (adr_id,))
		reponse = cursor.fetchone()
		adresse_existe = reponse["EXISTE"]
		altitude_existe = reponse["ADR_ALTITUDE"]

		# Si l'adresse existe déjà, passer à la suivante
		if adresse_existe > 0 and altitude_existe is not None:
			continue
		else:
			# Récupérer l'altitude
			adr_altitude = recupAltitude(adr_latitude, adr_longitude)

			# Insérer les données dans la table des adresses
			cursor.execute("""
				INSERT OR REPLACE INTO ADRESSES (ADR_ID, ADR_NUMERO, ADR_REP, ADR_NOM_VOIE, ADR_LATITUDE, ADR_LONGITUDE, ADR_ALTITUDE, ADR_VIL_CODE_INSEE)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?);
			""", (adr_id, adr_numero, adr_rep, adr_nom_voie, adr_latitude, adr_longitude, adr_altitude, vil_code_insee))

	# Valider les modifications
	conn.commit()

	print(Fore.GREEN + "[+] Base de données remplie avec succès." + Style.RESET_ALL)

def recupAltitude(latitude: float, longitude: float) -> float:
	"""
	Utilise l'API de Google pour récupérer l'élévation.
	"""
	try:
		altitude = gmaps.elevation((latitude, longitude))
		return altitude[0]["elevation"]
	except Exception as e:
		print(Fore.RED + f"[!] Erreur lors de la récupération de l'altitude : {e}." + Style.RESET_ALL)
		return None

if __name__ == "__main__":
	# Vérifier si le fichier CSV existe
	if not os.path.exists(f"adresses-{scope}.csv"):
		recupCSV()

	# Créer la base si elle n'existe pas
	if not os.path.exists(f"adresses-{scope}.sqlite"):
		creerBDD()

	# Remplir la base de données
	remplirBDD()