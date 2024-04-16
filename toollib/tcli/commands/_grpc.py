"""
@author axiner
@version v1.0.0
@created 2023/9/21 10:10
@abstract
@description
@history
"""
import subprocess
import sys
from pathlib import Path

from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins import grpc_tpl
from toollib.tcli.option import Options, Arg

try:
    import grpc, grpc_tools
except ImportError as err:
    sys.stderr.write(f"ERROR: {err} (pip install grpcio, grpcio_tools)\n")
    sys.exit(1)


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='grpc',
            desc='grpc模板',
            optional={self.tpl2bash: [
                Arg('-n', '--name', default='hello', type=str, help='名称'),
                Arg('-d', '--dir', default='grpctpl', type=str, help='目录'),
            ]}
        )
        return options

    def tpl2bash(self):
        name: str = self.parse_args.name.strip().lower()
        if not name or name == "''":
            sys.stderr.write('ERROR: -n/--name: 不能为空\n')
            sys.exit(1)
        dir_ = self.parse_args.dir
        dir_obj = Path(dir_).absolute()
        dir_obj.mkdir(parents=True, exist_ok=True)
        dir_path = dir_obj.as_posix()

        proto_path = dir_obj.joinpath(f'{name}.proto').as_posix()
        server_path = dir_obj.joinpath(f'{name}_server.py').as_posix()
        client_path = dir_obj.joinpath(f'{name}_client.py').as_posix()
        print(f'Writing to {dir_path}')
        with open(proto_path, 'wb') as f1, \
                open(server_path, 'wb') as f2, \
                open(client_path, 'wb') as f3:
            f1.write(self.__replace(grpc_tpl.HELLO_PROTO, name))
            f2.write(self.__replace(grpc_tpl.HELLO_SERVER, name))
            f3.write(self.__replace(grpc_tpl.HELLO_CLIENT, name))
        cmd = 'python -m grpc_tools.protoc -I {0} --python_out {0} --grpc_python_out {0} {1}'.format(dir_path, proto_path)
        subprocess.run(cmd, shell=True)

    @staticmethod
    def __replace(text_bytes: bytes, name: str):
        return text_bytes.replace(
            b'hello', name.encode('utf8')).replace(
            b'HELLO', name.upper().encode('utf8')).replace(
            b'Hello', name.title().encode('utf8'))
