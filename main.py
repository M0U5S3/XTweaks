from controller import AppController
from pages.question_editor_page import QuestionEditorPage

if __name__ == '__main__':
    app = AppController(home_page=QuestionEditorPage)
    app.run()
