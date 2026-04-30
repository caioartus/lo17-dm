## Construction XML à partir du HTML

### Extraction des champs a partir du HTML

Pour extraire les différents champs des fichiers HTML nous avons utilisé les
chemins XPath qui permettent d'extraire les elements du DOM HTML. Pour ce faire nous utilisons etree (Element Tree) de la librairie lxml pour extraire les elements avec leur string XPath.
Cela a permis de très facilement les extraire en utilisant les outils d'inspection du browser.

Les commandes strip() et replace() sont utilisé pour eliminer les espaces, tabulations et autres caractères en début et fin de ligne, ainsi que pour extraire certaines informations comme le numero de bulletin qui est précédé tout le temps par la string "BE ..."

Dans des cas précis comme l'extraction des information de l'auteur un commande regex à été utilisée pour séparer les champs car ils avaient une strucutre bien définie.

Pour l'information de contact, la structure n'est pas bien définie donc nous ajoutons tout au XML.

### Formation du fichier XML

Nous utilisons etree de lxml pour construire le fichier html.

## Tokenisation

Separation du text selon " ", et '.'
Object CorpusTokeniser pour centraliser la logique en cas de changements.

- Nous vons choisi de ne pas utiliser le tiret comme un delimiteur mais simplement de l'enlever
arc-en-ciel devient arcenciel
## Anti-Dictionnaire

Choix de la granularité (document = article ou bulletin)

> 1 Document = 1 Article

Justification :

- Les bulletins n'ont pas vraiment de lien entre eux
- Filtrage probablement plus efficace


## Choix du seuil tf-idf

- Nous avons choisi le seuil de 0.7 de tf-idf moyen pour considérer un mot comme un stop word.
Ce seuil a été choisi après une analyse qualitative révélant que certains mots spécifiques commencent à apparaitre après ce seuil comme "laboratoire" "chercheurs" et "actualité".

- Il est a noté que ces mots restent très communs dans au vu du sujet des documents. De plus, certains mots clairement non intérréssants persistent même au dessus du seuil. Il s'agit d'un choix conservatif pour préserver au maximum les mots qui ont du sens au risk d'inclure des mots moins interressants.

#### Pourquoi sauvegarder en CSV entre les étapes ?

- Traçabilité : Tu peux vérifier chaque fichier, l’ouvrir, l’inspecter, le versionner.
- Reproductibilité : Si une étape change, tu ne recalcules pas tout depuis zéro.
- Séparation claire des tâches : Chaque fichier correspond exactement à une question du sujet.
- Compatibilité : CSV = lisible par n’importe quel outil (Excel, R, scripts bash, etc.).

## Analyse SpaCy vs SnowBall : 

Le corpus contient 14344 tokens unique avec notre méthode de séparation.

Avec le lemmatizeur SpaCy nous avons 11285 lemmes uniques;
Avec SnowBall nous avons 9046 racines uniques;
Ainsi SpaCy conserve une plus grande compléxité dans le text, chaque lemme correspond en moyenne moins de mots qu'une racine de SnowBall. 

En regardant la distribution de Pareto (% du dictonnaire nescessaire pour couvrir le x% du corpus) on peut voir la différence en distribution des différentes méthodes. On voit que les courbes sont globalements similaires, mais que le plus le dictionnaire est restreint le plus une petite partie des mots est sur-représenté et correspond a une grande partie du corpus. On a donc Snowball qui a la distribution la plus extrème suivi de proche par SpaCy. 

Il est intérréssant de noter que l'on voit bien que environ 20% des tokens représentent 80% du corpus, c'est le principe des 80-20.

Il faut tenir compte que nous avons appliqué les outils sur le corpus entier, avec les stop words toujours présentes.

![alt text](image.png)

## Choix

// TODO - Voir ce choix ensemble pour décider pour de vrai

