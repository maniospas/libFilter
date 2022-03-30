import random
import numpy as np
import tqdm


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)


def load_data(path="data/"):
    apps = set()
    libs = set()
    pairs = list()
    with open(path+"relation.csv") as file:
        for line in file:
            app, lib = line[:-1].split(",")
            apps.add("A"+app)
            libs.add("L"+lib)
            pairs.append(("A"+app, "L"+lib))
    return apps, libs, pairs


def _split_to_words(sentence):
    if "_" in sentence:
        ret = list()
        for word in sentence.split("_"):
            ret += _split_to_words(word)
        return ret
    if "." in sentence:
        ret = list()
        for word in sentence.split("."):
            ret += _split_to_words(word)
        return ret
    for pos, letter in enumerate(sentence):
        if pos > 0 and letter.isupper() and sentence[pos-1].islower() and (pos<2 or sentence[pos-2].islower()):
            return _split_to_words(sentence[:pos])+_split_to_words(sentence[pos:])
    return [sentence.lower()]


def load_features(nodes, path="data/", embeddings=True):
    features = dict()
    with open(path + '/apk_info.csv') as file:
        for line in file:
            line = line[:-1].split(',')
            line[0] = "A" + line[0]
            features[line[0]] = _split_to_words(line[1])
    with open('../data/lib_info.csv') as file:
        for line in file:
            line = line[:-1].split(',')
            line[0] = "L" + line[0]
            features[line[0]] = _split_to_words(line[1])
    occurences = dict()
    for words in features.values():
        for word in words:
            occurences[word] = occurences.get(word, 0) + 1
    feature2id = dict()
    for words in features.values():
        for word in words:
            if word not in feature2id and occurences[word] > 1 and len(word) > 3:
                feature2id[word] = len(feature2id)
    if embeddings:
        import gensim.downloader as api
        word_vectors = api.load("glove-wiki-gigaword-100")
        #word_vectors = api.load("wiki-english-20171001")
        feature_matrix = list()
        for node in nodes:
            embedding = np.array([0.] * 100)
            count = 0
            for word in features[node]:
                if word in feature2id and word in word_vectors:
                    count += 1
                    embedding = embedding + word_vectors[word]
            if count == 0:
                count = 1
            feature_matrix.append(embedding / count)
        feature_matrix = np.array(feature_matrix, np.float32)
    else:
        feature_matrix = np.zeros((len(nodes), len(feature2id)), dtype=np.float32)
        for row, node in enumerate(nodes):
            for word in features[node]:
                if word in feature2id:
                    feature_matrix[row, feature2id[word]] = 1./np.log(occurences[word]+1)**0.5
    return feature_matrix


def split(pairs, min_app_size=10, rm=3):
    apps = set([app for app, _ in pairs])
    dependencies = {app: list() for app in apps}
    for app, lib in pairs:
        dependencies[app].append(lib)
    test_dependencies = {app: list(random.sample(dependencies[app], rm)) for app in apps if len(dependencies[app]) >= min_app_size}
    for app in test_dependencies:
        dependencies[app] = set(dependencies[app])-set(test_dependencies[app])
    return [(app, lib) for app, libs in dependencies.items() for lib in libs], [(app, lib) for app, libs in test_dependencies.items() for lib in libs]
