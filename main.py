import ftplib
import re
import sys

from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QApplication, QWidget, QVBoxLayout, QTreeWidget, \
    QTreeWidgetItem, QDesktopWidget, QLineEdit, QLabel, QPushButton, \
    QMessageBox, QFileDialog


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.ftp = None
        self.current_server = ''

        self._init_ui()

    def _init_ui(self):
        self.main_widget = QVBoxLayout(self)
        
        self.main_widget.addWidget(QLabel('Адрес FTP-сервера:'))
        
        self.url_edit = QLineEdit()
        self.connect(self.url_edit, SIGNAL('textEdited(QString)'),
                     self.url_edited)
        self.main_widget.addWidget(self.url_edit)
        
        self.connect_btn = QPushButton('Подключиться')
        self.connect_btn.setEnabled(False)
        self.connect(self.connect_btn, SIGNAL('pressed()'), self.ftp_connect)
        self.main_widget.addWidget(self.connect_btn)

        self.path_label = QLabel()
        self.path_label.hide()
        self.main_widget.addWidget(self.path_label)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(['Имя', 'Тип'])
        self.tree_widget.setRootIsDecorated(False)
        self.connect(self.tree_widget,
                     SIGNAL('itemDoubleClicked(QTreeWidgetItem*, int)'),
                     self.double_click)
        self.tree_widget.hide()
        self.main_widget.addWidget(self.tree_widget)
        
        self.setLayout(self.main_widget)
        self.setWindowTitle('FTP Client')
        self.center()
        self.show()

    def url_edited(self, url):
        self.connect_btn.setEnabled(url != self.current_server)

    def ftp_connect(self):
        if self.ftp:
            self.ftp.quit()
        try:
            self.ftp = ftplib.FTP(self.url_edit.text())
            self.ftp.login()
        except ftplib.all_errors:
            QMessageBox().warning(self, 'Ошибка',
                                  'Невозможно подключиться к серверу')
        else:
            self.load()

    def load(self):
        self.connect_btn.setEnabled(False)

        path = re.findall('.*"(.*)".*', self.ftp.sendcmd('pwd'))[0]
        self.path_label.setText(path)
        self.path_label.show()

        self.tree_widget.clear()
        self.tree_widget.show()
        
        ls = []
        self.ftp.dir(ls.append)

        if path != '/':
            self.tree_widget.addTopLevelItem(QTreeWidgetItem(['..', 'Папка']))
        
        for line in ls:
            name = \
                re.findall('^([^\s]+\s+){8}(.+)$', line)[0][1].split(' -> ')[0]
            file_type = 'Папка' if line.startswith(
                'd') else 'Ссылка' if line.startswith('l') else 'Файл'
            self.tree_widget.addTopLevelItem(
                QTreeWidgetItem([name, file_type]))

    def open(self, directory_name):
        self.ftp.cwd(directory_name)
        self.load()
    
    def download(self, file_name):
        save_location = QFileDialog().getSaveFileName(self, 'Сохранение файла')

        if not save_location:
            return

        with open(save_location, 'wb') as f:
            self.ftp.retrbinary('RETR ' + file_name, f.write)
    
    def double_click(self, item: QTreeWidgetItem):
        try:
            self.open(item.text(0))
        except ftplib.error_perm:
            try:
                self.download(item.text(0))
            except ftplib.error_perm:
                QMessageBox().warning(self, 'Ошибка', 'Ошибка доступа к файлу')
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
