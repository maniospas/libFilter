import re

import requests
from tqdm import tqdm
from lxml import html
import json, os
from nltk.stem import PorterStemmer
import nltk
import networkx as nx
from threading import Lock
import requests
from threading import Lock
from lxml import html  # only needed if your Package class still uses it internally

# ---- NEW: fetch all names from the Simple API ----
try:
    resp = requests.get("https://pypi.org/simple/", timeout=30)
    resp.raise_for_status()
except Exception as e:
    print("Failed to retrieve PyPI simple index:", e)

# extract package names from the simple index HTML
# each line is like: <a href='...'>package-name</a>
all_names = []
for line in resp.text.splitlines():
    if "<a href=" in line:
        start = line.find('>') + 1
        end = line.find('</a>', start)
        if start > 0 and end > start:
            all_names.append(line[start:end])


graph_creation_lock = Lock()
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
from nltk.corpus import wordnet
stopwords = set(nltk.corpus.stopwords.words('english'))

def synonym_stems(word):
    """Return a set of stemmed WordNet synonyms for a single word."""
    syns = set()
    for synset in wordnet.synsets(word):
        for lemma in synset.lemmas():
            for token in lemma.name().split("_"):
                syns.add(stemmer.stem(token.lower()))
    return syns



def to_personalization(text, accepted):
    ret = dict()
    for word in prepare_for_split(text).split(" "):
        word = word.lower()
        if len(word) > 0:
            synonyms = [word]+[token for synset in wordnet.synsets(word) for lemma in synset.lemmas() for token in lemma.name().split("_")]
            if len(synonyms) > float('inf'):
                word = stemmer.stem(word)
                ret[word] = ret.get(word, 0) + 1
                continue

            synonyms = set([stemmer.stem(word) for word in synonyms])
            synonyms = [word for word in synonyms if word in accepted]
            if len(synonyms) > 0:
                for word in synonyms:
                    ret[word] = ret.get(word, 0) + 1#./len(synonyms)
    return ret


class Nostem:
    def stem(self, word):
        return word.lower()

stemmer = PorterStemmer()

#stemmer = Nostem()


def prepare_for_split(ret):
    ret = ret.replace("/", " ")
    ret = ret.replace("\\", " ")
    ret = ret.replace("-", " ")
    ret = ret.replace("_", " ")
    ret = ret.replace("-", " ")
    ret = ret.replace(".", " ")
    ret = ret.replace("2", " ")
    ret = ret.replace("|", " ")
    ret = ret.replace(":", " ")
    ret = ret.replace(".", " ")
    ret = ret.replace("(", " ")
    ret = ret.replace(")", " ")
    ret = ret.replace("[", " ")
    ret = ret.replace("]", " ")
    ret = ret.replace("<", " ")
    ret = ret.replace(">", " ")
    ret = ret.replace("=", " ")
    return ret


def tokenize(text, stem=True, include_empty=False):
    if include_empty: return ["" if word.lower() in stopwords and stem else stemmer.stem(word) if stem else word for word in prepare_for_split(text).split(" ") if len(word) > 0]
    return [stemmer.stem(word) if stem else word for word in prepare_for_split(text).split(" ") if len(word) > 0 and word.lower() not in stopwords]


