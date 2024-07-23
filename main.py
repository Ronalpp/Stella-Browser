import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Stella Browser')
    app.setApplicationDisplayName('Stella Browser')
    app.setOrganizationName('Scientyfic World')

    with open("styles.qss", "r") as file:
        app.setStyleSheet(file.read())

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
