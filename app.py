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
from flask import render_template_string
import os, bcrypt
from flask import flash, redirect, url_for, session
import re
from threading import Lock

progress_registry = {
    "progress": {},  # identifier -> int (0-100)
    "results": {},   # identifier -> html string
    "lock": Lock()
}

def set_progress(identifier: str, value: int, html: str = None):
    with progress_registry["lock"]:
        progress_registry["progress"][identifier] = value
        if html is not None:
            progress_registry["results"][identifier] = html

def get_progress(identifier: str):
    with progress_registry["lock"]:
        return progress_registry["progress"].get(identifier, 100)

def get_result(identifier: str):
    with progress_registry["lock"]:
        return progress_registry["results"].get(identifier, "")


# Allowed: letters, digits, underscore, dash; length 3–30
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,30}$')

def validate_username(username: str) -> str:
    """
    Ensure the username only contains safe characters and is 3–30 chars long.
    Returns the cleaned username or raises ValueError if invalid.
    """
    cleaned = username.strip()
    if not USERNAME_PATTERN.fullmatch(cleaned):
        # Raise a descriptive error for the caller to handle
        raise ValueError(
            "Username must be 3–30 characters long and contain only "
            "letters, digits, underscores, or dashes."
        )
    return cleaned


USERS_FILE="users.json"
def load_users():
    """Load users.json and upgrade old schema if needed."""
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data
users = load_users()

sys.stderr = sys.stdout

application = Flask(__name__)
application.secret_key = os.environ.get("FLARE_SECRET_KEY", "dev-secret")  # secure in production

logging.getLogger('werkzeug').setLevel(logging.ERROR)
packages = Packages()
requests = dict()
progress = dict()

