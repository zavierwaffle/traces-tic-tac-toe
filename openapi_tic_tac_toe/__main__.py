#!/usr/bin/env python3

import connexion

from time import perf_counter

from flask import Response
from flask import g
from flask import request
from prometheus_client import CONTENT_TYPE_LATEST

from openapi_tic_tac_toe import encoder
from openapi_tic_tac_toe.logging import logging_configure
from openapi_tic_tac_toe.metrics import metrics_get_payload
from openapi_tic_tac_toe.metrics import metrics_observe_http_request
from openapi_tic_tac_toe.tracing import tracing_configure

def main():
    logging_configure()
    tracing_configure()

    app = connexion.App(__name__, specification_dir = './openapi/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml', arguments = {'title': 'Tic-Tac-Toe'}, pythonic_params = True)

    @app.app.before_request
    def before_request():
        g.request_started_at = perf_counter()

    @app.app.after_request
    def after_request(response):
        started_at = getattr(g, "request_started_at", None)
        if started_at is not None:
            endpoint = request.url_rule.rule if request.url_rule is not None else "unknown"
            duration_seconds = perf_counter() - started_at
            metrics_observe_http_request(
                method = request.method,
                endpoint = endpoint,
                status_code = response.status_code,
                duration_seconds = duration_seconds,
            )

        return response

    @app.app.route("/metrics")
    def metrics():
        return Response(metrics_get_payload(), mimetype = CONTENT_TYPE_LATEST)

    app.run(port = 8080)


if __name__ == '__main__':
    main()
