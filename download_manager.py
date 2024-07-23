# download_manager.py

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class DownloadManager(QObject):
    download_updated = pyqtSignal()
    download_completed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.download_history = []  # Lista para almacenar el historial de descargas

    def handle_download(self, download):
        # Suponemos que 'download' es un objeto que contiene información sobre la descarga
        download_info = {
            'url': download.url().toString(),
            'status': 'In Progress'
        }
        self.download_history.append(download_info)
        self.download_updated.emit()

        # Añadimos una descarga completa después de 5 segundos para demostración
        QTimer.singleShot(5000, lambda: self.mark_download_completed(download_info))

    def mark_download_completed(self, download_info):
        download_info['status'] = 'Completed'
        self.download_completed.emit(download_info)

    def get_download_history(self):
        return self.download_history
