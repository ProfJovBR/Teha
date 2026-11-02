"""Native Qt Widgets application: no HTML, webview, local server or browser."""
import sys
import html
from datetime import date, datetime
from pathlib import Path
from PySide6.QtCore import Qt, QDate, QTime, QTimer, QStandardPaths, QLocale
from PySide6.QtGui import QColor, QPainter, QPixmap, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
 QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
 QLabel, QStackedWidget, QTableWidget, QTableWidgetItem, QLineEdit,
 QComboBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, QDateEdit,
 QTimeEdit, QSpinBox, QDoubleSpinBox, QCalendarWidget, QTabWidget, QMenu,
 QMessageBox, QFileDialog, QScrollArea, QInputDialog, QHeaderView,
)
from .models import MODULES, IMMUTABLE
from .storage import Store

STYLE = '''
QWidget {background:white;color:#173654;font-family:"Segoe UI";font-size:14px;}
QWidget#sidebar, QWidget#sidebar QLabel {background:#112e50;color:white;}
QWidget#sidebar QPushButton {background:#1b3e64;color:white;text-align:left;border:0;}
QPushButton {background:#163d66;color:white;border-radius:8px;padding:11px 14px;}
QPushButton:hover {background:#28618d;}
QLineEdit,QTextEdit,QComboBox,QDateEdit,QTimeEdit,QSpinBox,QDoubleSpinBox {border:1px solid #d7e2ee;border-radius:6px;padding:7px;background:#fff;}
QTableWidget {border:1px solid #dce6ef;gridline-color:#e7edf5;selection-background-color:#dceefa;selection-color:#14385e;}
QHeaderView::section {background:#edf5fc;padding:10px;border:0;color:#24496d;}
QLabel#title {font-size:28px;font-weight:700;}
QLabel#notice {background:#fff4dc;color:#795722;padding:10px;border-radius:6px;}
QTabBar::tab {padding:12px;background:#edf5fc;color:#173654;} QTabBar::tab:selected {background:#14385e;color:white;}
'''


def button(text, callback):
    b = QPushButton(text)
    b.clicked.connect(lambda checked=False: callback())
    return b


def table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.verticalHeader().hide()
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return t


def populate(t, rows):
    t.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            t.setItem(i, j, QTableWidgetItem(str(value)))


class Editor(QDialog):
    def __init__(self, parent, kind, record=None, initial=None):
        super().__init__(parent)
        self.owner, self.kind = parent, kind
        self.record = record or {}
        self.values = {**self.record, **(initial or {})}
        self.widgets = {}
        self.setWindowTitle(MODULES[kind][0])
        self.resize(580, 700)
        layout = QVBoxLayout(self)
        area = QScrollArea()
        area.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        for key, label, type_, required in MODULES[kind][1]:
            value = self.values.get(key)
            if isinstance(type_, list) or type_ in ('patients','team'):
                w = QComboBox()
                if isinstance(type_, list):
                    for item in type_:
                        w.addItem(item, item)
                else:
                    w.addItem('Selecione', '')
                    for r in parent.store.list(type_):
                        w.addItem(r['name'], r['id'])
                index = w.findData(value)
                if index >= 0:
                    w.setCurrentIndex(index)
            elif type_ == 'memo':
                w = QTextEdit(str(value or ''))
                w.setAcceptRichText(False)
                w.setMaximumHeight(90)
            elif type_ == 'date':
                w = QDateEdit()
                w.setCalendarPopup(True)
                w.setDisplayFormat('dd/MM/yyyy')
                # Optional birth supports an explicit empty date.
                w.setMinimumDate(QDate(1900,1,1))
                if not required:
                    w.setSpecialValueText('Não informado')
                w.setDate(QDate.fromString(str(value),'yyyy-MM-dd') if value else QDate.currentDate() if required else w.minimumDate())
            elif type_ == 'time':
                w = QTimeEdit(QTime.fromString(str(value or '09:00'),'HH:mm'))
                w.setDisplayFormat('HH:mm')
            elif type_ in ('number','pain','money'):
                w = QDoubleSpinBox() if type_ == 'money' else QSpinBox()
                w.setRange(0 if type_ != 'number' else 1, 10 if type_ == 'pain' else 10000000 if type_ == 'money' else 1440)
                w.setValue(float(value or 0) if type_ == 'money' else int(value or (30 if type_ == 'number' else 0)))
            else:
                w = QLineEdit(str(value or ('Sala 1' if key=='chair' else '')))
            self.widgets[key] = w
            form.addRow(label + (' *' if required else ''), w)
        area.setWidget(content)
        layout.addWidget(area)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.button(QDialogButtonBox.StandardButton.Save).setText('Salvar')
        controls.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        controls.accepted.connect(self.save)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def save(self):
        values = dict(self.values)
        for key, _, type_, _ in MODULES[self.kind][1]:
            w = self.widgets[key]
            if isinstance(w, QComboBox):
                value = w.currentData()
            elif isinstance(w, QTextEdit):
                value = w.toPlainText().strip()
            elif isinstance(w, QDateEdit):
                value = w.date().toString('yyyy-MM-dd')
            elif isinstance(w, QTimeEdit):
                value = w.time().toString('HH:mm')
            elif isinstance(w, (QSpinBox,QDoubleSpinBox)):
                value = w.value()
            else:
                value = w.text().strip()
            if isinstance(w, QDateEdit):
                value = '' if w.specialValueText() and w.date()==w.minimumDate() else w.date().toString('yyyy-MM-dd')
            values[key] = value
        try:
            self.owner.store.save(self.kind, values, self.owner.store.setting('profile','Demonstração'))
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, 'Não foi possível salvar', str(e))
            return
        self.owner.refresh()
        self.accept()


