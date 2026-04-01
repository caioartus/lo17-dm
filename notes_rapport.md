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

Separation du text selon " ", "-" et '.
Object CorpusTokeniser pour centraliser la logique en cas de changements.

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

Il faut tenir compte que nous appliqué les outils sur le corpus entier, avec les stop words toujours présentes.

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