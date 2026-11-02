"""
ClassPlanner - Manual Cell Editor Dialog
Allows interactive editing of individual timetable slots with real-time conflict validation.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QComboBox, QTextEdit, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager
from classplanner.solver.validator import ConflictValidator


class EditCellDialog(QDialog):
    """Dialog to manually edit or clear a timetable slot with conflict checking."""
    def __init__(self, db: DatabaseManager, timetable_id: int, section_id: int,
                 day_name: str, slot_number: int, current_entry=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.timetable_id = timetable_id
        self.section_id = section_id
        self.day_name = day_name
        self.slot_number = slot_number
        self.current_entry = current_entry
        self.section_info = self.db.get_section(section_id)

        self.setWindowTitle(f"Edit Timetable Slot — {self.section_info.get('section_name')} ({day_name} Period {slot_number})")
        self.setFixedSize(540, 460)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header Info Box
        info_group = QGroupBox("Slot Details")
        info_form = QFormLayout(info_group)
        info_form.addRow("Student Section:", QLabel(f"<b>{self.section_info.get('section_name')}</b> ({self.section_info.get('dept_code')}, Sem {self.section_info.get('semester')})"))
        info_form.addRow("Time Slot:", QLabel(f"<b>{self.day_name}</b> — Period {self.slot_number}"))
        layout.addWidget(info_group)

        # Edit Form
        form_group = QGroupBox("Cell Assignment")
        form = QFormLayout(form_group)

        self.cmb_subject = QComboBox()
        self.cmb_subject.addItem("-- [EMPTY / FREE PERIOD] --", None)

        subjects = self.db.get_subjects(
            department_id=self.section_info["department_id"],
            semester=self.section_info["semester"]
        )
        self.subject_map = {}
        for s in subjects:
            self.subject_map[s["id"]] = s
            self.cmb_subject.addItem(f"{s['code']} - {s['name']} ({s['subject_type']})", s["id"])
        self.cmb_subject.currentIndexChanged.connect(self.on_subject_changed)

        self.cmb_faculty = QComboBox()
        self.faculty_map = {f["id"]: f for f in self.db.get_faculty_list()}

        self.cmb_room = QComboBox()
        self.room_map = {r["id"]: r for r in self.db.get_classrooms()}
        for r in self.db.get_classrooms():
            self.cmb_room.addItem(f"{r['room_number']} ({r['capacity']} seats - {r['room_type']})", r["id"])

        form.addRow("Subject:", self.cmb_subject)
        form.addRow("Faculty:", self.cmb_faculty)
        form.addRow("Classroom:", self.cmb_room)
        layout.addWidget(form_group)

        # Conflict Diagnostic Box
        diag_group = QGroupBox("Real-time Conflict Validation")
        diag_lay = QVBoxLayout(diag_group)
        self.txt_diagnostics = QTextEdit()
        self.txt_diagnostics.setReadOnly(True)
        self.txt_diagnostics.setMaximumHeight(80)
        diag_lay.addWidget(self.txt_diagnostics)
        layout.addWidget(diag_group)

        # Pre-select existing entry if present
        if self.current_entry:
            s_idx = self.cmb_subject.findData(self.current_entry.get("subject_id"))
            if s_idx >= 0:
                self.cmb_subject.setCurrentIndex(s_idx)
            f_idx = self.cmb_faculty.findData(self.current_entry.get("faculty_id"))
            if f_idx >= 0:
                self.cmb_faculty.setCurrentIndex(f_idx)
            r_idx = self.cmb_room.findData(self.current_entry.get("classroom_id"))
            if r_idx >= 0:
                self.cmb_room.setCurrentIndex(r_idx)
        else:
            self.on_subject_changed()

        self.cmb_faculty.currentIndexChanged.connect(self.check_conflicts)
        self.cmb_room.currentIndexChanged.connect(self.check_conflicts)

        # Dialog Buttons
        btn_bar = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save Assignment")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.clicked.connect(self.on_save)

        self.btn_clear = QPushButton("🗑️ Clear Slot")
        self.btn_clear.clicked.connect(self.on_clear_slot)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_bar.addWidget(self.btn_clear)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(self.btn_save)
        layout.addLayout(btn_bar)

        self.check_conflicts()

    def on_subject_changed(self):
        sub_id = self.cmb_subject.currentData()
        self.cmb_faculty.clear()
        if not sub_id:
            self.cmb_faculty.setEnabled(False)
            self.cmb_room.setEnabled(False)
            self.txt_diagnostics.setHtml("<font color='green'>Slot will be marked as Free.</font>")
            self.btn_save.setEnabled(True)
            return

        self.cmb_faculty.setEnabled(True)
        self.cmb_room.setEnabled(True)

        # Populate faculties qualified for subject
        sub_facs = self.db.get_subject_faculties(sub_id)
        if sub_facs:
            for f in sub_facs:
                self.cmb_faculty.addItem(f"{f['name']} ({f['faculty_id']})", f["id"])
        else:
            # Fallback to all dept faculty
            for f in self.faculty_map.values():
                if f["department_id"] == self.section_info["department_id"]:
                    self.cmb_faculty.addItem(f"{f['name']} ({f['faculty_id']})", f["id"])

        self.check_conflicts()

    def check_conflicts(self):
        sub_id = self.cmb_subject.currentData()
        if not sub_id:
            self.txt_diagnostics.setHtml("<font color='green'>Slot will be marked as Free.</font>")
            self.btn_save.setEnabled(True)
            return

        fac_id = self.cmb_faculty.currentData()
        room_id = self.cmb_room.currentData()

        if not fac_id or not room_id:
            self.btn_save.setEnabled(False)
            return

        all_entries = self.db.get_timetable_entries(self.timetable_id)
        fac_avail = self.db.get_faculty_availability(fac_id)
        current_id = self.current_entry["id"] if self.current_entry else None

        is_valid, hard_conflicts, warnings = ConflictValidator.validate_assignment(
            timetable_id=self.timetable_id,
            section_id=self.section_id,
            day_name=self.day_name,
            slot_number=self.slot_number,
            subject_id=sub_id,
            faculty_id=fac_id,
            classroom_id=room_id,
            existing_entries=all_entries,
            section_info=self.section_info,
            faculty_info=self.faculty_map[fac_id],
            classroom_info=self.room_map[room_id],
            subject_info=self.subject_map[sub_id],
            faculty_availability=fac_avail,
            current_entry_id=current_id
        )

        html = ""
        if hard_conflicts:
            html += "<b style='color:red;'>HARD CONFLICTS (Cannot Save):</b><br/>"
            for c in hard_conflicts:
                html += f"<font color='red'>• {c}</font><br/>"
            self.btn_save.setEnabled(False)
        else:
            html += "<b style='color:green;'>✓ No hard conflicts detected. Valid placement.</b><br/>"
            self.btn_save.setEnabled(True)

        if warnings:
            html += "<b style='color:#B86200;'>Warnings:</b><br/>"
            for w in warnings:
                html += f"<font color='#B86200'>• {w}</font><br/>"

        self.txt_diagnostics.setHtml(html)

    def on_clear_slot(self):
        reply = QMessageBox.question(
            self,
            "Clear Slot",
            f"Are you sure you want to clear this period slot for {self.section_info.get('section_name')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.current_entry:
                self.db.delete_timetable_entry(self.current_entry["id"])
            self.accept()

    def on_save(self):
        sub_id = self.cmb_subject.currentData()
        if not sub_id:
            if self.current_entry:
                self.db.delete_timetable_entry(self.current_entry["id"])
            self.accept()
            return

        fac_id = self.cmb_faculty.currentData()
        room_id = self.cmb_room.currentData()

        if self.current_entry:
            self.db.update_timetable_entry(self.current_entry["id"], sub_id, fac_id, room_id)
        else:
            self.db.insert_single_entry(
                self.timetable_id, self.section_id, self.day_name, self.slot_number,
                sub_id, fac_id, room_id
            )

        QMessageBox.information(self, "Updated", "Timetable slot updated successfully.")
        self.accept()

