# test: flask run
# deploy: nohup python3.9 -m gunicorn -w 1 -b 0.0.0.0:5000 app & disown


import json
import uuid
import logging
import threading
import pygrank as pg
import sys
from flask import Flask, request
from pypigraph import Packages, tokenize, to_personalization
from utils.prototypes import *

sys.stderr = sys.stdout

application = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
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
    threading.Thread(target=local_search, args=(query, 40, identifier, "2" in task)).start()
    return application.response_class(
        response=json.dumps({"identifier": identifier}),
        status=200,
        mimetype='application/json'
    )


@application.route('/status/<identifier>')
def status(identifier):
    return application.response_class(
        response=json.dumps({"progress": str(progress.get(identifier, "100")), "result": requests.get(identifier, old_request)}),
        status=200,
        mimetype='application/json'
    )


def local_search(query, top, identifier, produce_mode):
    def update_search(curr_progress, max_progress, message="Searching for related packages to analyze", progress_now=None):
        progress[identifier] = min(99, 100*curr_progress // max_progress) if max_progress else str(curr_progress)
        requests[identifier] = progress_bar\
                                .replace("PROGRESSNOW", progress_now if progress_now else str(progress[identifier]))+"%"\
                                .replace("MESSAGE", message)
    update_search(0, 1, "Searching for related packages to analyze", "")
    if len(tokenize(query)) > 0:
        packages.search(query, max_new=40, max_distance=3, update=update_search)

    def update_mining(curr_progress, max_progress, message="Searching", progress_now=None):
        progress[identifier] = min(99, 100*curr_progress // max_progress) if max_progress else str(curr_progress)
        requests[identifier] = progress_bar\
                                .replace("PROGRESSNOW", progress_now if progress_now else str(progress[identifier]))+"%"\
                                .replace("MESSAGE", message)
    graph = packages.unique().create_graph(from_dependencies=produce_mode)
    personalization = to_personalization(query, set(graph))
    update_mining(0, 10)
    algorithm = pg.PageRank(tol=1.E-12, max_iters=1000) if produce_mode else pg.SymmetricAbsorbingRandomWalks(tol=1.E-12, max_iters=1000)
    #prev_has_converged = algorithm.convergence.has_converged
    #def has_converged(new_ranks):
    #    update_mining(algorithm.convergence.iteration+1, 10)
    #    return prev_has_converged(new_ranks)
    #algorithm.convergence.has_converged = has_converged
    recs = 1
    for word in query.split(" "):
        recs = algorithm(graph, to_personalization(word, set(graph))) * recs
    results = [package.name for package in sorted(packages.all(), key=lambda project: -recs.get(project, 0))[:top]]

    ret = """<div class="d-flex" style="height: 40px;"></div>"""
    wrong = set()#set([original for original, word in zip(tokenize(query, False, True), tokenize(query, True, True)) if word not in nodes])
    if wrong:
        ret += f"""<div class="alert alert-danger d-flex align-items-center" role="alert">
                <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>
                <div>Unused keywords: {", ".join(wrong)}</div>
                </div>"""
    if len(tokenize(query)) - len(wrong) == 0:
        ret += f"""<div class="alert alert-danger d-flex align-items-center" role="alert">
                <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>
                <div>Empty query recommends generally important libraries</div>
                </div>"""

    for i, package in enumerate(results):
        package = packages.packages[package]
        ret += prototype \
            .replace("result1", "result" + str(i)) \
            .replace("LIBRARYNAME", f'<span class="badge bg-secondary">{i+1}</span> {package.name}') \
            .replace("LIBRARYDESCRIPTION", package.summary if package.summary else "Unknown description") \
            .replace("LIBRARYLINK", package.info["package_url"]) \
            .replace("LIBRARYHOME", package.homepage if len(package.homepage)>0 else package.info["package_url"]) \
            .replace("LIBRARYMETADATA", package.info["keywords"] if package.info["keywords"] is not None else "")
    requests[identifier] = ret
    progress[identifier] = 100


if __name__ == "__main__":
    application.run(host='0.0.0.0',threaded=False, processes=1)