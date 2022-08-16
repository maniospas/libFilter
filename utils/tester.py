import networkx as nx
import numpy as np
from utils import importer, measures
import sys
from timeit import default_timer as time


def _test(graph_filter, test_apps, libs, global_train_graph, test_graph, verbose=False, receptive_field=None):
    evaluator5 = measures.Evaluator(k=5, libs=libs)
    evaluator10 = measures.Evaluator(k=10, libs=libs)
    #graph_filter.preprocessor(global_train_graph)

    sum_time = 0
    for i, app in enumerate(test_apps):
        tic = time()
        train_graph = global_train_graph if receptive_field is None else nx.ego_graph(global_train_graph, app, receptive_field)
        recommendations = graph_filter(train_graph, {app: 1.} | {lib: 1.for lib in train_graph.neighbors(app)})
        sum_time += time()-tic
        app_libs = [lib for lib in libs if not train_graph.has_edge(app, lib)]
        evaluator5.evaluate(labels=[1. if test_graph.has_edge(app, lib) else 0 for lib in app_libs],
                            recommendations=[recommendations.get(lib, 0) for lib in app_libs], app_libs=app_libs)
        evaluator10.evaluate(labels=[1. if test_graph.has_edge(app, lib) else 0 for lib in app_libs],
                             recommendations=[recommendations.get(lib, 0) for lib in app_libs], app_libs=app_libs)
        if verbose:
            sys.stdout.write(
                '\r' + str(i) + '/' + str(len(test_apps)) + ': '
                + str(evaluator5) + ' \t '
                + str(evaluator10) + '\t '
                + str(sum_time/(i+1))+' sec')
            sys.stdout.flush()
    return np.mean(evaluator5.f1s)


def test(apps, libs, pairs, graph_filter, rm, **kwargs):
    train_pairs, test_pairs = importer.split(pairs, rm=rm)
    train_graph = nx.Graph(train_pairs)
    test_graph = nx.Graph(test_pairs)
    test_apps = [app for app in test_graph if app in apps]
    return _test(graph_filter, test_apps, libs, train_graph, test_graph, **kwargs)
