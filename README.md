# AdressesFrance

Créer une base de données des adresses de toute la France.

Fichiers CSV télécharger par le script depuis l'adresse :
https://adresse.data.gouv.fr/data/ban/adresses/latest/csv

Documentation sur le format des fichiers CSV :
https://github.com/BaseAdresseNationale/adresse.data.gouv.fr/blob/master/public/schemas/adresses-csv.md

# Fonctionnement

## Création de l'environnement virtuel

Vous pouvez créer votre environnement virtuel avec Python :

**Sous Linux ou macOS :**

```bash
python3 -m venv .venv
```

**Sous Windows :**

```powershell
python -m venv .venv
```

## Basculer dans votre nouvel environnement virtuel

**Sous Linux ou macOS :**

```bash
source .venv/bin/activate
```

**Sous Windows :**

 - Dans **PowerShell** :
	```powershell
	.\.venv\Scripts\Activate.ps1
	```

 - Dans l'**Invite de commandes** :
	```batch
	.venv\Scripts\activate.bat
	```
## Installer les bibliothèques

Vous allez avoir besoin de plusieurs bibliothèques. Vous pouvez les Installer dans votre environnement virtuel avec **pip** :

```
pip install --requirement requirements.txt
```

## Spécifiction des variables d'environnement

Vous avez besoin de deux variables d'environnement à place dans un fichier ``.env`` à la racine du dépôt :

 - **``GOOGLE_API_KEY``** : Votre clé d'[API Google Maps Elevation](https://developers.google.com/maps/documentation/elevation/get-api-key).
 - **``SCOPE``** : Le numéro du département à traiter. Mettre ``france`` pour toute la France.
