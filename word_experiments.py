from pypigraph import Packages, tokenize
from utils.measures import Evaluator
import pygrank as pg
from bibliography.cosimrank import CoSimRank


packages = Packages()
"""
packages.search("Machine Learning", max_pages=5, max_distance=3)
packages.search("Deep Learning", max_pages=5, max_distance=3)
packages.search("Natural Language Processing", max_pages=5, max_distance=3)
packages.search("Text and Speech Processing", max_pages=5, max_distance=3)
packages.search("Morphological Analysis", max_pages=5, max_distance=3)
packages.search("Syntactic Analysis", max_pages=5, max_distance=3)
packages.search("Lexical Semantics", max_pages=5, max_distance=3)
packages.search("Relational Semantics", max_pages=5, max_distance=3)
packages.search("Discourse", max_pages=5, max_distance=3)
packages.search("Grammar and Error Correction", max_pages=5, max_distance=3)
packages.search("Text Translation", max_pages=5, max_distance=3)
packages.search("Dialogue Management", max_pages=5, max_distance=3)
packages.search("Question Answering", max_pages=5, max_distance=3)
packages.search("Computer Vision", max_pages=5, max_distance=3)
packages.search("Defect Detection", max_pages=5, max_distance=3)
packages.search("Meteorology", max_pages=5, max_distance=3)
packages.search("Intruder Detection", max_pages=5, max_distance=3)
packages.search("Security", max_pages=5, max_distance=3)
packages.search("Personalization", max_pages=5, max_distance=3)
packages.search("Editing", max_pages=5, max_distance=3)
packages.search("Assembly Verification", max_pages=5, max_distance=3)
packages.search("Screen Reader", max_pages=5, max_distance=3)
packages.search("Live Text", max_pages=5, max_distance=3)
packages.save()
"""
print(len(packages.dependencies()), "package dependencies")
#personalization = {stemmer.stem(word): 1. for word in tokenize(query)}
#recs = SymmetricAbsorbingRandomWalks()(graph, personalization)
#top = [package.name for package in sorted(packages.all(), key=lambda project: -recs.get(project,0))[:10]]

packages = Packages()
train, test = pg.split(packages.all(), 0.8)
graph = packages.create_graph(train)
evaluator5 = Evaluator(5, packages.all())
evaluator10 = Evaluator(5, packages.all())
nodes = set(graph)
app_libs = [lib for lib in train if lib in nodes]
algorithm = pg.SymmetricAbsorbingRandomWalks(assume_immutability=True, normalization="col")
algorithm = pg.PageRank(0.5, assume_immutability=True)
algorithm = CoSimRank(weights=[0.5**i for i in range(20)], assume_immutability=True, dims=1024)

for package in test:
    truth = {packages.packages[dependency]: 1 for dependency in package.dependencies if dependency in packages.packages}
    if sum(truth.get(lib, 0) for lib in app_libs) == 0:
        continue
    personalization = {word: 1. for word in tokenize(package.text()) if word in graph}
    recs = algorithm(graph, personalization)
    evaluator5.evaluate([truth.get(lib, 0) for lib in app_libs], [recs[lib] for lib in app_libs], app_libs)
    evaluator10.evaluate([truth.get(lib, 0) for lib in app_libs], [recs[lib] for lib in app_libs], app_libs)
    print("\r"+str(evaluator5)+" \t "+str(evaluator10), end="")


