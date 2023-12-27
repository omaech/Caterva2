###############################################################################
# Caterva2 - On demand access to remote Blosc2 data repositories
#
# Copyright (c) 2023 The Blosc Developers <blosc@blosc.org>
# https://www.blosc.org
# License: GNU Affero General Public License v3.0
# See LICENSE.txt for details about copyright and rights to use.
###############################################################################

import pathlib
import typing

# Requirements
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi_websocket_pubsub import PubSubEndpoint
import uvicorn

# Project
import models
import utils


# State
database = None


# API
app = FastAPI()

@app.get('/api/roots', response_model_exclude_none=True)
async def get_roots() -> typing.Dict[str, models.Root]:
    return database.roots

@app.post('/api/roots')
async def post_roots(root: models.Root) -> models.Root:
    database.roots[root.name] = root
    database.save()
    await endpoint.publish(['@new'], root)
    return root

# Pub/Sub interface
router = APIRouter()
endpoint = PubSubEndpoint()
endpoint.register_route(router)
app.include_router(router)

if __name__ == '__main__':
    parser = utils.get_parser(http='localhost:8000')
    args = utils.run_parser(parser)

    # Init database
    # roots = {name: <Root>}
    var = pathlib.Path('caterva2/broker').resolve()
    database = utils.Database(var / 'db.json', models.Broker(roots={}))
    print(database.data)

    # Run
    host, port = args.http
    uvicorn.run(app, host=host, port=port)