class Package:
    def __init__(self, info):
        self.name = info["name"].lower()
        self.keywords = info.get("keywords", list())
        if self.keywords is None:
            self.keywords = list()
        self.summary = info.get("summary", "")
        self.description = info.get("description", "")
        self.dependencies = info.get("requires_dist", [])
        self.dependencies = list() if self.dependencies is None else [
            dependency.split("(")[0].strip().split("[")[0].strip().split(" ")[0].strip().split(";")[0].strip()
                .split(">")[0].strip().split("<")[0].split("~")[0].split("=")[0].strip() for dependency in self.dependencies]
        self.dependencies = [dependency.lower() for dependency in self.dependencies if dependency != "extra"]
        self.info = info
        self.homepage = self.info.get("home_page", "")
        if self.homepage is None or len(self.homepage) == 0:
            self.homepage = ""
            urls = self.info.get("project_urls")
            if urls is not None:
                for k, v in urls.items():
                    if "home" in k.lower():
                        self.homepage = v
        if self.summary is None or len(self.summary) == 0:
            homepage = self.homepage
            if homepage is not None and len(homepage) > 0 and "github.com/" in homepage:
                print("Retrieving summary from", homepage)
                import requests
                x = requests.get(homepage)
                from bs4 import BeautifulSoup
                lines = [line.strip() for line in BeautifulSoup(x.text, parser="lxml", features="lxml").get_text().split("\n") if len(line.strip()) > 0]
                about = None
                for line in lines:
                    if about is not None:
                        if line == "Topics" or line == "Resources" or line=="Stars" or line=="Readme" or line=="License":
                            break
                        about += line+"\n"
                    if line == "About":
                        about = ""
                if about is not None:
                    self.summary = about
                    self.info["summary"] = self.summary

        if self.description is None or len(self.description) == 0:
            homepage = self.homepage
            if homepage is not None and len(homepage) > 0 and "github.com/" in homepage:
                try:
                    print("Retrieving readme from", homepage)
                    import requests
                    x = requests.get(homepage.replace("github.com/", "raw.githubusercontent.com/")+ "/master/README.md")
                    if x.status_code != 200:
                        x = requests.get(homepage.replace("https://github.com/", "https://raw.githubusercontent.com/")+ "/main/README.md")
                    self.description = x.text
                    self.info["description"] = self.description
                except Exception as e:
                    print(str(e))
                    self.description = " "
                    self.info["description"] = self.description

    def text(self):
        ret = self.name+" "+((" ".join(self.keywords)) if self.keywords is not None else "")+" "+(self.summary if self.summary is not None else "")
        #if self.description is not None:
            #ret += " "+self.description
            #ret += " "+self.description[:min(len(self.description), 5000)]
        return prepare_for_split(ret)


