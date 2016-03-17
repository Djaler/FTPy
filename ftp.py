import ftplib
import re
from threading import Thread


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper


class FTPProtocol(object):
    ls_format = re.compile('^([^\s]+\s+){4}(\d+)\s([^\s]+\s+){3}(.+)$')

    def __init__(self):
        self._connection = ftplib.FTP()

    @property
    def current_server(self):
        return self._connection.host

    def connect(self, url):
        if self.current_server:
            self.disconnect()
        try:
            self._connection.connect(url)
        except ftplib.all_errors:
            raise

    def size(self, file_name):
        return self._connection.size(file_name)

    def disconnect(self):
        self._connection.quit()

    def login(self, user=None, password=None, anonymous=False):
        if anonymous:
            self._connection.login()
        else:
            self._connection.login(user, password)

    @property
    def pwd(self):
        return re.findall('.*"(.*)".*', self._connection.sendcmd('pwd'))[0]

    @property
    def ls(self):
        ls = []
        self._connection.dir(ls.append)

        files = []
        for line in ls:
            file = re.findall(self.ls_format, line)[0]
            size = file[1]
            name = file[3].split(' -> ')[0]
            files.append((name, size, line.startswith('d')))
        return files

    def cwd(self, directory):
        self._connection.cwd(directory)

    def cancel_download(self):
        try:
            self._connection.sendcmd('ABOR')
        except ftplib.error_temp:
            pass

    @thread
    def upload(self, location, file_name, signal):
        with open(location) as f:
            def callback(chunk):
                signal.emit(len(chunk))

            self._connection.storbinary('STOR ' + file_name, f,
                                        callback=callback)
        signal.emit(-1)

    @thread
    def download(self, file_name, save_path, signal):
        with open(save_path, 'wb') as f:
            def callback(chunk):
                f.write(chunk)
                signal.emit(len(chunk))

            self._connection.retrbinary('RETR ' + file_name, callback)
        signal.emit(-1)

    @property
    def all_errors(self):
        return ftplib.all_errors
