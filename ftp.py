import ftplib
import re
import threading


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper


class FTPProtocol(object):
    def __init__(self):
        self._connection = None
        self._current_server = ''

    @property
    def current_server(self):
        return self._current_server

    def connect(self, url):
        if self._connection:
            self.disconnect()
        try:
            self._connection = ftplib.FTP(url)
        except ftplib.all_errors:
            raise
        else:
            self._current_server = url

    def disconnect(self):
        self._connection.quit()
        self._current_server = ''

    def login(self, user=None, password=None):
        self._connection.login(user, password)

    @property
    def pwd(self):
        return re.findall('.*"(.*)".*', self._connection.sendcmd('pwd'))[0]

    @property
    def ls(self):
        ls = []
        self._connection.dir(ls.append)
        return ls

    def cwd(self, directory):
        self._connection.cwd(directory)

    def get_size(self, file_name):
        return self._connection.size(file_name)

    @thread
    def download(self, file_name, save_path, signal):
        with open(save_path, 'wb') as f:
            def callback(chunk):
                f.write(chunk)
                signal.emit(len(chunk))

            self._connection.retrbinary('RETR ' + file_name, callback)

    @property
    def exceptions(self):
        return ftplib.all_errors