def get_user_record(username):
    user = users.get(username)
    if isinstance(user, str):  # old format
        users[username] = {
            "password": user,
            "last_search": None,
            "stars": []
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
        user = users[username]
    return user

@application.route('/')
def hello():
    # Load the HTML template
    with open('index.html') as file:
        contents = file.read()


    if 'username' in session:
        user = get_user_record(session['username'])
        last_id = user.get("last_search")

        # --- Determine JS variables for the frontend ---
        if last_id:
            current_progress = get_progress(last_id)
            if current_progress < 100:
                last_search_js = (
                    f"<script>window.FLARE_LAST_SEARCH = "
                    f"{json.dumps(last_id)}</script>"
                )
            else:
                last_search_js = "<script>window.FLARE_LAST_SEARCH = null;</script>"
                last_result = get_result(last_id)
                if last_result:
                    contents = contents.replace(
                        '<div id="results"></div>',
                        f'{last_result}<div id="results"></div>'
                    )
        else:
            last_search_js = "<script>window.FLARE_LAST_SEARCH = null;</script>"

        user_js = (
            f"<script>window.FLARE_USER = "
            f"{json.dumps(session['username'])}</script>"
        )
        inject = user_js + last_search_js

    else:
        # Not logged in → nulls and any flash messages
        inject = (
            "<script>window.FLARE_USER = null;"
            "window.FLARE_LAST_SEARCH = null;</script>"
        )
        messages = ""
        for _, msg in session.get('_flashes', []):
            messages += f"<div class='progress-alert'>{msg}</div>"
        session.pop('_flashes', None)
        contents = contents.replace(
            '<div id="results"></div>',
            f"{messages}<div id=\"results\"></div>"
        )

    # Insert our JS variables before </head>
    return contents.replace("</head>", inject + "</head>")


@application.route("/search", methods=['GET', 'POST'])
def search():
    query = str(request.json["search"])
    task = set(request.json["task"])
    identifier = str(uuid.uuid1())
    requests[identifier] = ""
    progress[identifier] = 0
    if 'username' in session:
        users[session['username']]["last_search"] = identifier
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    if "username" in session:
        get_user_record(session["username"])["last_search"] = identifier
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    threading.Thread(
        target=local_search,
        args=(query, 40, identifier, "2" in task)
    ).start()
    return application.response_class(
        response=json.dumps({"identifier": identifier}),
        status=200,
        mimetype='application/json'
    )


@application.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = validate_username(request.form.get("username", ""))
        except ValueError as err:
            flash(f"❗ {err}")
            return redirect(url_for("hello"))
        password = request.form.get("password")
        if username in users:
            flash("❗ User already exists")
            return redirect(url_for('hello'))
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        users[username] = {
            "password": hashed,
            "last_search": None,
            "stars": []
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
        session['username'] = username
        flash(f"✅ Registered and logged in as: {username}")
        return redirect(url_for('hello'))
    return render_template_string(register_page)


@application.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = validate_username(request.form.get("username", ""))
        except ValueError:
            flash("❗ Invalid username format")
            return redirect(url_for("hello"))
        password = request.form.get("password")

        user_data = users.get(username)
        if not user_data:
            flash("❗ Incorrect user name or password")
            return redirect(url_for('hello'))

        if bcrypt.checkpw(password.encode("utf-8"),
                          user_data["password"].encode("utf-8")):
            session['username'] = username
            #flash(f"🔐 Logged in as: {username}")
        else:
            flash("❗ Incorrect user name or password")
        return redirect(url_for('hello'))
    return render_template_string(login_page)


@application.route("/logout")
def logout():
    session.pop('username', None)
    flash("✅ Logged out")
    return redirect(url_for('hello'))


@application.route('/status/<identifier>')
def status(identifier):
    if identifier == "current" and "username" in session:
        identifier = get_user_record(session["username"]).get("last_search")
    return application.response_class(
        response=json.dumps({
            "progress": str(get_progress(identifier)),
            "result": get_result(identifier)
        }),
        status=200,
        mimetype='application/json'
    )

@application.route("/star/<pkg>", methods=["POST"])
def star(pkg):
    if "username" not in session:
        return "Not logged in", 401
    stars = get_user_record(session["username"]).setdefault("stars", [])
    if pkg not in stars:
        stars.append(pkg)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    return "ok", 200


@application.route("/unstar/<pkg>", methods=["POST"])
def unstar(pkg):
    if "username" not in session:
        return "Not logged in", 401
    stars = get_user_record(session["username"]).setdefault("stars", [])
    if pkg in stars:
        stars.remove(pkg)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    return "ok", 200


@application.route("/stars")
def list_stars():
    if "username" not in session:
        return application.response_class(response=json.dumps([]), mimetype='application/json')
    return application.response_class(
        response=json.dumps(get_user_record(session["username"]).get("stars", [])),
        mimetype='application/json'
    )


def local_search(query, top, identifier, produce_mode):
    def update_search(curr, max_, message, progress_now=None):
        pct = min(99, 100*curr // max_) if max_ else curr
        html = progress_bar.replace("PROGRESSNOW", progress_now or f"{pct}%")\
                           .replace("MESSAGE", message)
        set_progress(identifier, pct, html)
    update_search(0, 1, "Searching for related packages to analyze", "starting")
    if len(tokenize(query)) > 0:
        packages.search(query, max_new=40, max_distance=3, update=update_search)

    def update_mining(curr_progress, max_progress, message="Searching", progress_now=None):
        progress[identifier] = min(99, 100*curr_progress // max_progress) if max_progress else str(curr_progress)
        requests[identifier] = progress_bar\
                                .replace("PROGRESSNOW", progress_now if progress_now else str(progress[identifier])+"%")\
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
            .replace("LIBRARYORDER", f'{i+1}') \
            .replace("LIBRARYNAME", f'{package.name}') \
            .replace("LIBRARYDESCRIPTION", package.summary if package.summary else "Unknown description") \
            .replace("LIBRARYLINK", package.info["package_url"]) \
            .replace("LIBRARYHOME", package.homepage if len(package.homepage)>0 else package.info["package_url"]) \
            .replace("LIBRARYMETADATA", package.info["keywords"] if package.info["keywords"] is not None else "")
    requests[identifier] = ret
    progress[identifier] = 100


if __name__ == "__main__":
    application.run(host='0.0.0.0',threaded=False, processes=1)