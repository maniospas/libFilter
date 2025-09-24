from utils.tester import test
from utils.importer import load_data
import pygrank as pg
from experiments.bibliography.cosimrank import CoSimRank


pre = pg.preprocessor(assume_immutability=True, normalization="symmetric", renormalize=1)
arw = pg.SymmetricAbsorbingRandomWalks(preprocessor=pre, tol=1.E-12)
#arw = pg.PageRank(preprocessor=pre, tol=1.E-12, max_iters=1000, alpha=0.5)

apps, libs, pairs = load_data()
arw = CoSimRank(assume_immutability=True)
rm = 1
print("arw rm =", rm)
for _ in range(5):
    test(apps, libs, pairs, arw, rm=rm, verbose=True)
    print("\n")
