"""
@author axiner
@version v1.0.0
@created 2022/5/2 9:34
@abstract
@description
@history
"""
import sys
from multiprocessing import Process, Queue

from toollib import utils

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    raise


class FileEventHandler(FileSystemEventHandler):

    def __init__(self, q):
        super().__init__()
        self.queue = q

    def on_created(self, event):
        event_name = sys._getframe().f_code.co_name
        if event.is_directory:
            _even_type = (event_name, 'dir')
        else:
            _even_type = (event_name, 'file')
        self.queue.put((_even_type, {'src_path': event.src_path}))

    def on_deleted(self, event):
        event_name = sys._getframe().f_code.co_name
        if event.is_directory:
            _even_type = (event_name, 'dir')
        else:
            _even_type = (event_name, 'file')
        self.queue.put((_even_type, {'src_path': event.src_path}))

    def on_modified(self, event):
        event_name = sys._getframe().f_code.co_name
        if event.is_directory:
            _even_type = (event_name, 'dir')
        else:
            _even_type = (event_name, 'file')
        self.queue.put((_even_type, {'src_path': event.src_path}))

    def on_moved(self, event):
        event_name = sys._getframe().f_code.co_name
        if event.is_directory:
            _even_type = (event_name, 'dir')
        else:
            _even_type = (event_name, 'file')
        self.queue.put((_even_type, {'src_path': event.src_path, 'dest_path': event.dest_path}))

    def on_closed(self, event):
        event_name = sys._getframe().f_code.co_name
        if event.is_directory:
            _even_type = (event_name, 'dir')
        else:
            _even_type = (event_name, 'file')
        self.queue.put((_even_type, {'src_path': event.src_path}))


def monitor(queue, src):
    observer = Observer()
    event_handler = FileEventHandler(queue)
    observer.schedule(event_handler, src, recursive=True)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def sync(queue, src, dest, ip, user, port, suffix):
    while True:
        event = queue.get()
        if event:
            if not event[1].get('src_path', '').endswith(('.swp', '.swx')):
                sys.stdout.write(f'[pytcli][info]{event}\n')
                _rsync(src, dest, ip, user, port, suffix)


def _rsync(src, dest, ip, user, port, suffix):
    for _ in range(3):
        try:
            if suffix:
                dest = f'{dest}-{suffix}'
            if port == 22:
                cmd = f'rsync -avz --delete --exclude={{*.swp,*.swx}} ' \
                      f'{src} {user}@{ip}:{dest}'
            else:
                cmd = f'rsync -avz -e "ssh -p {port}" --delete --exclude={{*.swp,*.swx}} ' \
                      f'{src} {user}@{ip}:{dest}'
            p = utils.syscmd(cmd)
            out, err = p.communicate()
            if out:
                sys.stdout.write(u'[pytcli][info]{0}'.format(out.decode('utf-8')))
            if err:
                sys.stderr.write(u'[pytcli][error]{0}'.format(err.decode('utf-8')))
        except Exception as err:
            sys.stderr.write(f'[pytcli][error]{str(err)}\n')
            sys.stdout.write('[pytcli][info][重试中]...\n')


def execute(src, dest, ip, user, port, suffix):
    sys.stdout.write('[pytcli][info]start...(请确保主备服务可免密登录)\n')
    queue = Queue()
    _rsync(src, dest, ip, user, port, suffix)
    producer = Process(target=monitor, args=(queue, src))
    consumer = Process(target=sync, args=(queue, src, dest, ip, user, port, suffix))
    producer.start()
    consumer.start()
