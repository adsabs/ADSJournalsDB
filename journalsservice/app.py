from __future__ import absolute_import
from werkzeug.serving import run_simple
from .views import Summary, Journal, Holdings, Refsource
from flask_restful import Api
from flask_discoverer import Discoverer
from adsmutils import ADSFlask


def create_app(**config):
    """
    Create the application and return it to the user
    :return: flask.Flask application
    """

    if config:
        app = ADSFlask(__name__, static_folder=None, local_config=config)
    else:
        app = ADSFlask(__name__, static_folder=None)

    app.url_map.strict_slashes = False

    api = Api(app)
    api.add_resource(Summary, '/Summary/<string:bibstem>')
    api.add_resource(Journal, '/Journal/<string:journalname>')
    api.add_resource(Holdings, '/Holdings/<string:bibstem>/<string:volume>')
    api.add_resource(Refsource, '/Refsource/<string:bibstem>')

    discoverer = Discoverer(app)

    return app

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, create_app(), use_reloader=False, use_debugger=False)
