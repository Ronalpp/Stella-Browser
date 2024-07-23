from PyQt6.QtCore import QUrl, Qt, QStringListModel
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QToolBar, QLineEdit, QMenu, QToolButton, QFileDialog, QWidget, QVBoxLayout, QDialog, QListWidget, QListWidgetItem, QPushButton, QCompleter, QPlainTextEdit)
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage  # Importar desde PyQt6.QtWebEngineCore
import os
from download_manager import DownloadManager  # Asegúrate de que esta importación sea correcta

class VideoWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_url = None

    def createWindow(self, _type):
        # Aquí puedes crear una ventana para mostrar el video si es necesario
        return super().createWindow(_type)

    def acceptNavigationRequest(self, url: QUrl, type, isMainFrame):
        if url.toString().endswith(".mp4"):
            self.video_url = url
            return False
        return super().acceptNavigationRequest(url, type, isMainFrame)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Set window properties
        self.setWindowTitle('Stella Browser')
        self.setWindowIcon(QIcon('icons/Logo.png'))

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Create toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Add buttons
        self.create_buttons()

        # Create and set up QCompleter
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.url_model = QStringListModel()
        self.completer.setModel(self.url_model)
        self.url_bar = QLineEdit()
        self.url_bar.setCompleter(self.completer)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        # Add new tab button
        add_tab_btn = QToolButton()
        add_tab_btn.setIcon(QIcon('icons/new-tab.svg'))
        add_tab_btn.clicked.connect(self.add_tab)
        self.toolbar.addWidget(add_tab_btn)

        # Add circular download button (hidden initially)
        self.download_btn = QToolButton()
        self.download_btn.setIcon(QIcon('icons/download.svg'))
        self.download_btn.setVisible(False)
        self.download_btn.clicked.connect(self.show_download_history)
        self.toolbar.addWidget(self.download_btn)

        # Initialize download manager and history
        self.download_manager = DownloadManager()  # Initialize the download manager
        self.closed_tabs = []  # Track closed tabs for reopening
        self.setup_download_handling()

        # Initialize visited URLs list
        self.visited_urls = []

        # Add first tab
        self.add_tab()

        # Keyboard shortcuts
        self.create_shortcuts()

    def create_buttons(self):
        # Add back button
        back_btn = QAction(QIcon('icons/back.svg'), '', self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        self.toolbar.addAction(back_btn)

        # Add forward button
        forward_btn = QAction(QIcon('icons/forward.svg'), '', self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.toolbar.addAction(forward_btn)

        # Add reload button
        reload_btn = QAction(QIcon('icons/reload.svg'), '', self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.toolbar.addAction(reload_btn)

        # Add home button
        home_btn = QAction(QIcon('icons/home.svg'), '', self)
        home_btn.triggered.connect(self.navigate_home)
        self.toolbar.addAction(home_btn)

        # Add DevTools button
        devtools_btn = QAction(QIcon('icons/devtools.svg'), 'Open DevTools', self)
        devtools_btn.triggered.connect(self.open_devtools)
        self.toolbar.addAction(devtools_btn)

        # Add open video button
        open_video_btn = QAction(QIcon('icons/video.svg'), 'Open Video', self)
        open_video_btn.triggered.connect(self.open_video)
        self.toolbar.addAction(open_video_btn)

    def create_shortcuts(self):
        # Create keyboard shortcuts using key sequences
        self.add_shortcut(QKeySequence("Ctrl+T"), self.add_tab)
        self.add_shortcut(QKeySequence("Ctrl+W"), lambda: self.close_tab(self.tabs.currentIndex()))
        self.add_shortcut(QKeySequence("Ctrl+R"), lambda: self.current_browser().reload())
        self.add_shortcut(QKeySequence("Ctrl+N"), self.add_tab)
        self.add_shortcut(QKeySequence("Ctrl+Shift+T"), self.reopen_last_closed_tab)
        self.add_shortcut(QKeySequence("Ctrl+Tab"), self.next_tab)
        self.add_shortcut(QKeySequence("Ctrl+Shift+Tab"), self.previous_tab)
        self.add_shortcut(QKeySequence("Alt+Left"), lambda: self.current_browser().back())
        self.add_shortcut(QKeySequence("Alt+Right"), lambda: self.current_browser().forward())
        self.add_shortcut(QKeySequence("Ctrl+L"), self.focus_url_bar)
        self.add_shortcut(QKeySequence("F11"), self.toggle_full_screen)
        self.add_shortcut(QKeySequence("Ctrl+Shift+I"), self.open_devtools)  # Shortcut to open DevTools

    def add_shortcut(self, key_sequence, action):
        shortcut = QShortcut(key_sequence, self)
        shortcut.activated.connect(action)

    def add_tab(self):
        try:
            browser = QWebEngineView()
            browser.setPage(VideoWebEnginePage(browser))
            google_url = QUrl("https://www.google.com")
            browser.setUrl(google_url)
            index = self.tabs.addTab(browser, 'Loading...')
            self.tabs.setCurrentIndex(index)

            browser.titleChanged.connect(
                lambda title, browser=browser: self.update_tab_title(browser, title))
            browser.urlChanged.connect(
                lambda url, browser=browser: self.update_url(url) if self.tabs.currentWidget() == browser else None)
            browser.iconChanged.connect(lambda icon: self.update_tab_icon(icon, index))
            browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            browser.customContextMenuRequested.connect(self.context_menu)
            browser.page().profile().downloadRequested.connect(self.handle_download)

        except Exception as e:
            print(f"Error adding tab: {e}")

    def setup_download_handling(self):
        self.download_manager.download_updated.connect(self.update_download_status)
        self.download_manager.download_completed.connect(self.download_completed)

    def handle_download(self, download):
        try:
            self.download_manager.handle_download(download)
            self.start_download_animation()
        except Exception as e:
            print(f"Error handling download: {e}")

    def update_download_status(self, download):
        self.download_btn.setVisible(True)
        if download:
            for d in self.download_manager.downloads:
                if d['url'] == download.url():
                    status = d.get('status', 'unknown')
                    self.download_btn.setToolTip(f"Downloading: {status}")

    def download_completed(self, download):
        self.download_btn.setVisible(False)
        print(f"Download completed: {download.url()}")

    def start_download_animation(self):
        try:
            self.download_btn.setIcon(QIcon('icons/download-anim.svg'))
        except Exception as e:
            print(f"Error starting download animation: {e}")

    def stop_download_animation(self):
        try:
            self.download_btn.setIcon(QIcon('icons/download.svg'))
        except Exception as e:
            print(f"Error stopping download animation: {e}")

    def show_download_history(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Download History")
            dialog.resize(400, 300)
            layout = QVBoxLayout(dialog)
            list_widget = QListWidget(dialog)
            for item in self.download_manager.downloads:
                list_item = QListWidgetItem(f"File: {item['path']} - Status: {item['status']}")
                list_widget.addItem(list_item)
            layout.addWidget(list_widget)
            dialog.exec()
        except Exception as e:
            print(f"Error showing download history: {e}")

    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        self.tabs.setTabText(index, title or 'Untitled')

    def update_url(self, url):
        self.url_bar.setText(url.toString())
        self.url_bar.setToolTip(url.toString())

    def update_tab_icon(self, icon, index):
        self.tabs.setTabIcon(index, icon)

    def context_menu(self, pos):
        try:
            menu = QMenu(self)
            inspect_action = menu.addAction("Inspect Element")
            inspect_action.triggered.connect(self.inspect_element)
            view_source_action = menu.addAction("View Page Source")
            view_source_action.triggered.connect(self.view_page_source)
            menu.exec(self.tabs.mapToGlobal(pos))
        except Exception as e:
            print(f"Error displaying context menu: {e}")

    def inspect_element(self):
        try:
            browser = self.current_browser()
            if browser:
                browser.page().runJavaScript("window.inspectElement()")
                print("Inspect Element action triggered")
        except Exception as e:
            print(f"Error inspecting element: {e}")

    def view_page_source(self):
        try:
            browser = self.current_browser()
            if browser:
                url = browser.url().toString()
                source_code = browser.page().toHtml()
                dialog = QDialog(self)
                dialog.setWindowTitle("Page Source")
                dialog.resize(800, 600)
                layout = QVBoxLayout(dialog)
                text_edit = QPlainTextEdit(dialog)
                text_edit.setPlainText(source_code)
                text_edit.setReadOnly(True)
                layout.addWidget(text_edit)
                dialog.exec()
        except Exception as e:
            print(f"Error viewing page source: {e}")

    def open_video(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4)")
            if file_name:
                # Create a new video widget
                video_widget = QVideoWidget()
                media_player = QMediaPlayer()
                media_player.setVideoOutput(video_widget)
                media_player.setSource(QUrl.fromLocalFile(file_name))

                # Create a dialog to display the video
                dialog = QDialog(self)
                dialog.setWindowTitle("Play Video")
                dialog.resize(800, 600)
                layout = QVBoxLayout(dialog)
                layout.addWidget(video_widget)

                # Play the video
                media_player.play()

                dialog.exec()
        except Exception as e:
            print(f"Error opening video: {e}")

    def current_browser(self):
        return self.tabs.currentWidget() if isinstance(self.tabs.currentWidget(), QWebEngineView) else None

    def navigate_to_url(self):
        url = QUrl(self.url_bar.text())
        if url.isValid():
            self.current_browser().setUrl(url)

    def navigate_home(self):
        home_url = QUrl("https://www.google.com")
        self.current_browser().setUrl(home_url)

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def focus_url_bar(self):
        self.url_bar.setFocus()

    def close_tab(self, index):
        try:
            widget = self.tabs.widget(index)
            if widget:
                self.closed_tabs.append(widget.url().toString())  # Store the URL of the closed tab
                widget.deleteLater()
                self.tabs.removeTab(index)
        except Exception as e:
            print(f"Error closing tab: {e}")

    def reopen_last_closed_tab(self):
        if self.closed_tabs:
            last_url = self.closed_tabs.pop()
            self.add_tab()
            self.current_browser().setUrl(QUrl(last_url))

    def next_tab(self):
        current_index = self.tabs.currentIndex()
        next_index = (current_index + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next_index)

    def previous_tab(self):
        current_index = self.tabs.currentIndex()
        prev_index = (current_index - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(prev_index)

    def open_devtools(self):
        try:
            self.current_browser().page().runJavaScript("window.openDevTools()")
        except Exception as e:
            print(f"Error opening DevTools: {e}")
