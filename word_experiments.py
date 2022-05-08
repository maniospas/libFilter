from pypigraph import Packages, tokenize
from graph_filter import SymmetricAbsorbingRandomWalks
from utils.measures import Evaluator
import pygrank as pg

"""
query = "image machine learning"
packages = Packages()
packages.search(query, max_pages=3, max_distance=2)
print(len(packages.dependencies()), "package dependencies")
personalization = {stemmer.stem(word): 1. for word in tokenize(query)}
recs = SymmetricAbsorbingRandomWalks()(graph, personalization)
top = [package.name for package in sorted(packages.all(), key=lambda project: -recs.get(project,0))[:10]]
"""

packages = Packages()
train, test = pg.split(packages.all(), 0.2)
graph = packages.create_graph(train)
evaluator = Evaluator(5, packages.all())
nodes = set(graph)
app_libs = [lib for lib in train if lib in nodes]
algorithm = SymmetricAbsorbingRandomWalks(assume_immutability=True)

for package in test:
    truth = {packages.packages[dependency]: 1 for dependency in package.dependencies if dependency in packages.packages}
    if sum(truth.get(lib, 0) for lib in app_libs) == 0:
        continue
    personalization = {word: 1. for word in tokenize(package.text()) if word in graph}
    recs = algorithm(graph, personalization)
    evaluator.evaluate([truth.get(lib, 0) for lib in app_libs], [recs[lib] for lib in app_libs], app_libs)
    print(evaluator)