Nous avons opté pour Spacy car celui ci garde mieux la nuance des termes. En effet quantitativement on observe que il y a plus de lemmes uniques, et qualitativement certains mots ne devrai pas être traités comme les même mais le sont avec le Stemmer Snowball (exemple optim fait référence a optimisation et optimiste, ce qui n'ont rien a voir).

Avec SpaCy on perd probablement en recall (il faut être plus précis dans sa recherche) mais on gagne en précision (moins de documents non pertinents.)

## Nouveaux stop words

En appliquant dans un notebook TF-IDF aux tableau des tokens transformés en lemmes avec SpaCy, nous observons l'emergence de nouveaux termes non intérréssants avec des faibles TF-IDF.
Par exemple 'permettre' avait un TD-IDF moyen de 0.92 avant la lemmatization. Après ce chiffre est passé à 0.42, représentant un très forte baisse.

Cela s'explique par le fait que avec la lemmatization les termes dérivés tels que 'permis', 'permettent', 'permet' etc. sont tous transformés à l'infinitif, augmentant ainsi la frequence d'appartition de 'permettre' a l'infinitif.

De même pour 'son', un terme qui n'était que très peu présent dans le corpus original mais qui englobe désormais les 'leurs', 'leur', 'sa' etc.

En maintenant le même seuil de $tf-idf \le 0.7$ nous parvenons à éliminer des nouveau mots non porteur de sens dans ce context.


## Construction de l'index inversé 

// TODO

### Amérliorations possibles

// TODO : Table de hachage, arbres binaires, B-Tree


## Traitement de l'input Autocorrecteur 

### Implémentation
// TODO

### Problème avec la solution initiale

Due à la condition du while dans l'agorithme de préfiltre, on stop la comparaison dés qu'une différence entre les deux chaines est trouvé. Concrétement c'est cette condition qui pose probleme `mot[i] == terme[i]` Ainsi si une erreur survient en début de mot, même si le reste du mot est très proche, il sera considéré comme loin car la boucle qui incrémente le nombre de lettre identiques se sera arrété avant d'aller au prochaines lettres.

```python
while i < min(len_m, len_t) and mot[i] == terme[i]: 
                i += 1
```

Par exemple prenon le mot **échange** :

Erreur en fin de mot : 
```bash
Input : échgne
Output : échange (super ça marche)
```

Erreur en début de mot : 
```bash
Input : echange
Output : erlangen (pas bon)
```

### Version corrigée

Il suffit d'enlever cette condition et comparer le mot en entier. Cela réduit la rapidité de la recherche car on parcour à chaque fois le mot en entier mais garanti de ne pas pénaliser trop fortement les fautes en début de mot.

Une approche plus subtile serait d'avoir un nombre d'erreurs authorisées avant d'arreter la comparaison. Ce seuil pourrait même être determiné selon la longeur du mot et le seuil minimal (seuilProx).

// TODO - faire mieux l'explication

```python
 i = 0
            ident = 0
            diff = 0
            maxlen = max(len_m, len_t)
            for i in range(min(len_m, len_t)):
                if mot[i] == terme[i]:
                    ident += 1
                else:
                    diff += 1

                perreur = (diff / maxlen) * 100

                if perreur > 100 - seuilProx:
                    break

```

## Moteur de recherche 

### A. Format des requêtes pour explorer le corpus indexé

Pour savoir à quoi ressemblera le processus qui sera exécuté à chaque requête, nous nous sommes  d'abord appuyés sur deux points :
* Il faut savoir ce que le moteur de recherche retourne
* Il faut savoir comment exprimer les conditions sur ce que l'on retourne.

Dans un premier temps, on peut noter d'après notre indexation du corpus que :
* Il n'existe qu'un petit nombre de catégories que notre moteur de recherche peut retourner (auteur, date, contact, bulletin, ...). En particulier, dans les exemples de requêtes, l'utilisateur ne peut vouloir qu'une liste d'articles, de bulletins, ou de rubriques.
* Notre unité documentaire est l'article. On ne peut réaliser les conditions que sur ces derniers. 

On retournera donc un dictionnaire :
```python
requete = {
    type_doc : # type des documents à retourner (articles, bulletins, ou rubrique)
    # --- Conditions sur l'article ---
}
```

Par ailleurs, d'après notre indexation, il n'existe qu'un nombre limité de conditions que l'on peut traiter (concernant la date, la rubrique, le titre, ou le contenu).

On retournera donc un dictionnaire :
```python
requete = {
    type_doc : # type des documents à retourner (articles, bulletins, ou rubrique)
    # --- Conditions sur l'article ---
    date_min :
    date_max :
    anti_date_min : 
    anti_date_max :
    rubrique :
    anti_rubrique : 
    titre : 
    anti_titre : 
    contenu :
    anti_contenu :
}
```

A noter que seul `type_doc` ne peut pas être vide et doit être unique puisque le moteur de recherche doit savoir quoi retourner.

Pour ce qui concerne les conditions sur les articles, il peut y en avoir plusieurs dans une même catégorie coordonnées par différents oppérateurs logiques. On choisit donc un format sous forme de liste de liste interprété commu une DNF (ie. `[[A,B], [C], [D,E,F]] = (A^B) v C v (D^E^F)`)

### B. Traitement des requête NLP selon le format

#### 0. Exploration de stratégies pour le traitement des requêtes

Ce projet nous a principalement permis de comprendre à quel point il était périlleux de traiter des requêtes NLP. En effet, nous avons relevé plusieurs cas qui posent problème.

Dans un premier temps nous avons cherché à traiter le sens sémantique des phrases. Pour ce faire, on souhaitait se reposer sur la structure grammaticale des phrases. De cette manière nous aurions pu mettre en corrélation les sujet et les compléments à partir des verbes, tout en étant en capacité d'appliquer les opérateurs logique en fonction de leur place dans la structure grammaticale.

Le problème est que spacy n'était pas très bon et trop lent pour traiter ceci [insérer code exemple 9 avril].

Nous avons ensuite réfléchi à plusieurs stratégies pour corriger les erreurs de spacy, et encore à d'autres en se passant de spacy, mais aucune stratégie n'était réellement concluante. 

On a donc changé de paradigme pour se concentrer sur l'objectif d'obtenir un moteur de recherche efficace pour traiter n'importe quelle **requête qui ressemblerait à celles fournies**. De cette manière, on peut s'appuyer sur les différents schémas linguistiques que l'on voit apparaitre dans les exemples afin de réfléchir à la conception de notre traiteur de requêtes, qui sera ensuite mobilisé dans le moteur de recherche.

Plutôt que de traiter toute la requête en une seule fois, on décide donc de traiter séquentiellement et dans un ordre précis (correspondant à celui du dictionnaire donné en exemple) chaque condition qui se trouve dans notre dictionnaire. De plus, à chaque fois que l'on traitera une condition, on retirera les mots-clés correspondant à cette condition, afin de filtrer petit à petit la requête.

#### 1. Trouver les types de documents à retourner 

La première condition que l'on traite concerne les types de documents à retourner. En effet, d'après les exemples de requête fournis, on peut voir qu'il suffit de vérifier quel est le mot qui apparait en premier entre article, recherche et bulletin pour savoir ce que l'on doit retourner. En effet, on peut supposer que lorsqu'un utilisateur rédige une requête, il a tendance à mettre en premier le genre de document qu'il cherche.

Ainsi, par exemple, pour les requêtes suivantes, on retournera : 

> "Dans quelles rubriques trouve-t-on des articles sur l’alimentation ?"

```requete = {type_doc : rubrique, ... (condition sur l'article)}```

> "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin."

```requete = {type_doc : bulletins, ... (condition sur l'article)}```

> "Afficher la liste des articles qui parlent des systèmes embarqués dans la rubrique Horizons Enseignement."

```requete = {type_doc : articles, ... (condition sur l'article qui concerne la rubrique)}```

*Rappel : Les conditions sont sur l'article car l'unité documentaire est l'article* 

On suppose également que si l'utilisateur n'indique aucun de ces 3 mots, alors il cherche un article. Par exemple, la requête suivante retournera :

> " Je cherche les recherches sur l’aéronotique."

```requete = {type_doc : articles, ... (condition sur l'article)}```

#### 2. Trouver les conditions sur la date 

// TO-DO Je ne sais pas vraiment ce que t'as fait 

On retournera donc un dictionnaire :
```python
requete = {
    type_doc : ...,
    date_min : date # vide ou date au format dd/mm/jj
    date_max :
    anti_date_min : 
    anti_date_max :
    # --- Reste des conditions sur l'article ---
}
```

> **En vrai je suis pas sûre de comment t'as formulé la date mais mets ce que t'as mis**

Ainsi, par exemple, pour les requêtes suivantes, on retournera : 

> "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?"

```requete = {type_doc : articles, date_min : 03/03/2013, date_max : 04/05/2013, ... }```

> "Rechercher tous les articles sur le CNRS et l’innovation à partir de 2013"

```requete = {type_doc : articles, date_min : **/**/2013, ...}``` 

> "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin."

```requete = {type_doc : bulletins, date_min : **/**/2012, date_max : **/**/2013, antidate : **/06/**, ... }```

*Note : Notre moteur de recherche ne traite pas le cas où il y a plusieurs intervale de temps autorisé (par exemple "de 2008 à 2012 ou de 2016 à 2020"), puisque cela n'était pas inscrits dans les exemples de requêtes. En effet, on pourrait supposer qu'un utilisateur qui voudrait filtrer selon deux intervales de temps le ferait en deux requêtes.*

#### 3. Trouver les conditions sur la rubrique

L'avantage des rubriques est qu'il n'en existe pas beaucoup. On peut donc vérifier, pour chaque requête concernant une rubrique, de quelle rubrique il s'agit. 

De plus, chaque rubrique est autoexcluante (on ne peut pas vouloir un article qui se trouve à la fois dans la rubrique A et dans la rurique B). 

On retournera donc un dictionnaire :
```python
requete = {
    type_doc : ...,
    rubrique : [[A],[B]] # A ou B (jamais A et B -> car rubrique auto-excluante)
    anti_rubrique : [[A,B]] # A et B (règle de Morgan)
    # --- Reste des conditions sur l'article ---
}
```

D'après les requêtes qui ont été fournies, pour récupérer les conditions sur les rubriques, il suffit donc de vérifier si le document mentionne le terme "rubrique".

**Remarque** : Si l'utilisateur a inscrit rubrique en premier dans sa recherche, on considère qu'il cherche une rubrique, et on retire le mot "rubrique" lors de la première étape.

A chaque fois, on pourra alors récupérer tous les mots qui suivent le terme rubrique, et si l'on rencotre un "ou", on ajoutera 

Ainsi, par exemple, pour les requêtes suivantes, on retournera : 

> "Afficher les articles de la rubrique en direct des laboratoires."

```requete = {type_doc : articles, rubrique : "en direct des laboratoires", ...}``` 

> "Je voudrais les articles de la rubrique Focus mentionnant un laboratoire"

```requete = {type_doc : articles, rubrique : "Focus", ...} # "mentionnant" detecté comme pas_une_rubrique``` 

> "Je souhaites avoir tout les articles donc la rubrique est focus ou Actualités Innovations et qui contiennent les mots chercheurs et paris"

```requete = {type_doc : articles, rubrique : [["Focus"], ["Actualités Innovations"]], ...} # "mentionnant" detecté comme pas_une_rubrique``` 

// TO-DO dans index_rubrique.tsv, il y a un seul article dans "Actualités Innovations" et plusieurs dans "Actualité Innovations" (sans s), est-ce qu'on prend les deux dans la requête ?

> "Je voudrais tout les articles provenant de la rubrique événement et contenant le mot congres dans le titre.

```requete = {type_doc : articles, rubrique : "événement", ...}``` 

> "Je souhaite les rubriques des articles parlant de nutrition ou de vins."

```requete = {type_doc : rubriques, rubrique : , ...}``` 

#### 4. Trouver les conditions sur le titre et sur le contenu

On a remarqué dans les requêtes fournies que lorsque l'utilisateur souhaitait mettre une condition sur le titre et sur le contenu, il mentionnait explicitement le terme "titre" et "contenu".

De cette manière, pour traiter ces conditions, nous avons choisi de :
```python
```

> "Je voudrais tout les articles provenant de la rubrique événement et contenant le mot congres dans
le titre"
*  Quels sont les articles dont le titre contient biocarburant ou le contenu parle des bioénergies ?


### Structure de la requete 

Liste de liste en DNF : [[A,B], [C], [D,E,F]] = (A^B) v C v (D^E^F)

{  
    date_min :
    date_max :
    rubrique : [[A],[B]] # A ou B (jamais A et B -> car rubrique auto-excluante)
    titre : [[A,B]] # A et B (jamais A ou B -> d'après le corpus)
    contenu : [...] # mots-clés en DNF
}

On retournera donc un dictionnaire :
```python
requete = {
    type_doc : # type des documents à retourner (articles, bulletins, ou rubrique)
    # --- Conditions sur l'article ---
    date_min : date # date au format dd/mm/jj
    date_max :
    anti_date_min : 
    anti_date_max :
    rubrique : [[A],[B]] # A ou B (jamais A et B -> car rubrique auto-excluante)
    anti_rubrique : [[A,B]] # A et B (règle de Morgan)
    titre : [[A,B]] # A et B (jamais A ou B -> d'après le corpus)
    anti_titre : [[A],[B]] # A ou B (règle de Morgan)
    contenu : [...] # mots-clés en DNF
    anti_contenu :
}
```