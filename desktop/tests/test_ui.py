import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from teha.storage import Store
from teha.app import Window, Editor

class NativeUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_native_screens_and_patient_save(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'test.sqlite3')
            store.seed_demo()
            window=Window(store)
            window.show()
            for key,page in window.pages.items():
                window.navigate(key)
                self.app.processEvents()
                self.assertIs(window.stack.currentWidget(),page)
            dialog=Editor(window,'patients')
            dialog.widgets['name'].setText('Paciente novo (teste)')
            dialog.save()
            self.assertEqual(len(store.list('patients')),7)
            self.assertEqual(window.tables['patients'].rowCount(),7)
            window.timer.stop()
            window.close()
            store.close()

if __name__=='__main__':
    unittest.main()
