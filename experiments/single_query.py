from pypigraph import Packages, tokenize, stemmer, to_personalization
import pygrank as pg
import math

query = "explainable machine learning"

packages = Packages("query (delete).json")
#packages.search(query, max_pages=10)
packages = packages.unique()
graph = packages.create_graph(from_dependencies=False, weight=lambda tf, df: tf/math.log(df+1), direct_links=1)
personalization = to_personalization(query, set(graph))
recs = 1
for word in query.split(" "):
    recs = pg.SymmetricAbsorbingRandomWalks(tol=1.E-12, normalization="symmetric")(graph, to_personalization(word, set(graph))) * recs
recs = pg.Ordinals()(recs)
for package in packages.all():
    if len(package.description) < 100 and package.homepage == "" and package in graph:
        recs[package] = len(graph)
        #print(package.name, "ignored", len(package.description))
top = [package.name for package in sorted(packages.all(), key=lambda project: recs.get(project, 0))[:20]]
print(top)
