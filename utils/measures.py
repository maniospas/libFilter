import numpy as np
from sklearn import metrics


class Evaluator:
    def __init__(self, k, libs):
        self.f1s = list()
        self.maps = list()
        self.precs = list()
        self.recs = list()
        self.aucs = list()
        self.cov = set()
        self.libs = list(libs)
        self.k = k

    def evaluate(self, labels, recommendations, app_libs):
        k = self.k
        self.f1s.append(f1(labels, recommendations, k))
        self.precs.append(prec(labels, recommendations, k))
        self.recs.append(rec(labels, recommendations, k))
        self.maps.append(avprec(labels, recommendations, k))
        self.aucs.append(auc(labels, recommendations))
        self.cov = set(list(self.cov) + list([app_libs[i] for i in np.argsort(recommendations)[-k:]]))
        return self

    def __str__(self):
        return f"AUC {np.mean(self.aucs):.3f} \t " \
               + f"MP {np.mean(self.precs):.3f} \t "\
               + f"MR {np.mean(self.recs):.3f} \t "\
               + f"F1 {np.mean(self.f1s):.3f} \t "\
               + f"MAP {np.mean(self.maps):.3f} \t " \
               + f"coverage {len(self.cov) / len(self.libs):.3f}"


def auc(labels, predictions):
    fpr, tpr, thresholds = metrics.roc_curve(labels, predictions, pos_label=1)
    return metrics.auc(fpr, tpr)


def avprec(labels, predictions, k=5):
    nom = 0
    top = np.argsort(predictions)[-k:]
    for pos, i in enumerate(reversed(top)):
        nom += labels[i]/(pos+1)
    return 0 if nom == 0 else nom/np.sum(np.array(labels)[top])


def rec(labels, predictions, k=5):
    top = np.argsort(predictions)[-k:]
    return np.sum(np.array(labels)[top])/np.sum(labels)


def prec(labels, predictions, k=5):
    top = np.argsort(predictions)[-k:]
    return np.mean(np.array(labels)[top])


def f1(labels, predictions, k=5):
    precision = prec(labels, predictions, k)
    recall = rec(labels, predictions, k)
    if precision+recall == 0:
        return 0
    return 2*precision*recall/(precision+recall)
