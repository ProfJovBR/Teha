import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from teha.storage import Store

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name)/'clinic.sqlite3')
        self.store.seed_demo()
        self.a = dict(patient='demo-patient-0', professional='demo-dentist', date=date.today().isoformat(), time='09:00',duration=30,chair='Sala 1',procedure='Teste',status='Agendado')

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_seed_does_not_duplicate_or_overwrite(self):
        p=self.store.get('patients','demo-patient-0')
        self.store.save('patients',{**p,'name':'Alterado'})
        self.store.seed_demo()
        self.assertEqual(len(self.store.list('patients')),6)
        self.assertEqual(self.store.get('patients',p['id'])['name'],'Alterado')

    def test_conflicts_and_adjacent_slot(self):
        self.store.save('appointments',self.a)
        for changes in ({'time':'09:15'}, {'patient':'demo-patient-1','chair':'Sala 2'}, {'chair':' sala 1 ','patient':'demo-patient-1'}):
            with self.assertRaisesRegex(ValueError,'Conflito'):
                self.store.save('appointments',{**self.a,**changes})
        self.store.save('appointments',{**self.a,'time':'09:30'})
        self.assertEqual(len(self.store.list('appointments')),2)

    def test_future_appointment_not_in_waiting_room(self):
        a=self.store.save('appointments',{**self.a,'date':(date.today()+timedelta(days=1)).isoformat()})
        with self.assertRaises(ValueError):
            self.store.arrive(a['id'])
        self.assertEqual(self.store.waiting(),[])

    def test_checkin_assessment_revision_and_completion(self):
        a=self.store.save('appointments',self.a)
        self.store.arrive(a['id'])
        self.assertEqual(len(self.store.waiting()),1)
        t=self.store.save('triages',dict(patient=a['patient'],appointmentId=a['id'],reason='Dor',pain=3,priority='Rotina'))
        self.store.save('triages',{**t,'reason':'Dor corrigida'})
        self.assertEqual(self.store.revisions('triages',t['id'])[0]['reason'],'Dor')
        self.store.save('appointments',{**self.store.get('appointments',a['id']),'status':'Concluído'})
        self.assertEqual(self.store.waiting(),[])

    def test_cannot_reassign_assessment_to_another_patient(self):
        a=self.store.save('appointments',self.a)
        with self.assertRaises(ValueError):
            self.store.save('triages',dict(patient='demo-patient-1',appointmentId=a['id'],reason='Dor',pain=1,priority='Rotina'))

    def test_preserved_notes_and_backup(self):
        n=self.store.save('notes',dict(patient='demo-patient-0',professional='demo-dentist',kind='Anamnese',content='Teste'))
        with self.assertRaisesRegex(ValueError,'preservado'):
            self.store.save('notes',{**n,'content':'Alterado'})
        path=Path(self.temp.name)/'backup.sqlite3'
        self.store.backup(path)
        backup=Store(path)
        self.assertEqual(backup.get('notes',n['id'])['content'],'Teste')
        backup.close()

if __name__=='__main__':
    unittest.main()
