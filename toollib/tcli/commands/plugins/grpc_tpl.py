"""
@author axiner
@version v1.0.0
@created 2023/9/21 10:10
@abstract
@description
@history
"""

HELLO_PROTO = b'syntax="proto3";\n\npackage hello;\n\n// \xe5\xae\x9a\xe4\xb9\x89\xe6\x9c\x8d\xe5\x8a\xa1\nservice HelloSvc {\n    rpc Hello(HelloReq) returns(HelloResp){}\n}\n\n// \xe5\xae\x9a\xe4\xb9\x89\xe6\xb6\x88\xe6\x81\xaf\xef\xbc\x88\xe8\xaf\xb7\xe6\xb1\x82\xe4\xb8\x8e\xe5\x93\x8d\xe5\xba\x94\xef\xbc\x89\nmessage HelloReq {\n    string arg1 = 1;\n    int32 arg2 = 2;\n}\nmessage HelloResp {\n    string msg = 1;\n}\n'

HELLO_SERVER = b'"""\n@author axiner\n@version v1.0.0\n@created 2023/9/21 10:10\n@abstract\n@description\n@history\n"""\nfrom concurrent.futures import ThreadPoolExecutor\n\nimport grpc\n\nimport hello_pb2\nimport hello_pb2_grpc\n\n\nclass HelloSvc(hello_pb2_grpc.HelloSvcServicer):\n\n    def Hello(self, request, context):\n        arg1 = request.arg1\n        arg2 = request.arg2\n        return hello_pb2.HelloResp(msg=f\'arg1: {arg1}, arg2: {arg2}\')\n\n\ndef serve():\n    port = \'9000\'\n    server = grpc.server(ThreadPoolExecutor(max_workers=4))\n    hello_pb2_grpc.add_HelloSvcServicer_to_server(HelloSvc(), server)\n    server.add_insecure_port(f\'[::]:{port}\')\n    server.start()\n    print(\'Server started, listening on \' + port)\n    server.wait_for_termination()\n\n\nif __name__ == \'__main__\':\n    serve()\n'

HELLO_CLIENT = b'"""\n@author axiner\n@version v1.0.0\n@created 2023/9/21 10:10\n@abstract\n@description\n@history\n"""\nimport grpc\n\nimport hello_pb2\nimport hello_pb2_grpc\n\n\ndef call_hello():\n    addr = \'localhost:9000\'\n    with grpc.insecure_channel(addr) as channel:\n        stub = hello_pb2_grpc.HelloSvcStub(channel)\n        resp = stub.Hello(hello_pb2.HelloReq(arg1=\'aaa\', arg2=111))\n        print(f\'resp: {resp.msg}\')\n\n\nif __name__ == \'__main__\':\n    call_hello()\n'
