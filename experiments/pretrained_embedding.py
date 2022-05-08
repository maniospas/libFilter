# THIS IS AN EXPERIMENTAL FILE NOT USED IN THE PUBLICATION

import networkx as nx
import pygrank as pg
from utils import importer, measures
import numpy as np

apps, libs, pairs = importer.load_data()
train_pairs, test_pairs = importer.split(pairs, rm=1)
evaluator = measures.Evaluator(k=5, libs=libs)
train_graph = nx.Graph(train_pairs)
test_graph = nx.Graph(test_pairs)

preprocessor = pg.preprocessor(assume_immutability=True, normalization="symmetric", renormalize=True)
filter = pg.AbsorbingWalks(0.5, preprocessor=preprocessor)
propagator = pg.PageRank(0.9, preprocessor=preprocessor, max_iters=20, error_type="iters", use_quotient=False, converge_to_eigenvectors=True)

#features = np.random.uniform(size=(len(train_graph), 32))
#features = features / np.sqrt(np.sum(features*features, axis=0))
features = importer.load_features(train_graph)
print("Features", features.shape)
features = propagator.propagate(train_graph, features)
node2id = {node: i for i, node in enumerate(train_graph)}


for app in test_graph:
    if app in apps:
        recommendations = pg.Transformer(filter, lambda x: x/np.max(x))(train_graph, {app: 1.} | {lib: 1. for lib in train_graph.neighbors(app)})
        app_libs = [lib for lib in libs if not train_graph.has_edge(app, lib)]
        sims = {lib: np.sum((features[node2id[lib], :]-features[node2id[app], :])**2) for lib in libs}
        recommendations = [-(sims[lib]/100)**0.5+np.log(recommendations[lib]) for lib in app_libs]
        print(evaluator.evaluate(labels=[1. if test_graph.has_edge(app, lib) else 0 for lib in app_libs],
                                 recommendations=recommendations, app_libs=app_libs))
