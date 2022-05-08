import requests
from lxml import html
import json, os
from nltk.stem import PorterStemmer
import nltk
import networkx as nx


nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))
stemmer = PorterStemmer()


def tokenize(text, stem=True):
    return [stemmer.stem(word) if stem else word for word in text.split(" ") if len(word) > 0 and word.lower() not in stopwords]


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
                .split(">")[0].strip().split("<")[0].strip() for dependency in self.dependencies]
        self.dependencies = [dependency.lower() for dependency in self.dependencies if dependency != "extra"]
        self.info = info

    def text(self):
        ret = self.name+" "+((" ".join(self.keywords)) if self.keywords is not None else "")+" "+(self.summary if self.summary is not None else "")#+" "+self.description
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


class Packages:
    def __init__(self, filename="pypi.json"):
        self.packages = dict()
        self.filename = filename
        self.load(filename)

    def all(self):
        return self.packages.values()

    def load(self, filename="pypi.json"):
        self.filename = filename
        if not os.path.exists(filename):
            return
        with open(filename, "r") as file:
            for info in json.load(file):
                self.packages[info["name"].lower()] = Package(info)
        print("Loaded", len(self.packages), "packages")

    def save(self, filename="pypi.json"):
        with open(filename, "w") as file:
            file.write(json.dumps([package.info for package in self.packages.values()]))

    def search(self, keyword, max_pages=1, max_distance=2, update=None):
        pending = list()
        distance = dict()
        for page in range(max_pages):
            tree = html.fromstring(requests.get("https://pypi.org/search/?q="+keyword+"&page="+str(page)).text)
            pending.extend([package.text for package in tree.xpath("//span[contains(@class, 'package-snippet__name')]")])
            if update is not None:
                update(page, max_pages)
            distance = distance | {package.lower(): 0 for package in pending}
            while pending:
                name = pending.pop(0).lower()
                if distance[name] > max_distance:
                    continue
                if name in self.packages:
                    #print(name, distance[name])
                    package = self.packages[name]
                else:
                    try:
                        package = Package(requests.get("https://pypi.org/pypi/" + name + "/json").json()["info"])
                        print(name, distance[name], " (new)")
                        self.packages[package.name] = package
                    except:
                        print("Failed to retrieve", name, "from pypi.org")
                for dependency in package.dependencies:
                    prev_distance = distance.get(dependency, float('inf'))
                    next_distance = distance[name] + 1
                    if next_distance < prev_distance:
                        distance[dependency] = next_distance
                        pending.append(dependency)
        self.save(self.filename)

    def dependencies(self, packages=None):
        if packages is None:
            packages = self.all()
        pairs = [(self.packages[package.name], self.packages[dependency])
                 for package in packages
                 for dependency in package.dependencies
                 if dependency in self.packages]
        return pairs

    def create_graph(self, packages=None, words=True, from_dependencies=True):
        if packages is None:
            packages = self.all()
        if not words:
            return nx.Graph(self.dependencies(packages))
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
        return nx.Graph(dependencies)
