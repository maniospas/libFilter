from pypigraph import Packages, tokenize
from utils.measures import Evaluator
import pygrank as pg
import numpy as np
import gnntf
import networkx as nx
import tensorflow as tf
from random import random

packages = Packages()
train, test = pg.split(packages.all(), 1)
graph = packages.create_graph(train, words=False)
evaluator = Evaluator(10, packages.all())
nodes = set(graph)
app_libs = [package for package in test if package in nodes]
all_words = list(set([word for package in packages.all() for word in tokenize(package.text())]))
all_words = {word: identifier for identifier, word in enumerate(all_words)}
package_ids = {package: identifier for identifier, package in enumerate(packages.all())}


def to_features(words):
    ret = [0.]*(max(all_words.values())+1)
    for word in words:
        if word in all_words:
            ret[all_words[word]] = 1.
    return ret


features = [to_features(tokenize(package.text())) for package in packages.all()]
features = np.array(features)

#features = features/np.sum(features, axis=0)

train = set(train)
edges = [(package_ids[u], package_ids[v]) for u, v in packages.dependencies(test)]# if u in train and v in train]
train_edges = list()
valid_edges = list()
test_edges = list()
for edge in edges:
    if random() < 0.6:
        train_edges.append(edge)
    elif random() < 0.5:
        valid_edges.append(edge)
    else:
        test_edges.append(edge)


class CustomMLP(gnntf.Trainable):
    def __init__(self, features: tf.Tensor, num_classes: int, latent_dims=[256], dropout: float = 0):
        super().__init__(features)
        self.add(gnntf.Dropout(dropout))
        for latent_dim in latent_dims:
            self.add(gnntf.Dense(latent_dim, dropout=dropout, activation=tf.nn.relu))
        self.add(gnntf.Dense(num_classes, dropout=dropout))

tfGraph = nx.Graph()
for u in range(len(package_ids)):
    tfGraph.add_node(u)
for u, v in train_edges:
    tfGraph.add_edge(u, v)

model = gnntf.NGCF(gnntf.graph2adj(tfGraph), tf.convert_to_tensor(features, dtype=tf.float32), num_classes=256)
train_objective = gnntf.LinkPrediction(
    gnntf.negative_sampling(train_edges, nx.Graph(train_edges), negative_nodes=[package_ids[u] for u in train], samples=1),
    similarity="cos")
valid_objective = gnntf.LinkPrediction(
    *gnntf.negative_sampling(valid_edges, nx.Graph(valid_edges), negative_nodes=[package_ids[u] for u in train], samples=1)(),
    similarity="cos")
model.train(train_objective, valid=valid_objective, test=train_objective, epochs=10, learning_rate=0.01, verbose=True)

prediction = model(tf.convert_to_tensor(features, dtype=tf.float32)).numpy()
#prediction = np.reshape((1./np.sum(features**2, axis=1)**0.5), (-1, 1))*features
all_features = {package: prediction[i, :] for package, i in package_ids.items()}
#all_features = {package: np.array(to_features(tokenize(package.text()))) for package in packages.all()}


def similarity(x, y):
    return np.sum(x*y)/np.sqrt(np.sum(x*x)*np.sum(y*y))

test_dependencies = {u: set() for u, v in test_edges}
for u, v in test_edges:
    test_dependencies[u].add(v)
#test_dependencies = packages.dependencies

for package in test:
    truth = {dependency: 1 for dependency in package.dependencies
             if package in package_ids
                 and package_ids[package] in test_dependencies
                 and dependency in package_ids
                 and package_ids[dependency] in test_dependencies[package_ids[package]]}
    if sum(truth.get(lib, 0) for lib in app_libs) < 5:
        continue
    personalization = all_features[package]
    recs = {lib: similarity(personalization, all_features[lib]) for lib in app_libs}
    evaluator.evaluate([truth.get(lib, 0) for lib in app_libs], [recs[lib] for lib in app_libs], app_libs)
    print(evaluator)


