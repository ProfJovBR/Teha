"""SQLite repository. Audited, atomic writes; revisions retain previous values."""
import json
from contextlib import closing
import sqlite3
from datetime import datetime, date
from pathlib import Path
from uuid import uuid4
from .models import MODULES, IMMUTABLE


def timestamp():
    return datetime.now().astimezone().isoformat()


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.executescript('''
        CREATE TABLE IF NOT EXISTS records(kind TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(kind,id));
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT, actor TEXT, kind TEXT, record_id TEXT, previous TEXT, current TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        PRAGMA user_version=1;
        ''')

    def list(self, kind):
        return [json.loads(r[0]) for r in self.connection.execute('SELECT payload FROM records WHERE kind=? ORDER BY rowid', (kind,))]

    def get(self, kind, id):
        row = self.connection.execute('SELECT payload FROM records WHERE kind=? AND id=?', (kind, id)).fetchone()
        return json.loads(row[0]) if row else None

    def setting(self, key, default=''):
        row = self.connection.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        with self.connection:
            self.connection.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value))

    def validate(self, kind, data, old):
        if kind not in MODULES:
            raise ValueError('Tipo de registro inválido.')
        for key, label, field_type, required in MODULES[kind][1]:
            value = data.get(key)
            if required and (value is None or str(value).strip() == ''):
                raise ValueError('Preencha: ' + label)
            if isinstance(field_type, list) and value not in field_type:
                raise ValueError('Opção inválida: ' + label)
            if field_type in ('patients', 'team') and value and not self.get(field_type, value):
                raise ValueError('Cadastro vinculado não encontrado: ' + label)
        if old and kind in IMMUTABLE:
            raise ValueError('Registro preservado. Crie uma correção / adendo.')
        if kind == 'patients' and data.get('birth') and date.fromisoformat(data['birth']) > date.today():
            raise ValueError('Nascimento não pode estar no futuro.')
        if kind == 'triages':
            if not 0 <= float(data['pain']) <= 10:
                raise ValueError('Dor deve estar entre 0 e 10.')
            if data.get('appointmentId'):
                appointment = self.get('appointments', data['appointmentId'])
                if not appointment or appointment['patient'] != data['patient']:
                    raise ValueError('Avaliação deve pertencer ao paciente da consulta.')
        if kind == 'teeth' and str(data['tooth']) not in {str(q*10+t) for q in range(1,9) for t in range(1,9 if q<5 else 6)}:
            raise ValueError('Use um dente FDI válido: 11–48 ou 51–85.')
        if kind in ('finance', 'treatments') and float(data['amount']) <= 0:
            raise ValueError('O valor deve ser maior que zero.')
        if kind != 'appointments':
            return
        date.fromisoformat(data['date'])
        start = datetime.strptime(data['time'], '%H:%M')
        minutes = start.hour * 60 + start.minute
        duration = int(data['duration'])
        if duration < 1 or minutes + duration > 1440:
            raise ValueError('Duração inválida ou consulta termina no dia seguinte.')
        if data['status'] in ('Na sala de espera', 'Em atendimento') and (data['date'] != date.today().isoformat() or not data.get('arrivedAt')):
            raise ValueError('Confirme a chegada de uma consulta de hoje primeiro.')
        if data['status'] in ('Cancelado', 'Faltou'):
            return
        for other in self.list(kind):
            if other['id'] == data.get('id') or other['date'] != data['date'] or other['status'] in ('Cancelado', 'Faltou'):
                continue
            same = (other['patient'] == data['patient'] or other['professional'] == data['professional'] or other['chair'].strip().casefold() == data['chair'].strip().casefold())
            h, m = map(int, other['time'].split(':'))
            begin = h*60+m
            if same and minutes < begin+int(other['duration']) and minutes+duration > begin:
                raise ValueError('Conflito de horário: paciente, profissional ou sala.')

    def save(self, kind, values, actor='Demonstração'):
        data = dict(values)
        data.setdefault('id', str(uuid4()))
        with self.connection:
            # Serialize the conflict check together with its write, including across processes.
            self.connection.execute('BEGIN IMMEDIATE')
            old = self.get(kind, data['id'])
            self.validate(kind, data, old)
            data['createdAt'] = old['createdAt'] if old else timestamp()
            data['updatedAt'] = timestamp()
            data['author'] = actor
            encoded = json.dumps(data, ensure_ascii=False)
            self.connection.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, data['id'], encoded))
            self.connection.execute('INSERT INTO audit(at,actor,kind,record_id,previous,current) VALUES (?,?,?,?,?,?)', (timestamp(), actor, kind, data['id'], json.dumps(old, ensure_ascii=False) if old else None, encoded))
        return data

    def arrive(self, id):
        a = self.get('appointments', id)
        if not a or a['date'] != date.today().isoformat() or a['status'] not in ('Agendado', 'Confirmado'):
            raise ValueError('Confirme a chegada apenas para uma consulta de hoje ainda não atendida.')
        return self.save('appointments', {**a, 'arrivedAt':timestamp(), 'status':'Na sala de espera'})

    def waiting(self):
        return sorted([a for a in self.list('appointments') if a['date']==date.today().isoformat() and a.get('arrivedAt') and a['status'] in ('Na sala de espera','Em atendimento')], key=lambda a:a['arrivedAt'])

    def revisions(self, kind, id):
        return [json.loads(r[0]) for r in self.connection.execute('SELECT previous FROM audit WHERE kind=? AND record_id=? AND previous IS NOT NULL ORDER BY id', (kind,id))]

    def backup(self, path):
        target = Path(path)
        if target.resolve() == self.path.resolve():
            raise ValueError('Escolha outro arquivo para o backup.')
        with closing(sqlite3.connect(target)) as dest:
            self.connection.backup(dest)

    def seed_demo(self):
        if self.setting('demo-v1'):
            return
        for i, name in enumerate(['Ana Oliveira','Bruno Almeida','Carla Souza','Diego Martins','Elisa Ferreira','Fábio Costa']):
            id = f'demo-patient-{i}'
            if not self.get('patients', id):
                self.save('patients', {'id':id, 'name':name+' (teste)', 'notes':'Dados fictícios para demonstração.'})
        if not self.get('team','demo-dentist'):
            self.save('team', {'id':'demo-dentist','name':'Dentista de demonstração','role':'Dentista','registration':''})
        self.set_setting('demo-v1', '1')

    def close(self):
        self.connection.close()
