"""
@author axiner
@version v1.0.0
@created 2023/6/28 10:23
@abstract
@description
@history
"""
from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins import snowflake_service
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='snowflake',
            desc='雪花服务',
            optional={self.snowflake: [
                Arg('--host', default='0.0.0.0', type=str, help='host'),
                Arg('--port', default=9000, type=int, help='port'),
                Arg('--workers', default=4, type=int, help='进程数'),
            ]}
        )
        return options

    def snowflake(self):
        host = self.parse_args.host
        port = self.parse_args.port
        workers = self.parse_args.workers
        snowflake_service.run(
            host=host,
            port=port,
            workers=workers,
        )
