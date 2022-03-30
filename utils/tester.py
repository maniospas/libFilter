import networkx as nx
import numpy as np
from utils import importer, measures
import sys
from timeit import default_timer as time


def _test(graph_filter, test_apps, libs, train_graph, test_graph, verbose=False):
    evaluator5 = measures.Evaluator(k=5, libs=libs)
    evaluator10 = measures.Evaluator(k=10, libs=libs)
    graph_filter.preprocessor(train_graph)

    tic = time()
    for i, app in enumerate(test_apps):
        recommendations = graph_filter(train_graph, {app: 1.} | {lib: 1.for lib in train_graph.neighbors(app)})
        recommendations.np = recommendations.np
        app_libs = [lib for lib in libs if not train_graph.has_edge(app, lib)]
        evaluator5.evaluate(labels=[1. if test_graph.has_edge(app, lib) else 0 for lib in app_libs],
                            recommendations=[recommendations[lib] for lib in app_libs], app_libs=app_libs)
        evaluator10.evaluate(labels=[1. if test_graph.has_edge(app, lib) else 0 for lib in app_libs],
                             recommendations=[recommendations[lib] for lib in app_libs], app_libs=app_libs)
        if verbose:
            sys.stdout.write(
                '\rApp ' + str(i) + ' / ' + str(len(test_apps)) + ': '
                + str(evaluator5) + ' \t '
                + str(evaluator10) + '\t '
                + str((time()-tic)/(i+1))+' sec ')
            sys.stdout.flush()
    return np.mean(evaluator5.f1s)


def test(apps, libs, pairs, graph_filter, rm, verbose=True):
    train_pairs, test_pairs = importer.split(pairs, rm=rm)
    train_graph = nx.Graph(train_pairs)
    test_graph = nx.Graph(test_pairs)
    test_apps = [app for app in test_graph if app in apps]
    return _test(graph_filter, test_apps, libs, train_graph, test_graph, verbose=verbose)
