# Moteur de recherche documentaire — LO17

*Ce dépôt présente l'implémentation d'un moteur de recherche sur un corpus de bulletins officiels en langue française, réalisé dans le cadre du cours LO17 à l'UTC. Le projet couvre l'ensemble de la chaîne de traitement : extraction du corpus, nettoyage, indexation, et interrogation, avec une interface web et une suite d'évaluation.*

---

## Présentation

Le projet suit un pipeline de traitement en quatre étapes, de l'analyse des documents HTML bruts jusqu'à la recherche en langage naturel. La chaîne repose sur des techniques classiques de recherche d'information : modèle TF-IDF, lemmatisation, correction orthographique, et extraction de dates pour le filtrage temporel.

Une interface web Flask permet d'effectuer des recherches, de parcourir le corpus, et d'annoter manuellement les résultats pour l'évaluation (précision, rappel, F-mesure).

---

## Contenu

| Module | Rôle |
| :--- | :--- |
| `scripts/1-parse_corpus.py` | Extraction du corpus HTML vers XML |
| `scripts/2-clean_data.py` | Nettoyage, tokenisation, calcul TF-IDF, anti-dictionnaire |
| `scripts/3-make_index.py` | Construction des index lemmatisés (TSV) |
| `scripts/4-moteur.py` | Interface de recherche en mode console |
| `app.py` | Application web Flask (recherche + annotation + évaluation) |
| `exercices-td/` | Scripts d'exercices pédagogiques (TD2 à TD6) |
| `src/` | Package Python `lo17_dm` (classes et modules réutilisables) |

---

## Installation

Ce projet utilise [uv](https://github.com/astral-sh/uv) pour la gestion de l'environnement virtuel et des dépendances.

**Installer uv** (si ce n'est pas déjà fait) :
```bash
pip install uv
```

**Cloner le dépôt et créer l'environnement virtuel** :
```bash
git clone https://github.com/cheerxe/lo17-dm.git
cd lo17-dm
uv venv
```

**Activer l'environnement virtuel** :
```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

**Installer les dépendances** :
```bash
uv sync
```

---

## Utilisation

### Mode console — pipeline complet

Les quatre scripts doivent être exécutés dans l'ordre. Le corpus HTML doit se trouver dans `data/BULLETINS/`.

```bash
python .\scripts\1-parse_corpus.py --indir .\data\BULLETINS\
python .\scripts\2-clean_data.py
python .\scripts\3-make_index.py
python .\scripts\4-moteur.py
```

### Mode application web

L'application lance automatiquement les étapes 1 à 3 si les fichiers de sortie sont absents (cela peut prendre un moment).

```bash
uv run app.py
```

L'interface est ensuite accessible à l'adresse [http://localhost:5000](http://localhost:5000). Elle permet de :
- lancer des requêtes en langage naturel avec filtrage par date et par type de document,
- parcourir les documents du corpus,
- annoter manuellement la pertinence des résultats,
- calculer les métriques d'évaluation (précision, rappel, F-mesure, temps de réponse).

---

## Exercices TD

Les scripts suivants reproduisent les résultats demandés dans les travaux dirigés :

```bash
python .\exercices-td\td2-determination_antidict.py   # Anti-dictionnaire et TF-IDF
python .\exercices-td\td3-make_stemmer_tabs.py         # Tables de lemmatisation (Spacy vs Snowball)
python .\exercices-td\td4-correcteur.py                # Correcteur orthographique et normalisation
python .\exercices-td\td6-evaluate.py                  # Évaluation précision / rappel / F1
```

---

## Architecture

```
lo17-dm/
├── data/               # Corpus brut (HTML)
├── outputs/            # Fichiers générés (XML, TSV, SQLite)
├── scripts/            # Pipeline principal (4 étapes)
├── exercices-td/       # Scripts pédagogiques
├── src/lo17_dm/        # Package Python (parseur, index, moteur, etc.)
├── templates/          # Templates HTML Flask
├── test_data/          # Requêtes de test
└── app.py              # Point d'entrée de l'application web
```
