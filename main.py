from utils.tester import test
from utils.importer import load_data
import pygrank as pg
from graph_filter import SymmetricAbsorbingRandomWalks

pre = pg.preprocessor(assume_immutability=False, normalization="symmetric", renormalize=1)
arw = SymmetricAbsorbingRandomWalks(preprocessor=pre, tol=1.E-12, max_iters=1000, symmetric=True)

apps, libs, pairs = load_data()
test(apps, libs, pairs, arw, rm=5)
