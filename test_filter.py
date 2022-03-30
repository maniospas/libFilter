from utils.tester import test
from utils.importer import load_data
import pygrank as pg
import numpy as np

class AbsorbingWalksSymmetric(pg.RecursiveGraphFilter):
    """ Implementation of partial absorbing random walks for Lambda = (1-alpha)/alpha diag(absorption vector) .
    """

    def __init__(self,
                 alpha: float = 0.5,
                 symmetric: bool = True,
                 *args, **kwargs):
        """ Initializes the AbsorbingWalks filter parameters. For appropriate parameter values. This can model PageRank
        but is in principle a generalization that allows custom absorption rate per node (when not given, these are I).

        Args:
            alpha: Optional. (1-alpha)/alpha is the absorption rate of the random walk multiplied with individual node
                absorption rates. This is chosen to yield the
                same underlying meaning as PageRank (for which Lambda = alpha Diag(degrees) ) when the same parameter
                value alpha is chosen. Default is 1-1.E-6 per the respective publication.

        Example:
            >>> from pygrank.algorithms import AbsorbingWalks
            >>> algorithm = AbsorbingWalks(1-1.E-6, tol=1.E-9) # tol passed to the ConvergenceManager
            >>> graph, seed_nodes = ...
            >>> ranks = algorithm(graph, {v: 1 for v in seed_nodes})

        Example (same outcome, explicit absorption rate definition):
            >>> from pygrank.algorithms import AbsorbingWalks
            >>> algorithm = AbsorbingWalks(1-1.E-6, tol=1.E-9) # tol passed to the ConvergenceManager
            >>> graph, seed_nodes = ...
            >>> ranks = algorithm(graph, {v: 1 for v in seed_nodes}, absorption={v: 1 for v in graph})
        """

        super().__init__(*args, **kwargs)
        self.alpha = alpha
        self.symmetric = symmetric

    def _start(self, M, personalization, ranks, absorption=None, **kwargs):
        self.degrees = pg.degrees(M)
        if self.symmetric:
            self.absorption = (1+(1+4*self.degrees)**0.5)/2
        else:
            self.absorption = pg.to_signal(personalization.graph, absorption).np * (1 - self.alpha) / self.alpha
        self.personalization_skew = self.absorption / (self.absorption + self.degrees)
        self.sqrt_degrees = (self.degrees / (self.absorption + self.degrees))
        self.sqrt_degrees_left = 1./self.absorption

    def _end(self, *args, **kwargs):
        super()._end(*args, **kwargs)
        del self.absorption
        del self.degrees
        del self.sqrt_degrees
        del self.sqrt_degrees_left
        del self.personalization_skew

    def _formula(self, M, personalization, ranks, *args, **kwargs):
        ret = pg.conv(self.sqrt_degrees_left * ranks, M) * self.sqrt_degrees \
               + personalization * self.personalization_skew
        return ret

    def references(self):
        refs = super().references()
        refs[0] = "partially absorbing random walks \\cite{wu2012learning}"
        return refs


pre = pg.preprocessor(assume_immutability=True, normalization="symmetric", renormalize=1)
arw = AbsorbingWalksSymmetric(preprocessor=pre, tol=1.E-12, max_iters=1000, symmetric=False)

apps, libs, pairs = load_data()
test(apps, libs, pairs, arw, rm=1)
