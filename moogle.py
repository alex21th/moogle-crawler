import pickle
import urllib.request
from bs4 import BeautifulSoup
import unicodedata
from urllib.parse import urljoin
from collections import deque


def clean_word(word):
    '''Returns the longest prefix of a word made of latin unicode
       characters.'''
    for i, c in enumerate(word):
        if not unicodedata.name(c).startswith("LATIN"):
            return word[:i].lower()
    return word.lower()


def clean_words(words):
    """Cleans all words in a string."""
    return " ".join(map(clean_word, words.split()))


#############################################################################
# Common part
#############################################################################


def authors():
    """Returns a string with the name of the authors of the work."""

    # Please modify this function

    return "Alex Carrillo"


#############################################################################
# Crawler
#############################################################################


def store(db, filename):
    with open(filename, "wb") as f:
        print("store", filename)
        pickle.dump(db, f)
        print("done")


def crawler(url, maxdist):
    """
        Crawls the web starting from url,
        following up to maxdist links
        and returns the built database.
    """

    # Diccionari que associa una paraula a la llista de pàgines en les quals
    # apareix.
    diccionari = {}
    # Diccionari que associa cada pàgina a la seva distància respecte l'orígen.
    distancia = 0                # (el node principal té distància 0)
    visitats = {url: distancia}  # (marquem la pàgina inicial com a visitada)
    # Cua en la qual es van afegint les pàgines veïnes d'una pàgina.
    cua = deque([url])           # (afegim la pàgina inicial a la cua)

    # Analitzem les pàgines mentre hagin elements a la cua.
    while cua:
        # Guardem el primer element 'url' i l'eliminem de la cua.
        url = cua.popleft()

        # Intentem d'obtenir informació de la pàgina.
        try:
            response = urllib.request.urlopen(url)
            page = response.read()
            soup = BeautifulSoup(page, "html.parser",
                                 from_encoding="iso-8859-1")
            # Obtenim el títol.
            titol = clean_words(soup.title.string)
            # Obtenim el text.
            text = clean_words(soup.get_text()).split()
            # Establim la puntuació (nombre d'aparicions d'una paraula en una
            # pàgina).
            puntuacio = 1.0

            print("_________________________")
            print(" Analitzant la pàgina...")     # Imprimim per pantalla
            print('')                             # la informació que hem
            print("  ➤    TÍTOL:   ", titol)      # obtingut.
            print('')
            print("  ➤      URL:   ", url)
            print('')
            print("  ➤ PARAULES:   ", len(text), "         ",
                  text[0], " ... ", text[-1])
            print('')

            # Analitzem cada paraula que apareix a la pàgina.
            for paraula in text:
                # Establim la informació que tindrà cada pàgina.
                pag = {"score": puntuacio, "title": titol}
                # Creem un nou diccionari si la paraula és nova.
                if paraula not in diccionari:
                    diccionari[paraula] = {}
                # Si ja havíem guardat la página en la qual apareix la paraula
                # vol dir que es repeteix, així que incrementem la puntuació.
                if url in diccionari[paraula]:
                    diccionari[paraula][url]["score"] += 1
                # Altrament, associem a la pàgina (associada a la paraula) la
                # informació de títol i puntuació.
                else:
                    diccionari[paraula][url] = pag

        # En cas que es produeixi alguna excepció mostrem un missatge d'error.
        except:
            print("_________________________")
            print(" No s'ha pogut anal·litzar la pàgina.")
            print('')
            print("  ➤      URL:   ", url)

        # Per a cada pàgina veïna (enllaç), si no ha estat visitada, la afegim
        # a la cua i la marquem com a visitada.
        if visitats[url] <= maxdist:
            # Trobem tots els enllaços de la pàgina que estem visitant.
            enllacos = soup.find_all("a")
            print("  ➤ ENLLAÇOS:   ", len(enllacos))
            # Donem el format correcte a cada enllaç.
            for link in enllacos:
                enllac = urljoin(url, link.get("href"))
                # Si no hem visitat un enllaç, l'afegim a la cua.
                if enllac not in visitats:
                    print("                   • ", enllac)
                    cua.append(enllac)
                    # Assignem la profunditat corresponent a l'enllaç.
                    visitats[enllac] = distancia + 1
            # Augmentem el nivell de profunditat.
            distancia += 1

        print('')
        print("                 Queden", len(cua), "pàgines per analitzar.")

    # Mostrem un missatge quan finalitza el crawler.
    print("======================================")
    print(" El crawler ha finalitzat amb èxit! ☺")
    print("======================================")
    return diccionari


