from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QIcon
import wikipediaapi
import io
import urllib.request
import nltk.data
import speech_recognition as sr
from googletrans import Translator

# Download the Punkt tokenizer data for sentence tokenization
nltk.download('punkt')

def summarize_wiki_page(topic: str, lang: str = 'en', user_agent: str = 'WikiSum', max_chars: int = 500):
    wiki = wikipediaapi.Wikipedia(language=lang, user_agent=user_agent)
    page = wiki.page(topic)
    if not page.exists():
        return f"No page found for topic '{topic}'"

    # Get the first image URL (if available) from the Wikipedia page
    image_url = ""
    if 'imageinfo' in page.__dict__:
        image_info = page.imageinfo
        if len(image_info) > 0:
            image_url = image_info[0]['url']

    # Tokenize the summary into sentences using nltk Punkt tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(page.summary)

    # Find the last complete sentence within the character limit
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 1 <= max_chars:
            summary += sentence + " "
        else:
            break

    return summary, image_url

def on_submit():
    topic = entry.text()
    lang = language.currentData()
    summary, image_url = summarize_wiki_page(topic, lang=lang)
    text.setPlainText(summary)
    text.moveCursor(QtGui.QTextCursor.Start)

    # Load the first image from the URL and display it in the text area
    if image_url:
        image_data = urllib.request.urlopen(image_url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        pixmap = pixmap.scaledToWidth(text.width(), Qt.SmoothTransformation)
        text.document().addResource(QtGui.QTextDocument.ImageResource, QtCore.QUrl(image_url), pixmap)
        cursor = text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        cursor.insertImage(image_url)

def on_mode_change():
    dark_mode = mode.currentText() == 'Dark'
    window.setStyleSheet("background-color: #333333; color: white;" if dark_mode else "background-color: white; color: black;")
    entry.setStyleSheet("background-color: #4285F4; color: black; border-radius: 20px;" if dark_mode else "background-color: #dddddd; color: black; border-radius: 20px;")
    submit.setStyleSheet("background-color: #555555; color: white;" if dark_mode else "background-color: #dddddd; color: black;")
    text.setStyleSheet("background-color:#555555;color:white;" if dark_mode else "background-color: #dddddd; color: black;")
    menu_button.setStyleSheet("background-color:#0F9D58;color:white; border: none;" if dark_mode else "background-color: #0F9D58; color: black; border: none;")
    menu.setStyleSheet("background-color:#555555;color:white;" if dark_mode else "background-color: #dddddd; color: black;")
    options_title.setStyleSheet("color: white;" if dark_mode else "color: black;")

def update_menu_position():
    # Function to update the position of the menu based on the window's geometry
    menu.move(window.geometry().width() - menu.width(), window.geometry().height() - menu.height())

def on_menu_button_click():
    if menu.isHidden():
        # Show the menu with an animation
        menu.show()
        overlay_widget.show()
        animation = QPropertyAnimation(menu, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(menu.geometry())
        animation.setEndValue(QtWidgets.QApplication.desktop().availableGeometry())
        animation.start()
    else:
        # Hide the menu with an animation
        animation = QPropertyAnimation(menu, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(menu.geometry())
        animation.setEndValue(QtWidgets.QApplication.desktop().availableGeometry().adjusted(window.geometry().width(), window.geometry().height(), 0, 0))
        animation.finished.connect(lambda: hide_menu())
        animation.start()

def hide_menu():
    menu.hide()
    overlay_widget.hide()

def on_voice_search():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            query = recognizer.recognize_google(audio, language=language.currentData())
            entry.setText(query)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

def translate_to_selected_language():
    topic = entry.text()
    lang = language.currentData()
    translator = Translator()
    try:
        translation = translator.translate(topic, src=lang)
        entry.setText(translation.text)
    except Exception as e:
        print(f"Translation error: {e}")

def open_in_wikipedia():
    topic = entry.text()
    lang = language.currentData()
    if lang == 'en':
        url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    else:
        translator = Translator()
        try:
            translation = translator.translate(topic, src=lang, dest='en')
            url = f"https://en.wikipedia.org/wiki/{translation.text.replace(' ', '_')}"
        except Exception as e:
            print(f"Translation error: {e}")
            return

    import webbrowser
    webbrowser.open(url)

def toggle_fullscreen():
    if window.isFullScreen():
        window.showNormal()
    else:
        window.showFullScreen()

class EventFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == Qt.Key_F11:
            toggle_fullscreen()
        return False

app = QtWidgets.QApplication([])
window = QtWidgets.QWidget()
window.setWindowTitle("Wikipedia Summary")
window.setStyleSheet("background-color:#333333;color:white;")

# Logo
logo_url = "https://creazilla-store.fra1.digitaloceanspaces.com/emojis/52832/magnifying-glass-tilted-right-emoji-clipart-xl.png"
image_bytes = urllib.request.urlopen(logo_url).read()
pixmap = QPixmap()
pixmap.loadFromData(image_bytes)
pixmap = pixmap.scaled(int(pixmap.width() * 0.05), int(pixmap.height() * 0.05), Qt.KeepAspectRatio, Qt.SmoothTransformation)
label = QtWidgets.QLabel(window)
label.setPixmap(pixmap)
label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

# Add Title "WikiSum" between logo and menu button
title_label = QtWidgets.QLabel("WikiSum", window)
title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")  # Customize the title style

# Search bar
search_widget = QtWidgets.QWidget(window)
search_widget.setStyleSheet("background-color: #4285F4; color: black; border-radius: 20px; padding: 5px;")
search_layout = QtWidgets.QHBoxLayout(search_widget)
search_layout.setContentsMargins(10, 5, 10, 5)

entry = QtWidgets.QLineEdit(search_widget)
entry.setPlaceholderText("Search on Wikipedia")  # Set placeholder text
entry.setStyleSheet("background-color: transparent; color: black; border: none;")
entry.setFont(QtGui.QFont("REM", weight=QtGui.QFont.Bold))
search_layout.addWidget(entry)

# Voice search button
voice_search_button = QtWidgets.QPushButton("🎤", search_widget)
voice_search_button.setStyleSheet("background-color: transparent; color: white; border: none; font-size: 20px;")
voice_search_button.clicked.connect(on_voice_search)
search_layout.addWidget(voice_search_button)

# Language selection
language = QtWidgets.QComboBox(window)
language.addItem(QIcon("Flags/uk_flag.png"), 'English', 'en')
language.addItem(QIcon("Flags/germany_flag.png"), 'German', 'de')
language.addItem(QIcon("Flags/france_flag.png"), 'French', 'fr')
language.addItem(QIcon("Flags/spain_flag.png"), 'Spanish', 'es')
language.addItem(QIcon("Flags/italy_flag.png"), 'Italian', 'it')
language.addItem(QIcon("Flags/portugal_flag.png"), 'Portuguese', 'pt')
language.setStyleSheet("background-color:#555555;color:white;")
language.setFont(QtGui.QFont("Segoe UI Emoji", weight=QtGui.QFont.Bold))

# Mode selection
mode = QtWidgets.QComboBox(window)
mode.addItems(['Dark', 'Light'])
mode.currentTextChanged.connect(on_mode_change)
mode.setStyleSheet("background-color:#555555;color:white;")
mode.setFont(QtGui.QFont("REM", weight=QtGui.QFont.Bold))

# Menu
menu = QtWidgets.QWidget(window)
menu.setStyleSheet("background-color:#555555;color:white;")
menu.setFixedSize(window.geometry().width(), window.geometry().height())  # Make the menu the same size as the app
menu_layout = QtWidgets.QVBoxLayout(menu)

# "Options" title for the menu
options_title = QtWidgets.QLabel("Options", window)
options_title.setAlignment(Qt.AlignCenter)
options_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding: 5px;")
menu_layout.addWidget(options_title)

menu_layout.addWidget(language)
menu_layout.addWidget(mode)

# Accessibility submenu
accessibility_menu = QtWidgets.QMenu("Accessibility")
menu_button = QtWidgets.QPushButton("Accessibility options", menu)
menu_button.setStyleSheet("background-color: #F4B400; color: white; border: none; padding: 10px 5px; font-size: 16px; border-radius: 10px;")
menu_button.clicked.connect(lambda: accessibility_menu.exec_(menu_button.mapToGlobal(QtCore.QPoint(0, menu_button.height()))))
menu_layout.addWidget(menu_button)

magnifier_action = QtWidgets.QAction("Magnifier", accessibility_menu)
high_contrast_action = QtWidgets.QAction("High Contrast Mode", accessibility_menu)
text_to_speech_action = QtWidgets.QAction("Text-to-Speech", accessibility_menu)
accessibility_menu.addAction(magnifier_action)
accessibility_menu.addAction(high_contrast_action)
accessibility_menu.addAction(text_to_speech_action)

# "Hide menu" button with a red color
hide_menu_button = QtWidgets.QPushButton("Hide menu", menu)
hide_menu_button.setStyleSheet("background-color:#DB4437;color:white;")
hide_menu_button.clicked.connect(hide_menu)
menu_layout.addWidget(hide_menu_button)

# Overlay widget to hide other stuff when the menu is visible
overlay_widget = QtWidgets.QWidget(window)
overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
overlay_widget.hide()

# Submit button
submit = QtWidgets.QPushButton("Submit", window)
submit.setStyleSheet("background-color:#555555;color:white;")
submit.clicked.connect(on_submit)

# Text
text = QtWidgets.QPlainTextEdit(window)
text.setStyleSheet("background-color:#555555;color:white;")
text.setFont(QtGui.QFont("REM", weight=QtGui.QFont.Bold))
text.setReadOnly(True)  # Make the text read-only

# "Show in Wikipedia" button
show_in_wikipedia_button = QtWidgets.QPushButton("Show in Wikipedia", window)
show_in_wikipedia_button.setStyleSheet("background-color: #4285F4; color: black; border-radius: 20px; font-size: 14px; padding: 10px 20px;")
show_in_wikipedia_button.clicked.connect(open_in_wikipedia)

# Menu button
menu_button = QtWidgets.QPushButton("☰", window)
menu_button.setFixedWidth(50)  # Set the desired width for the menu button
menu_button.setFixedHeight(40)  # Set the desired height for the menu button
menu_button.setStyleSheet("background-color:#0F9D58;color:white; border: none;")  # Remove border
menu_button.clicked.connect(on_menu_button_click)

# Layout
layout = QtWidgets.QVBoxLayout(window)  # Use a QVBoxLayout for the window
layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins

# Header layout (logo, title, and menu button)
header_layout = QtWidgets.QHBoxLayout()
header_layout.addWidget(label)
header_layout.addWidget(title_label)
header_layout.addStretch(1)
header_layout.addWidget(menu_button)
layout.addLayout(header_layout)

# Main content layout (search, submit button, text, and "Show in Wikipedia" button)
main_content_layout = QtWidgets.QVBoxLayout()
main_content_layout.addWidget(search_widget)
main_content_layout.addWidget(submit)
main_content_layout.addWidget(text)
main_content_layout.addWidget(show_in_wikipedia_button)
layout.addLayout(main_content_layout)

layout.addWidget(menu)  # Add the menu to the window
layout.addWidget(overlay_widget)  # Add the overlay widget to the window

window.setLayout(layout)  # Set the main layout for the window

# Set the initial visibility of the options menu
menu.hide()
overlay_widget.hide()

# Start the application
window.show()

# Install event filter to handle F11 key press for fullscreen
event_filter = EventFilter()
window.installEventFilter(event_filter)

app.exec()
