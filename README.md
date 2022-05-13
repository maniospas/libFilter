# FLARE - Fast Library Recommendation
This repository holds the code necessary to replicate the manuscript 
titled *Fast Library Recommendation in Software Dependency Graphs 
with Symmetric Partially Absorbing Random Walks* 
by Emmanouil Krasanakis and Andreas Symeonidis.

It additionally 
hosts the code for a server implementing a variation of this
publication to perform keyword-based library recommendation at:

http://83.212.100.59:5000

**Dependencies:** *numpy, networkx, pygrank, nltk, flask*<br>
**License:** Apache 2.0<br/>
**Contact:** manios.krasanakis@issel.ee.auth.gr

## Contents
1. [Symmetric Absorbing Random Walks](#symmetric-absorbing-random-walks)
2. [Replicating Library Recommendation Experiments](#replicating-library-recommendation-experiments)

## Symmetric Absorbing Random Walks
This is a `pygrank` graph filter and will be integrated in
future versions of that package.
It has *no* hyperparameters and emulates the stochastic
equivalent of memory-aware random walks with restart
under stationary memory and low-pass graph filter principles.

The filter can be initialized from this project's code per
```Python
from graph_filter import SymmetricAbsorbingRandomWalks
libFilter = SymmetricAbsorbingRandomWalks(normalization="symmetric", renormalization=True, assume_immutability=True, tol=1.E-12)
```
where immutability takes advantage of *pygrank*'s optimizations
to reuse adjacency matrix normalization for the same graphs. 
Note that we present here the arguments used for publication
experiments, but tinkering with different arguments or other
*pygrank* capabilities (e.g. applying postprocessors) on this
base outcome is also possible.

:bulb: This graph filter will be import-able directly from
the future release `pygrank 0.2.8`.

## Replicating Library Recommendation Experiments
TODO