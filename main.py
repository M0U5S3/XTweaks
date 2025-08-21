# Local application imports
from controller import AppController, DebugMode
from pages.question_editor.question_editor_page import QuestionEditorPage

# Initialize AppController
if __name__ == '__main__':
    app = AppController(QuestionEditorPage, debug_mode=DebugMode.DEBUG)
    app.run()
