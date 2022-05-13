# <<< flask run

from pypigraph import Packages, tokenize
from graph_filter import SymmetricAbsorbingRandomWalks
from flask import Flask, request
import json
import uuid
import threading
import pygrank as pg


application = Flask(__name__)
packages = Packages()
requests = dict()
progress = dict()


@application.route('/')
def hello():
    with open('index.html') as file:
        contents = file.read()
    return contents


@application.route("/search", methods=['GET', 'POST'])
def search():
    query = str(request.json["search"])
    task = set(request.json["task"])
    identifier = str(uuid.uuid1())
    requests[identifier] = ""
    progress[identifier] = 0
    threading.Thread(target=local_search, args=(query, 20, identifier, "2" in task)).start()
    return application.response_class(
        response=json.dumps({"identifier": identifier}),
        status=200,
        mimetype='application/json'
    )


@application.route('/status/<identifier>')
def status(identifier):
    return application.response_class(
        response=json.dumps({"progress": str(progress[identifier]), "result": requests[identifier]}),
        status=200,
        mimetype='application/json'
    )



prototype = """
<div class="accordion-item">
    <div class="accordion-header" id="result1heading">
        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#result1" aria-expanded="false" aria-controls="result1">
            <h5 class="card-text">LIBRARYNAME</h2>
        </button>
    </div>
    <div id="result1" class="accordion-collapse collapse" aria-labelledby="result1heading" data-bs-parent="#results">
        <div class="accordion-body">
            <h6 class="card-text text-muted">LIBRARYMETADATA</h6>
            <p class="card-text">LIBRARYDESCRIPTION</p>
            <a href="LIBRARYLINK" target="_blank" rel="noopener noreferrer" class="card-link">PyPI</a>
        </div>
    </div>
</div>
"""

progress_bar = """
<div class="d-flex" style="height: 40px;"></div>
<div class="progress">
  <div class="progress-bar bg-info" style="width: PROGRESSNOW%" role="progressbar" aria-valuenow="PROGRESSNOW" aria-valuemin="0" aria-valuemax="100">MESSAGE</div>
</div>
"""


def local_search(query, top, identifier, produce_mode):
    def update_search(curr_progress, max_progress):
        progress[identifier] = min(99, 100*curr_progress // max_progress)
        requests[identifier] = progress_bar\
                                .replace("PROGRESSNOW", str(progress[identifier]))\
                                .replace("MESSAGE", "Enriching database")

    update_search(0, 1)

    if len(tokenize(query)) > 0:
        packages.search(query, max_pages=5, max_distance=3, update=update_search)

    def update_mining(curr_progress, max_progress):
        progress[identifier] = min(99, 100*curr_progress // max_progress)
        requests[identifier] = progress_bar\
                                .replace("PROGRESSNOW", str(progress[identifier]))\
                                .replace("MESSAGE", "Searching")
    graph = packages.create_graph(from_dependencies=produce_mode)
    nodes = set(graph)
    personalization = {word: 1. for word in tokenize(query) if word in nodes}
    update_mining(0, 10)
    algorithm = pg.PageRank() if produce_mode else SymmetricAbsorbingRandomWalks()
    prev_has_converged = algorithm.convergence.has_converged

    def has_converged(new_ranks):
        update_mining(algorithm.convergence.iteration+1, 10)
        return prev_has_converged(new_ranks)
    algorithm.convergence.has_converged = has_converged
    recs = algorithm(graph, personalization)
    results = [package.name for package in sorted(packages.all(), key=lambda project: -recs.get(project, 0))[:top]]

    ret = """<div class="d-flex" style="height: 40px;"></div>"""
    wrong = set([original for original, word in zip(tokenize(query, False, True), tokenize(query, True, True)) if word not in nodes])
    if wrong:
        ret += f"""<div class="alert alert-danger d-flex align-items-center" role="alert">
                <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>
                <div>Unused keywords: {", ".join(wrong)}</div>
                </div>"""
    if len(tokenize(query)) == 0:
        ret += f"""<div class="alert alert-danger d-flex align-items-center" role="alert">
                <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>
                <div>Empty query recommends generally important libraries</div>
                </div>"""

    for i, package in enumerate(results):
        package = packages.packages[package]
        ret += prototype \
            .replace("result1", "result" + str(i)) \
            .replace("LIBRARYNAME", f'<span class="badge bg-secondary">{i+1}</span> {package.name}') \
            .replace("LIBRARYDESCRIPTION", package.summary) \
            .replace("LIBRARYLINK", package.info["package_url"]) \
            .replace("LIBRARYMETADATA", package.info["keywords"] if package.info["keywords"] is not None else "")
    requests[identifier] = ret
    progress[identifier] = 100
