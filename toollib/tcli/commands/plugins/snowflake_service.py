"""
@author axiner
@version v1.0.0
@created 2023/6/28 10:29
@abstract
@description
@history
"""
import os
import sys

from toollib.guid import SnowFlake
try:
    import uvicorn
    from fastapi import FastAPI
except ImportError as err:
    sys.stderr.write(f'ERROR: {err}\n')
    sys.exit(1)

app = FastAPI()

snow = SnowFlake(epoch_timestamp=int(os.environ.setdefault('epoch-timestamp', '1288834974657')))


@app.get('/gen-snowid')
async def gen_snowid(to_str: bool = False):
    snowid = snow.gen_uid(to_str=to_str)
    return {'snowid': snowid}


def run(host: str, port: int, workers: int):
    uvicorn.run(f"{__name__}:app", host=host, port=port, workers=workers)
