from typing import Literal

class Film:
    nom: str
    date: int
    lieu: list[Literal["Bibliothèque", "Chez un ami"]]
    type: list[Literal["VHF", "DVD"]]


class Bibliotheque:
    Films : list[Film] = []
    
    def trierBibliotheque(self) -> list[Film]:
        return sorted(self.Films, key=lambda film: film.type)
    def __init__(self):
        pass
    def getFilm(self, nom: str) -> Film | None:
        for film in self.Films:
            if film.nom == nom:
                return film
        return None

class Ami:
    nom: str | None = None
    Films : list[Film] = []
    def __init__(self, nom: str | None = None):
        self.nom = nom
    

class FilmsPretes:
    Films : list[Film] = []

    def __init__(self, Films: list[Film] = []):
        pass

    def filmsPretesAmi(self, ami: Ami) -> list[Film]:
        return [film for film in self.Films if film in ami.Films]
    def nomAmi(self, Film: str) -> str | None:
        for ami in amis:
            for film in ami.Films:
                if film.nom == Film:
                    return ami.nom
        return None 
        
if __name__ == "__main__":
    biblio = Bibliotheque()
    Films = [

    ("Blade Runner (1982)", "vhf"),

    ("Alien : Le 8ème Passager (1979)", "vhf"),

    ("2001 : L'Odyssée de l'espace (1968)", "VhF"),

    ("Matrix (1999)", "DVD"),

    ("Interstellar (2014)", "dvD"),

    ("L'Empire contre-attaque (1980)", "vhf"),

    ("Retour vers le futur (1985)", "vhf"),

    ("La Guerre des Étoiles (1977)", "vhf"),

    ("L'Armée des 12 singes (1995)", "dVd"),

    ("Terminator 2 : Le Jugement dernier (1991)", "DVD"),

    ]



    Amis = [

    ("Paul", "Blade Runner"),

    ("Lucie",),

    ("Zoé", "Terminator 2 : Le Jugement dernier"),

    ] 

    
    test = FilmsPretes()
    test2 = test.filmsPretesAmi(Amis[0])
    test3 = test.nomAmi("Blade Runner")
    for i in range(len(Films)):
        Movies[i].nom = Films[i][0]
        Movies[i].type = Films[i][1].upper()
        biblio.Films.append(Movies[i])
    for j in range (len(Amis)):
        Friends[j].nom = Amis[j][0]
        for k in range(1, len(Amis[j])):
            film_trouve = biblio.getFilm(Amis[j][k])
            if film_trouve:
                Friends[j].Films.append(film_trouve)

    test.Films = Movies



    