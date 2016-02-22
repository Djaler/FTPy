from sys import argv, exit

from PyQt4 import QtCore
from PyQt4 import QtGui

from ftp import FTPProtocol


class MainWindow(QtGui.QWidget):
    download_progress_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        
        self.ftp = FTPProtocol()
        self.download_progress_signal.connect(self.progress,
                                              QtCore.Qt.QueuedConnection)
        
        self._init_ui()
    
    def _init_ui(self):
        self._init_icons()

        self.main_layout = QtGui.QVBoxLayout(self)
        
        self.main_layout.addWidget(QtGui.QLabel('Адрес FTP-сервера:'))
        
        self.url_edit = QtGui.QLineEdit()
        self.connect(self.url_edit, QtCore.SIGNAL('textEdited(QString)'),
                     self.url_edited)
        self.main_layout.addWidget(self.url_edit)
        
        self.connect_btn = QtGui.QPushButton('Подключиться')
        self.connect_btn.setDisabled(True)
        self.connect(self.connect_btn, QtCore.SIGNAL('pressed()'),
                     self.ftp_connect)
        self.main_layout.addWidget(self.connect_btn)
        
        self.path_label = QtGui.QLabel()
        self.path_label.hide()
        self.main_layout.addWidget(self.path_label)
        
        self.tree_widget = QtGui.QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(['Имя', 'Размер'])
        self.tree_widget.setRootIsDecorated(False)
        self.connect(self.tree_widget,
                     QtCore.SIGNAL('itemDoubleClicked(QTreeWidgetItem*, int)'),
                     self.double_click)
        self.tree_widget.hide()
        self.main_layout.addWidget(self.tree_widget)

        self.progress_window = QtGui.QDialog(self)
        self.progress_window.setWindowTitle('Загрузка')
        self.progress_window.setModal(True)
        progress_layout = QtGui.QHBoxLayout()
        self.progress_bar = QtGui.QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.cancel_download_btn = QtGui.QPushButton()
        self.cancel_download_btn.setIcon(self.cancel_icon)
        self.cancel_download_btn.setIconSize(QtCore.QSize(24, 24))
        self.connect(self.cancel_download_btn, QtCore.SIGNAL('pressed()'),
                     self.download_cancel)
        progress_layout.addWidget(self.cancel_download_btn)
        self.progress_window.setLayout(progress_layout)
        
        self.setLayout(self.main_layout)
        self.setWindowTitle('FTPy')
        self.center()
        self.show()

    def _init_icons(self):
        self.folder_icon = QtGui.QIcon('icons/folder.svg')
        self.file_icon = QtGui.QIcon('icons/file.svg')
        self.cancel_icon = QtGui.QIcon('icons/cancel.svg')

    def url_edited(self, url):
        self.connect_btn.setDisabled(url == self.ftp.current_server or not url)
    
    def ftp_connect(self):
        try:
            self.ftp.connect(self.url_edit.text())
            self.ftp.login()
        except self.ftp.all_errors:
            QtGui.QMessageBox().warning(self, 'Ошибка',
                                        'Невозможно подключиться к серверу')
            self.path_label.hide()
            self.tree_widget.hide()
        else:
            self.path_label.show()
            self.tree_widget.show()
            self.load()
        finally:
            self.adjustSize()
            self.connect_btn.setEnabled(False)
    
    def load(self):
        path = self.ftp.pwd
        self.path_label.setText(path)
        
        self.tree_widget.clear()

        if path != '/':
            item = QtGui.QTreeWidgetItem(['..', '4096'])
            item.setIcon(0, self.folder_icon)
            self.tree_widget.addTopLevelItem(item)
        
        for name, size, is_directory in self.ftp.ls:
            item = QtGui.QTreeWidgetItem([name, size])
            item.setIcon(0,
                         self.folder_icon if is_directory else self.file_icon)
            self.tree_widget.addTopLevelItem(item)
    
    def open(self, directory_name):
        self.ftp.cwd(directory_name)
        self.load()
    
    def download(self, file_name):
        save_location = QtGui.QFileDialog().getSaveFileName(self,
                                                            'Сохранение файла')
        
        if not save_location:
            return

        self.progress_bar.setMaximum(self.ftp.size(file_name))
        self.progress_bar.setValue(0)
        self.progress_window.show()

        self.ftp.download(file_name, save_location,
                          self.download_progress_signal)
    
    def progress(self, value):
        self.progress_bar.setValue(self.progress_bar.value() + value)
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.progress_window.close()
    
    def download_cancel(self):
        self.ftp.cancel_download()
        self.progress_window.close()

    def double_click(self, item: QtGui.QTreeWidgetItem):
        try:
            self.open(item.text(0))
        except self.ftp.all_errors:
            try:
                self.download(item.text(0))
            except self.ftp.all_errors:
                QtGui.QMessageBox().warning(self, 'Ошибка',
                                            'Ошибка доступа к файлу')
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QtGui.QApplication(argv)
    window = MainWindow()
    exit(app.exec_())