class Calendar(QCalendarWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setGridVisible(True)
        self.setMinimumHeight(290)

    def paintCell(self, painter, rect, day):
        super().paintCell(painter, rect, day)
        if any(a['date']==day.toString('yyyy-MM-dd') and a['status'] not in ('Cancelado','Faltou') for a in self.store.list('appointments')):
            painter.save()
            painter.setBrush(QColor('#df4454'))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.center().x()-3,rect.bottom()-9,7,7)
            painter.restore()


class Window(QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store, self.collapsed = store, False
        self.setWindowTitle('Teha • Consultório odontológico • Demonstração local')
        self.resize(1280,850)
        self.setMinimumSize(900,650)
        root = QWidget()
        self.setCentralWidget(root)
        horizontal = QHBoxLayout(root)
        horizontal.setContentsMargins(0,0,0,0)
        self.sidebar = QWidget()
        self.sidebar.setObjectName('sidebar')
        side = QVBoxLayout(self.sidebar)
        side.addWidget(QLabel('◈ TEHA'))
        side.addWidget(button('☰',self.toggle))
        self.stack, self.pages, self.nav = QStackedWidget(), {}, []
        nav = [('home','⌂','Visão geral'),('patients','♧','Pacientes'),('appointments','▦','Agenda'),('notes','▤','Prontuário'),('teeth','◇','Odontograma'),('treatments','✓','Tratamentos'),('documents','▧','Documentos'),('finance','$','Financeiro'),('team','♙','Equipe'),('reports','▥','Relatórios'),('ai','✧','Assistente IA'),('data','⇅','Dados e backup')]
        for key, icon, text in nav:
            b = button(icon+'  '+text,lambda k=key:self.navigate(k))
            b.setToolTip(text)
            side.addWidget(b)
            self.nav.append((b,icon,text))
        side.addStretch()
        self.profile = button('◉  '+store.setting('profile','Seu nome'),self.edit_profile)
        if store.setting('photo'):
            from PySide6.QtGui import QIcon
            self.profile.setIcon(QIcon(store.setting('photo')))
        side.addWidget(self.profile)
        horizontal.addWidget(self.sidebar)
        body = QWidget()
        layout = QVBoxLayout(body)
        stripe = QLabel('')
        stripe.setFixedHeight(5)
        stripe.setStyleSheet('background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4299e1,stop:.3 #56c5a8,stop:.6 #efba55,stop:1 #d27ba7);')
        layout.addWidget(stripe)
        notice = QLabel('DEMONSTRAÇÃO LOCAL • Somente dados fictícios • Nuvem, autenticação e permissões ainda pendentes')
        notice.setObjectName('notice')
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addWidget(self.stack)
        horizontal.addWidget(body,1)
        self.tables, self.searches, self.filters = {}, {}, {}
        self.build_home()
        for key in MODULES:
            if key not in ('appointments','triages'):
                self.build_records(key)
        self.build_agenda()
        self.build_other()
        self.refresh()
        self.toggle()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)

    def new_page(self,key,title):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(title)
        label.setObjectName('title')
        layout.addWidget(label)
        self.stack.addWidget(widget)
        self.pages[key] = widget
        return layout

    def navigate(self,key):
        self.stack.setCurrentWidget(self.pages[key])
        self.refresh()

    def toggle(self):
        self.collapsed = not self.collapsed
        self.sidebar.setFixedWidth(76 if self.collapsed else 230)
        for b,icon,text in self.nav:
            b.setText(icon if self.collapsed else icon+'  '+text)
        self.profile.setText('◉' if self.collapsed else self.store.setting('profile','Seu nome'))

    def edit_profile(self):
        name, ok = QInputDialog.getText(self,'Perfil local','Nome declarado (não é login):',text=self.store.setting('profile',''))
        if ok and name.strip():
            self.store.set_setting('profile',name.strip())
            filename,_ = QFileDialog.getOpenFileName(self,'Foto de perfil opcional','','Imagens (*.png *.jpg *.jpeg)')
            if filename:
                pixmap = QPixmap(filename).scaled(72,72,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                target = self.store.path.parent/'profile.png'
                pixmap.save(str(target))
                self.store.set_setting('photo',str(target))
            self.profile.setText('◉' if self.collapsed else name.strip())
            from PySide6.QtGui import QIcon
            if self.store.setting('photo'):
                self.profile.setIcon(QIcon(self.store.setting('photo')))

    def build_home(self):
        layout = self.new_page('home','Seu consultório, em movimento.')
        self.summary = QLabel()
        layout.addWidget(self.summary)
        layout.addWidget(button('Abrir agenda',lambda:self.navigate('appointments')))
        layout.addWidget(button('Ver pacientes',lambda:self.navigate('patients')))
        layout.addStretch()

    def build_records(self,key):
        layout = self.new_page(key,MODULES[key][0])
        controls = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText('Buscar registros…')
        search.textChanged.connect(self.refresh)
        self.searches[key] = search
        controls.addWidget(search)
        if key not in ('patients','team'):
            combo = QComboBox()
            combo.currentIndexChanged.connect(self.refresh)
            self.filters[key] = combo
            controls.addWidget(combo)
        controls.addWidget(button('+ Adicionar '+('paciente' if key=='patients' else 'registro'),lambda:self.edit(key)))
        layout.addLayout(controls)
        t = table([f[1] for f in MODULES[key][1]]+['Ações'])
        if key=='patients':
            t.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.tables[key] = t
        layout.addWidget(t)
        if key=='notes':
            layout.addWidget(QLabel('Avaliações iniciais vinculadas ao paciente selecionado'))
            self.assessments = QTextEdit()
            self.assessments.setReadOnly(True)
            self.assessments.setMaximumHeight(180)
            layout.addWidget(self.assessments)

    def edit(self,key,record=None,initial=None):
        return Editor(self,key,record,initial).exec()

    def build_agenda(self):
        layout = self.new_page('appointments','Agenda')
        layout.addWidget(button('+ Agendar consulta',lambda:self.edit('appointments',initial={'date':self.calendar.selectedDate().toString('yyyy-MM-dd')})))
        self.tabs = QTabWidget()
        calendar_page, waiting_page = QWidget(), QWidget()
        calendar_layout, waiting_layout = QVBoxLayout(calendar_page), QVBoxLayout(waiting_page)
        self.calendar = Calendar(self.store)
        self.calendar.selectionChanged.connect(self.refresh)
        calendar_layout.addWidget(self.calendar)
        self.day_label = QLabel()
        calendar_layout.addWidget(self.day_label)
        self.agenda_table = table(['Horário','Paciente','Profissional','Procedimento','Situação','Ações'])
        calendar_layout.addWidget(self.agenda_table)
        waiting_layout.addWidget(QLabel('A lista inclui somente chegadas confirmadas de hoje.'))
        self.waiting_table = table(['Horário','Paciente','Profissional','Tempo desde chegada','Situação','Ações'])
        waiting_layout.addWidget(self.waiting_table)
        self.tabs.addTab(calendar_page,'Calendário')
        self.tabs.addTab(waiting_page,'Sala de espera')
        layout.addWidget(self.tabs)

    def assessment(self,a):
        records = [r for r in self.store.list('triages') if r.get('appointmentId')==a['id']]
        self.edit('triages',records[-1] if records else None,{'patient':a['patient'],'appointmentId':a['id']})

    def chart(self,patient):
        self.navigate('notes')
        self.filters['notes'].setCurrentIndex(self.filters['notes'].findData(patient))

    def actions(self,t,row,kind,record,waiting=False):
        b = QPushButton('⋯')
        b.setAccessibleName('Ações do registro')
        menu = QMenu(b)
        def add(label,callback):
            menu.addAction(label).triggered.connect(lambda checked=False:self.safe(callback))
        if kind not in IMMUTABLE:
            add('Editar',lambda:self.edit(kind,record))
        if kind=='patients':
            add('Abrir prontuário',lambda:self.chart(record['id']))
        if kind=='appointments':
            if record['date']==date.today().isoformat() and record['status'] in ('Agendado','Confirmado'):
                add('Confirmar chegada',lambda:self.store.arrive(record['id']))
            if record.get('arrivedAt') and record['status'] in ('Na sala de espera','Em atendimento'):
                add('Avaliação inicial / editar triagem',lambda:self.assessment(record))
                add('Iniciar atendimento',lambda:self.store.save(kind,{**record,'status':'Em atendimento'}))
                add('Concluir atendimento',lambda:self.store.save(kind,{**record,'status':'Concluído'}))
            add('Abrir prontuário',lambda:self.chart(record['patient']))
        if kind=='documents':
            add('Revisar / imprimir',lambda:self.print_document(record))
        if kind in IMMUTABLE:
            add('Criar novo registro / adendo',lambda:self.edit(kind,initial={'patient':record['patient']}))
        b.setMenu(menu)
        t.setCellWidget(row,t.columnCount()-1,b)
        t.horizontalHeader().setSectionResizeMode(t.columnCount()-1,QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(t.columnCount()-1,80)

    def safe(self,callback):
        try:
            callback()
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self,'Operação não concluída',str(e))

    def display(self,key,value):
        if key in ('patient','professional'):
            r = self.store.get('patients' if key=='patient' else 'team',value)
            return r['name'] if r else '—'
        return str(value if value is not None else '')

    def refresh(self,*args):
        if not hasattr(self,'summary'):
            return
        for key,combo in self.filters.items():
            selected = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('Todos os pacientes','')
            for p in self.store.list('patients'):
                combo.addItem(p['name'],p['id'])
            combo.setCurrentIndex(max(0,combo.findData(selected)))
            combo.blockSignals(False)
        for key,t in self.tables.items():
            query = self.searches[key].text().casefold()
            patient = self.filters[key].currentData() if key in self.filters else ''
            fields = MODULES[key][1]
            rows = [r for r in self.store.list(key) if (not patient or r.get('patient')==patient) and query in ' '.join(self.display(f[0],r.get(f[0],'')) for f in fields).casefold()]
            populate(t,[[self.display(f[0],r.get(f[0],'')) for f in fields]+[''] for r in rows])
            for i,r in enumerate(rows):
                self.actions(t,i,key,r)
        if not hasattr(self,'calendar'):
            return
        selected = self.calendar.selectedDate().toString('yyyy-MM-dd')
        self.day_label.setText('Caderneta • '+self.calendar.selectedDate().toString('dd/MM/yyyy'))
        appointments = sorted([a for a in self.store.list('appointments') if a['date']==selected],key=lambda a:a['time'])
        populate(self.agenda_table,[[a['time'],self.display('patient',a['patient']),self.display('professional',a['professional']),a['procedure'],a['status'],''] for a in appointments])
        for i,a in enumerate(appointments):
            self.actions(self.agenda_table,i,'appointments',a)
        waiting = self.store.waiting()
        populate(self.waiting_table,[[a['time'],self.display('patient',a['patient']),self.display('professional',a['professional']),str(max(0,int((datetime.now().astimezone()-datetime.fromisoformat(a['arrivedAt'])).total_seconds()/60)))+' min',a['status']+(' • Avaliação concluída' if any(t.get('appointmentId')==a['id'] for t in self.store.list('triages')) else ''),''] for a in waiting])
        for i,a in enumerate(waiting):
            self.actions(self.waiting_table,i,'appointments',a,True)
        self.calendar.updateCells()
        patient = self.filters['notes'].currentData()
        lines = []
        if patient:
            for r in self.store.list('triages'):
                if r['patient']==patient:
                    lines.append(f"{r['updatedAt'][:16]} • {r['reason']} • Dor {r['pain']} • {r['priority']} • {r.get('notes','')}")
                    for prev in self.store.revisions('triages',r['id']):
                        lines.append('Versão anterior: '+str(prev))
        self.assessments.setPlainText('\n'.join(lines) if patient else 'Selecione um paciente para consultar as avaliações.')
        finance = self.store.list('finance')
        balance = sum((1 if r['type']=='Receita' else -1)*float(r['amount']) for r in finance if r['status']=='Quitado')
        self.summary.setText(f"{len(self.store.list('patients'))} pacientes • {len(waiting)} aguardando / em atendimento • Saldo quitado R$ {balance:.2f}")
        if hasattr(self,'report'):
            self.report.setPlainText(self.summary.text()+'\n\nConsultas: '+str(len(self.store.list('appointments')))+'\n\nAuditoria local (últimas 100 operações):\n'+'\n'.join(' • '.join(map(str,r)) for r in self.store.connection.execute('SELECT at,actor,kind,record_id FROM audit ORDER BY id DESC LIMIT 100')))

    def print_document(self,r):
        dialog = QDialog(self)
        dialog.setWindowTitle('Revisão antes da impressão')
        dialog.resize(650,650)
        layout = QVBoxLayout(dialog)
        preview = QTextEdit()
        preview.setReadOnly(True)
        text = f"{r['title']}\n\nPaciente: {self.display('patient',r['patient'])}\nProfissional: {self.display('professional',r['professional'])}\n\n{r['content']}\n\nDocumento para revisão e assinatura. Sem assinatura digital."
        preview.setPlainText(text)
        layout.addWidget(preview)
        def print_now():
            printer = QPrinter()
            if QPrintDialog(printer,dialog).exec()==QDialog.DialogCode.Accepted:
                document = QTextDocument()
                document.setPlainText(text)
                document.print_(printer)
        layout.addWidget(button('Imprimir / salvar em PDF',print_now))
        dialog.exec()

    def build_other(self):
        layout = self.new_page('reports','Relatórios e auditoria')
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)
        layout = self.new_page('ai','Assistente IA')
        layout.addWidget(QLabel('Reservado e desativado. Nenhum dado é enviado a serviços externos.'))
        layout.addStretch()
        layout = self.new_page('data','Dados e backup')
        label = QLabel('Banco SQLite local: '+str(self.store.path)+'\n\nO backup contém dados locais e não é criptografado.\nPara restaurar: feche o app e substitua o arquivo SQLite pelo backup.\nNuvem, chaves de acesso e assinatura digital permanecem pendentes.')
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(button('Exportar backup SQLite',lambda:self.safe(self.backup)))
        layout.addStretch()

    def backup(self):
        path,_ = QFileDialog.getSaveFileName(self,'Backup local','teha-backup.sqlite3','SQLite (*.sqlite3)')
        if path:
            self.store.backup(path)
            QMessageBox.information(self,'Backup','Backup criado.')


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('Sophion')
    app.setApplicationName('TehaDemo')
    QLocale.setDefault(QLocale('pt_BR'))
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))/'teha-demo.sqlite3'
    store = Store(path)
    store.seed_demo()
    window = Window(store)
    window.show()
    app.aboutToQuit.connect(store.close)
    return app.exec()


if __name__=='__main__':
    sys.exit(main())