#############################################################################
# Answer
#############################################################################


def load(filename):
    """Reads an object from file filename and returns it."""
    with open(filename, "rb") as f:
        print("load", filename)
        db = pickle.load(f)
        print("done")
        return db


def answer(db, query):
    """
        Returns a list of pages for the given query.

        Each page is a map with three fields:
            - title: its title
            - url: its url
            - score: its score

        The list is sorted by score in descending order.
        The query is a string of cleaned words.
    """

    # Creem una llista de les paraules consultades
    # (i una còpia per a més tard).
    paraules = query.split()
    copia_paraules = paraules
    # Descartem les paraules repetides en la consulta.
    repetides = set(paraules)   # ex. "bus bus bus" → "bus"
    paraules = list(repetides)

    # Intentem obtenir les consultes de les paraules.
    try:
        # Per a múltiples paraules trobem les pàgines que es trobin en la
        # intersecció (és a dir, que continguin totes les paraules demanades).
        if len(paraules) > 1:
            # Agafem la primera paraula i l'eliminem de la llista.
            a = db[paraules[0]]
            del(paraules[0])
            # Treballem amb les paraules restants.
            while paraules:
                # Agafem la següent paraula.
                b = db[paraules[0]]
                # Calculem la intersecció de la consulta d'ambdues paraules.
                interseccio = a.keys() & b.keys()
                # Si no hi ha intersecció, abandonem.
                if not interseccio:
                    break
                # Reassignem l'última paraula i l'eliminem de la llista.
                a = b
                del(paraules[0])

            # Muntem la llista de pàgines amb el format correcte:
            # ex. {'score': 1.0, 'title': 'Index', 'url': 'http://index.html'}
            respostes = []
            for paraula in copia_paraules:
                for pag in interseccio:
                    web = {"title": db[paraula][pag]["title"],
                           "url": pag,
                           "score": db[paraula][pag]["score"]}
                    respostes.append(web)

            # Ordenem la llista de respostes alfabèticament segons les URLs.
            resp_ordenades_url = sorted(respostes, key=lambda k: k["url"])

            # Sumem les puntuacions de les pàgines (URLs) repetides.
            resp_suma_puntuacio = []
            # Afegim la primera pàgina (URL) i l'eliminem de la llista.
            resp_suma_puntuacio.append(resp_ordenades_url[0])
            del(resp_ordenades_url[0])
            # Recorrem les pàgines restants.
            for pag in resp_ordenades_url:
                # Si no hem ficat encara la pàgina, sumem les puntuacions.
                if not pag["url"] in resp_suma_puntuacio[-1]["url"]:
                    resp_suma_puntuacio.append(pag)
                # Altrament, fiquem la pàgina en la llista de respostes.
                else:
                    resp_suma_puntuacio[-1]["score"] += pag["score"]

        # Si la consulta és d'una sola paraula.
        else:
            # Muntem la llista de pàgines amb el format correcte:
            # ex. {'score': 1.0, 'title': 'Index', 'url': 'http://index.html'}
            resp_suma_puntuacio = []
            llista = db[paraules[0]]
            for pag in llista:
                web = {"title": llista[pag]["title"],
                       "url": pag,
                       "score": llista[pag]["score"]}
                resp_suma_puntuacio.append(web)

        # Ordenem la llista de respostes segons la puntuació de cadascuna.
        resp_ordenades_puntuacio = sorted(resp_suma_puntuacio,
                                          key=lambda k: k["score"],
                                          reverse=True)

        # Retornem la llista de respostes ordenada decreixentment segons la
        # puntuació de cada pàgina.
        return resp_ordenades_puntuacio

    # En cas que es produeixi alguna excepció (no existexi cap pàgina amb les
    # paraules consultades) retornem una llista buida.
    except:
        print("La cerca '", query, "' no ha obtingut cap resultat.")
        return []
