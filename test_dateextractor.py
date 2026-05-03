from lo17_dm.DateExtractor import DateExtractor

date_extractor = DateExtractor()
test = "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?"
result = date_extractor.extract(test) 
print(result)