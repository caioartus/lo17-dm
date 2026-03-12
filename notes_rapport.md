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

## Anti-Dictionnaire

-
