"""
ClassPlanner - Working Hours & Time Slots Management
Configures college operational schedule, working days, period lengths, and break timings.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QTimeEdit, QSpinBox, QCheckBox,
    QGridLayout
)
from PySide6.QtCore import QTime, Qt
from datetime import datetime, timedelta
from classplanner.database.db_manager import DatabaseManager
from classplanner.config import DAYS_OF_WEEK


class WorkingHoursWidget(QWidget):
    """Working Days, Hours, and Time Slots configuration view."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.day_checkboxes = {}
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Title
        lbl_title = QLabel("Working Hours & Time Slots Configuration")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")
        main_layout.addWidget(lbl_title)

        top_container = QHBoxLayout()

        # 1. Working Days Group
        days_group = QGroupBox("Active Working Days")
        days_layout = QVBoxLayout(days_group)
        for day in DAYS_OF_WEEK:
            cb = QCheckBox(day)
            self.day_checkboxes[day] = cb
            days_layout.addWidget(cb)
        top_container.addWidget(days_group)

        # 2. Timing Configuration Group
        timing_group = QGroupBox("College Daily Timings & Periods")
        timing_form = QFormLayout(timing_group)

        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm")

        self.spn_period_duration = QSpinBox()
        self.spn_period_duration.setRange(30, 90)
        self.spn_period_duration.setValue(50)
        self.spn_period_duration.setSuffix(" minutes")

        self.spn_periods_per_day = QSpinBox()
        self.spn_periods_per_day.setRange(4, 10)
        self.spn_periods_per_day.setValue(7)
        self.spn_periods_per_day.setSuffix(" teaching periods")

        self.chk_tea_break = QCheckBox("Enable Morning Tea Break")
        self.spn_tea_after = QSpinBox()
        self.spn_tea_after.setRange(1, 4)
        self.spn_tea_after.setValue(3)
        self.spn_tea_after.setPrefix("After Period ")

        self.spn_tea_dur = QSpinBox()
        self.spn_tea_dur.setRange(5, 30)
        self.spn_tea_dur.setValue(15)
        self.spn_tea_dur.setSuffix(" minutes")

        self.spn_lunch_after = QSpinBox()
        self.spn_lunch_after.setRange(2, 6)
        self.spn_lunch_after.setValue(4)
        self.spn_lunch_after.setPrefix("After Period ")

        self.spn_lunch_dur = QSpinBox()
        self.spn_lunch_dur.setRange(30, 90)
        self.spn_lunch_dur.setValue(50)
        self.spn_lunch_dur.setSuffix(" minutes")

        timing_form.addRow("College Starting Time:", self.time_start)
        timing_form.addRow("Period Duration:", self.spn_period_duration)
        timing_form.addRow("Total Teaching Periods/Day:", self.spn_periods_per_day)
        timing_form.addRow("", self.chk_tea_break)
        timing_form.addRow("Tea Break Position:", self.spn_tea_after)
        timing_form.addRow("Tea Break Duration:", self.spn_tea_dur)
        timing_form.addRow("Lunch Break Position:", self.spn_lunch_after)
        timing_form.addRow("Lunch Break Duration:", self.spn_lunch_dur)

        top_container.addWidget(timing_group)
        main_layout.addLayout(top_container)

        # Action bar
        act_bar = QHBoxLayout()
        btn_calc = QPushButton("⚡ Preview / Recalculate Time Slots Schedule")
        btn_calc.setObjectName("btn_primary")
        btn_calc.clicked.connect(self.calculate_and_preview_slots)

        btn_save = QPushButton("💾 Save & Apply Schedule")
        btn_save.clicked.connect(self.save_schedule)

        act_bar.addWidget(btn_calc)
        act_bar.addWidget(btn_save)
        act_bar.addStretch()
        main_layout.addLayout(act_bar)

        # Slots Preview Table
        preview_group = QGroupBox("Generated Daily Time Slots Preview")
        prev_layout = QVBoxLayout(preview_group)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Slot No.", "Slot Name", "Start Time", "End Time", "Type", "Duration"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        prev_layout.addWidget(self.table)
        main_layout.addWidget(preview_group)

    def load_current_settings(self):
        # Load Days
        working_days = self.db.get_working_days()
        for wd in working_days:
            if wd["day_name"] in self.day_checkboxes:
                self.day_checkboxes[wd["day_name"]].setChecked(bool(wd["is_working"]))

        # Load Times
        start_t_str = self.db.get_setting("college_start_time", "09:00")
        parts = start_t_str.split(":")
        self.time_start.setTime(QTime(int(parts[0]), int(parts[1])))

        self.spn_period_duration.setValue(int(self.db.get_setting("period_duration_minutes", "50")))
        self.spn_periods_per_day.setValue(int(self.db.get_setting("periods_per_day", "7")))
        self.chk_tea_break.setChecked(self.db.get_setting("tea_break_enabled", "1") == "1")

        self.load_slots_table()

    def load_slots_table(self):
        slots = self.db.get_all_time_slots()
        self.table.setRowCount(len(slots))
        for row, s in enumerate(slots):
            it0 = QTableWidgetItem(str(s["slot_number"]))
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(s["slot_name"])
            it1.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(s["start_time"])
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(s["end_time"])
            it3.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, it3)

            slot_type = "Break (" + s.get("break_type", "Break") + ")" if s["is_break"] else "Teaching Period"
            it4 = QTableWidgetItem(slot_type)
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            # Duration
            t1 = datetime.strptime(s["start_time"], "%H:%M")
            t2 = datetime.strptime(s["end_time"], "%H:%M")
            dur = int((t2 - t1).total_seconds() / 60)
            it5 = QTableWidgetItem(f"{dur} min")
            it5.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, it5)

    def calculate_and_preview_slots(self):
        """Calculates slots in memory and previews in table."""
        slots = self._build_slots_list()
        self.table.setRowCount(len(slots))
        for row, s in enumerate(slots):
            it0 = QTableWidgetItem(str(s["slot_number"]))
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(s["slot_name"])
            it1.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(s["start_time"])
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(s["end_time"])
            it3.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, it3)

            slot_type = f"Break ({s['break_type']})" if s["is_break"] else "Teaching Period"
            it4 = QTableWidgetItem(slot_type)
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            t1 = datetime.strptime(s["start_time"], "%H:%M")
            t2 = datetime.strptime(s["end_time"], "%H:%M")
            dur = int((t2 - t1).total_seconds() / 60)
            it5 = QTableWidgetItem(f"{dur} min")
            it5.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, it5)

    def _build_slots_list(self):
        qtime = self.time_start.time()
        cur_dt = datetime(2026, 1, 1, qtime.hour(), qtime.minute())
        period_dur = timedelta(minutes=self.spn_period_duration.value())
        tea_dur = timedelta(minutes=self.spn_tea_dur.value())
        lunch_dur = timedelta(minutes=self.spn_lunch_dur.value())

        total_periods = self.spn_periods_per_day.value()
        tea_after = self.spn_tea_after.value()
        lunch_after = self.spn_lunch_after.value()
        has_tea = self.chk_tea_break.isChecked()

        slots = []
        slot_number = 1
        disp_order = 1

        for p in range(1, total_periods + 1):
            # Teaching period
            start_str = cur_dt.strftime("%H:%M")
            cur_dt += period_dur
            end_str = cur_dt.strftime("%H:%M")
            slots.append({
                "slot_number": slot_number,
                "slot_name": f"Period {p}",
                "start_time": start_str,
                "end_time": end_str,
                "is_break": 0,
                "break_type": "",
                "display_order": disp_order
            })
            slot_number += 1
            disp_order += 1

            # Check if tea break after this period
            if has_tea and p == tea_after:
                t_start = cur_dt.strftime("%H:%M")
                cur_dt += tea_dur
                t_end = cur_dt.strftime("%H:%M")
                slots.append({
                    "slot_number": slot_number,
                    "slot_name": "Tea Break",
                    "start_time": t_start,
                    "end_time": t_end,
                    "is_break": 1,
                    "break_type": "Tea",
                    "display_order": disp_order
                })
                slot_number += 1
                disp_order += 1

            # Check if lunch break after this period
            if p == lunch_after:
                l_start = cur_dt.strftime("%H:%M")
                cur_dt += lunch_dur
                l_end = cur_dt.strftime("%H:%M")
                slots.append({
                    "slot_number": slot_number,
                    "slot_name": "Lunch Break",
                    "start_time": l_start,
                    "end_time": l_end,
                    "is_break": 1,
                    "break_type": "Lunch",
                    "display_order": disp_order
                })
                slot_number += 1
                disp_order += 1

        return slots

    def save_schedule(self):
        # 1. Save Working Days
        for day, cb in self.day_checkboxes.items():
            self.db.set_working_day(day, cb.isChecked())

        # 2. Save Timing Settings
        self.db.set_setting("college_start_time", self.time_start.time().toString("HH:mm"))
        self.db.set_setting("period_duration_minutes", str(self.spn_period_duration.value()))
        self.db.set_setting("periods_per_day", str(self.spn_periods_per_day.value()))
        self.db.set_setting("tea_break_enabled", "1" if self.chk_tea_break.isChecked() else "0")

        # 3. Save Slots
        slots = self._build_slots_list()
        self.db.set_time_slots(slots)

        QMessageBox.information(
            self,
            "Settings Saved",
            "Working hours, days, and time slots have been updated and saved to database."
        )
        self.load_slots_table()

