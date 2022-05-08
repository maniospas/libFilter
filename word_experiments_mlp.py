from pypigraph import Packages, tokenize
from utils.measures import Evaluator
import pygrank as pg
import numpy as np
import gnntf
import networkx as nx
import tensorflow as tf
from random import random


packages = Packages()
train, test = pg.split(packages.all(), 0.1)
graph = packages.create_graph(train, words=False)
evaluator = Evaluator(5, packages.all())
nodes = set(graph)
app_libs = [package for package in test if package in nodes]
all_words = [word for package in packages.all() for word in tokenize(package.text())]
all_words = {word: identifier for identifier, word in enumerate(all_words)}
package_ids = {package: identifier for identifier, package in enumerate(packages.all())}

def to_features(words):
    ret = [0.]*(max(all_words.values())+1)
    for word in words:
        if word in all_words:
            ret[all_words[word]] = 1.
    return ret


features = [to_features(tokenize(package.text())) for package in packages.all()]

train = set(train)
edges = [(package_ids[u], package_ids[v]) for u, v in packages.dependencies(test) if u in train and v in train]

model = gnntf.MLP(tf.convert_to_tensor(features, dtype=tf.float32), latent_dims=[128], num_classes=128)
train_objective = gnntf.LinkPrediction(
    gnntf.negative_sampling(edges, nx.Graph(edges), negative_nodes=[package_ids[u] for u in train], samples=10),
    gnn=model,
    similarity="cos",
    loss="ce")
model.train(train_objective, epochs=100)

prediction = model(tf.convert_to_tensor(features, dtype=tf.float32)).numpy()
all_features = {package: prediction[i, :] for package, i in package_ids.items()}


#all_features = {package: np.array(to_features(tokenize(package.text()))) for package in packages.all()}


def similarity(x, y):
    return np.sum(x*y)/np.sqrt(np.sum(x*x)*np.sum(y*y))


for package in test:
    truth = {packages.packages[dependency]: 1 for dependency in package.dependencies if dependency in packages.packages}
    if sum(truth.get(lib, 0) for lib in app_libs) == 0:
        continue
    personalization = all_features[package]
    recs = {lib: similarity(personalization, all_features[lib]) for lib in app_libs}
    evaluator.evaluate([truth.get(lib, 0) for lib in app_libs], [recs[lib] for lib in app_libs], app_libs)
    print(evaluator)