class Packages:
    def __init__(self, filename="pypi.json"):
        self.packages = dict()
        self.filename = filename
        self.load(filename)

    def copy(self):
        ret = Packages(None)
        ret.packages = self.packages

    def unique(self):
        homepages = dict()
        for package in self.packages.values():
            if len(package.homepage) > 0:
                if package.homepage not in homepages or len(package.name) < len(homepages[package.homepage].name):
                    homepages[package.homepage] = package
                homepages[package.homepage] = package
        prev_packages = self.packages
        self.packages = {package.name: package for package in homepages.values()}
        for package in self.packages.values():
            package.dependencies = [homepages[prev_packages[dependency].homepage].name
                                    for dependency in package.dependencies
                                    if dependency in prev_packages
                                    and len(prev_packages[dependency].homepage) > 0
                                    and prev_packages[dependency].homepage in homepages]
        return self

    def all(self): return self.packages.values()

    def load(self, filename="pypi.json"):
        self.filename = filename
        if filename is None:   return
        if not os.path.exists(filename): return
        with open(filename, "r") as file:
            for info in json.load(file):
                if info["name"].lower() in self.packages: print("WARNING: Duplicate package "+info["name"].lower())
                self.packages[info["name"].lower()] = Package(info)
        print("Loaded", len(self.packages), "packages")

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        if filename is None:
            return
        self.filename = filename
        with open(filename, "w") as file:
            file.write(json.dumps([package.info for package in self.packages.values()]))

    graph_creation_lock = Lock()  # keep your existing lock

    from tqdm import tqdm

    def synonym_stems(word):
        """Return a set of stemmed WordNet synonyms for a single word."""
        syns = set()
        for synset in wordnet.synsets(word):
            for lemma in synset.lemmas():
                for token in lemma.name().split("_"):
                    syns.add(stemmer.stem(token.lower()))
        return syns

    def search(self, keyword, max_new, max_distance=2, update=None):
        """
        Search for packages whose name contains any of the query words
        (case-insensitive), expand query words with WordNet synonyms,
        and recursively walk their dependencies up to `max_distance`.
        Results are sorted by how many of the query+synonym words match.
        """
        query_words = keyword.lower().split()
        expanded_query = set()
        for w in query_words:
            expanded_query.add(stemmer.stem(w))
            expanded_query |= synonym_stems(w)
        pending = []
        distance = {}
        scored_matches = []
        for name in all_names:
            words = set(stemmer.stem(x) for x in prepare_for_split(name).split())
            score = len(words & expanded_query)
            if score > 0:
                scored_matches.append((score, name))
        scored_matches.sort(reverse=True, key=lambda x: x[0])
        matching = [name for _, name in scored_matches]
        if len(matching) > max_new:
            matching = matching[:max_new]
        pending.extend(matching)
        distance.update({name.lower(): 0 for name in matching})
        if update is not None:
            update(0, len(matching), "Searching for related packages to analyze")
        remaining_original = set(matching)
        total = len(remaining_original)
        with tqdm(total=total, desc="Searching PyPI") as pbar:
            while pending:
                name = pending.pop().lower()
                if name in remaining_original:
                    remaining_original.remove(name)
                    pbar.update(1)
                if update is not None and total:
                    done = total - len(remaining_original)
                    update(done, total, "Indexing new packages: "+name,
                           str(len(self.packages))+"/" +str(len(all_names))+" indexed")
                if distance[name] > max_distance:
                    continue
                if name in self.packages:
                    package = self.packages[name]
                else:
                    try:
                        info = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=5).json()["info"]
                        package = Package(info)
                        print("New:", name, distance[name])
                        with graph_creation_lock:
                            self.packages[package.name] = package
                    except Exception as e:
                        print("Failed to retrieve", name, "from pypi.org:", e)
                        continue
                for dependency in package.dependencies:
                    prev = distance.get(dependency, float('inf'))
                    next_d = distance[name] + 1
                    if next_d < prev:
                        distance[dependency] = next_d
                        pending.append(dependency)
        self.save(self.filename)

    def dependencies(self, packages=None):
        if packages is None:
            packages = list(self.all())
        pairs = [(self.packages[package.name], self.packages[dependency])
                 for package in packages
                 for dependency in package.dependencies
                 if dependency in self.packages]
        return pairs

    def create_graph(self, packages=None, words=True, from_dependencies=True, weight=lambda tf, df: tf, direct_links=False):
        with graph_creation_lock:
            if packages is None:
                packages = list(self.all())
            if not words:
                return nx.Graph(self.dependencies(packages))
            homepagedict = dict()
            if not from_dependencies:
                word_dependencies = [(package, stemmer.stem(word))
                                     for package in packages
                                     for word in tokenize(package.text())]
            else:
                word_dependencies = [(self.packages[dependency], stemmer.stem(word))
                                     for package in packages
                                     for word in tokenize(package.text())
                                     for dependency in package.dependencies
                                     if dependency in self.packages
                                     ]
            dependencies = word_dependencies

        if weight is None:
            return nx.Graph(dependencies)

        edges = dict()
        for u, v in dependencies:
            edge_id = str(str(u)) + "-" + str(str(v))
            if edge_id in edges:
                edges[edge_id] = (edges[edge_id][0], edges[edge_id][1]+1)
            else:
                edges[edge_id] = ((u, v), 1)

        frequencies = dict()
        for edge, w in edges.values():
            word = edge[1]
            frequencies[word] = frequencies.get(word, 0) + 1

        if direct_links:
            dependencies += [((package, dependency), float(direct_links)) for package in packages for dependency in package.dependencies if dependency in self.packages]
        """
        for package in packages:
            for word in tokenize(package.text()):
                for synset in wordnet.synsets(word):
                    word_stem = stemmer.stem(word.lower())
                    for lemma in synset.lemmas():
                        for lemma_word in lemma.name().split("_"):
                            lemma_stem = stemmer.stem(lemma_word.lower())
                            if lemma_stem != word_stem and lemma_stem in frequencies:
                                dependencies.append(((word_stem, lemma_stem), 1.))
        """

        return nx.Graph([(*edge, {'weight': weight(w, frequencies[edge[1]]) if edge[1] in frequencies else w}) for edge, w in edges.values()])
