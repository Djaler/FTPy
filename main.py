from sys import argv, exit
from os.path import getsize

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ftp import FTPProtocol


class MainWindow(QWidget):
    progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.ftp = FTPProtocol()
        self.progress_signal.connect(self.progress, Qt.QueuedConnection)
        
        self._init_ui()

    def _init_ui(self):
        self._init_icons()

        self.main_layout = QVBoxLayout()
        
        self.main_layout.addWidget(QLabel('Адрес FTP-сервера:'))
        
        self.url_edit = QLineEdit()
        self.connect(self.url_edit, SIGNAL('textEdited(QString)'),
                     self.url_edited)
        self.main_layout.addWidget(self.url_edit)

        anonymous_login_layout = QHBoxLayout()
        self.anonymous_login_check_box = QCheckBox('Анонимно')
        self.anonymous_login_check_box.setChecked(True)
        self.connect(self.anonymous_login_check_box,
                     SIGNAL('stateChanged(int)'), self.anonymous_login_changed)
        anonymous_login_layout.addWidget(self.anonymous_login_check_box)
        self.main_layout.addLayout(anonymous_login_layout)

        self.login_label = QLabel('Логин:')
        self.login_label.hide()
        self.main_layout.addWidget(self.login_label)
        self.login_edit = QLineEdit()
        self.login_edit.hide()
        self.main_layout.addWidget(self.login_edit)
        self.password_label = QLabel('Пароль:')
        self.password_label.hide()
        self.main_layout.addWidget(self.password_label)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.hide()
        self.main_layout.addWidget(self.password_edit)

        self.connect_btn = QPushButton('Подключиться')
        self.connect_btn.setDisabled(True)
        self.connect(self.connect_btn, SIGNAL('pressed()'), self.ftp_connect)
        self.main_layout.addWidget(self.connect_btn)
        
        self.path_label = QLabel()
        self.path_label.hide()
        self.main_layout.addWidget(self.path_label)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(['Имя', 'Размер'])
        self.tree_widget.setRootIsDecorated(False)
        self.connect(self.tree_widget,
                     SIGNAL('itemDoubleClicked(QTreeWidgetItem*, int)'),
                     self.double_click)
        self.tree_widget.hide()
        self.main_layout.addWidget(self.tree_widget)

        self.upload_file_label = QLabel('Файл для загрузки:')
        self.upload_file_label.hide()
        self.main_layout.addWidget(self.upload_file_label)
        self.upload_file_layout = QHBoxLayout()
        self.upload_file_edit = QLineEdit()
        self.upload_file_edit.setReadOnly(True)
        self.upload_file_edit.hide()
        self.upload_file_layout.addWidget(self.upload_file_edit)

        self.choose_upload_file_btn = QPushButton('Выбрать')
        self.connect(self.choose_upload_file_btn, SIGNAL('pressed()'),
                     self.choose_upload_file)
        self.choose_upload_file_btn.hide()
        self.upload_file_layout.addWidget(self.choose_upload_file_btn)
        self.main_layout.addLayout(self.upload_file_layout)

        self.upload_btn = QPushButton('Загрузить')
        self.upload_btn.hide()
        self.upload_btn.setDisabled(True)
        self.connect(self.upload_btn, SIGNAL('pressed()'), self.upload)
        self.main_layout.addWidget(self.upload_btn)

        self.progress_window = QDialog(self)
        self.progress_window.setModal(True)
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.cancel_download_btn = QPushButton()
        self.cancel_download_btn.setIcon(self.cancel_icon)
        self.cancel_download_btn.setIconSize(QSize(24, 24))
        self.connect(self.cancel_download_btn, SIGNAL('pressed()'),
                     self.download_cancel)
        progress_layout.addWidget(self.cancel_download_btn)
        self.progress_window.setLayout(progress_layout)
        
        self.setLayout(self.main_layout)
        self.setWindowTitle('FTPy')
        self.center()
        self.show()

    def _init_icons(self):
        self.folder_icon = QIcon('icons/folder.svg')
        self.file_icon = QIcon('icons/file.svg')
        self.cancel_icon = QIcon('icons/cancel.svg')

    def choose_upload_file(self):
        upload_file = QFileDialog().getOpenFileName(self)

        if not upload_file:
            return

        self.upload_file_edit.setText(upload_file)
        self.upload_btn.setEnabled(True)

    def upload(self):
        self.progress_window.setWindowTitle('Загрузка')

        path = self.upload_file_edit.text()

        self.progress_bar.setMaximum(getsize(path))

        self.progress_bar.setValue(0)
        self.progress_window.show()

        file_name = path.split('/')[-1]

        self.ftp.upload(path, file_name, self.progress_signal)

    def anonymous_login_changed(self, state):
        if state == Qt.Checked:
            self.login_label.hide()
            self.login_edit.hide()
            self.password_label.hide()
            self.password_edit.hide()
        else:
            self.login_label.show()
            self.login_edit.show()
            self.password_label.show()
            self.password_edit.show()

        self.adjustSize()

    def url_edited(self, url):
        self.connect_btn.setEnabled(url != '')
    
    def ftp_connect(self):
        try:
            self.ftp.connect(self.url_edit.text())
            if self.anonymous_login_check_box.isChecked():
                self.ftp.login(anonymous=True)
            else:
                self.ftp.login(self.login_edit.text(),
                               self.password_edit.text())
        except self.ftp.all_errors as e:
            QMessageBox().warning(self, 'Невозможно подключиться к серверу',
                                  str(e))
            self.path_label.hide()
            self.tree_widget.hide()

            self.upload_file_label.hide()
            self.upload_file_edit.hide()
            self.choose_upload_file_btn.hide()
            self.upload_btn.hide()
        else:
            self.path_label.show()
            self.tree_widget.show()

            self.upload_file_label.show()
            self.upload_file_edit.show()
            self.choose_upload_file_btn.show()
            self.upload_btn.show()

            self.load()
        finally:
            self.adjustSize()
            self.connect_btn.setEnabled(False)

    def load(self):
        path = self.ftp.pwd
        self.path_label.setText(path)
        
        self.tree_widget.clear()

        if path != '/':
            item = QTreeWidgetItem(['..', '4096'])
            item.setIcon(0, self.folder_icon)
            self.tree_widget.addTopLevelItem(item)
        
        for name, size, is_directory in self.ftp.ls:
            item = QTreeWidgetItem([name, size])
            item.setIcon(0,
                         self.folder_icon if is_directory else self.file_icon)
            self.tree_widget.addTopLevelItem(item)
    
    def open(self, directory_name):
        self.ftp.cwd(directory_name)
        self.load()
    
    def download(self, file_name, size):
        save_location = QFileDialog().getSaveFileName(self, 'Сохранение файла')

        if not save_location:
            return

        self.progress_window.setWindowTitle('Загрузка')
        try:
            self.progress_bar.setMaximum(self.ftp.size(file_name))
        except self.ftp.all_errors:
            self.progress_bar.setMaximum(size)

        self.progress_bar.setValue(0)
        self.progress_window.show()

        self.ftp.download(file_name, save_location, self.progress_signal)
    
    def progress(self, value):
        if value == -1:
            self.progress_window.hide()
            self.load()
        else:
            self.progress_bar.setValue(self.progress_bar.value() + value)

    def download_cancel(self):
        self.ftp.cancel_download()
        self.progress_window.hide()

    def double_click(self, item):
        try:
            self.open(item.text(0))
        except self.ftp.all_errors:
            try:
                self.download(item.text(0), int(item.text(1)))
            except self.ftp.all_errors as e:
                QMessageBox().warning(self, 'Ошибка доступа к файлу', str(e))
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(argv)
    window = MainWindow()
    exit(app.exec_())
