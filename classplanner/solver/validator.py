"""
ClassPlanner - Timetable Conflict Validator
Validates hard and soft scheduling constraints for automated generation and manual editing.
"""

from typing import Dict, List, Any, Optional, Tuple


class ConflictValidator:
    """
    Checks conflict rules for assigning (subject, faculty, classroom) to (section, day, slot).
    """

    @staticmethod
    def validate_assignment(
        timetable_id: int,
        section_id: int,
        day_name: str,
        slot_number: int,
        subject_id: int,
        faculty_id: int,
        classroom_id: int,
        existing_entries: List[Dict[str, Any]],
        section_info: Dict[str, Any],
        faculty_info: Dict[str, Any],
        classroom_info: Dict[str, Any],
        subject_info: Dict[str, Any],
        faculty_availability: Dict[Tuple[str, int], bool],
        current_entry_id: Optional[int] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validates if an entry can be placed at day_name, slot_number.
        Returns:
            (is_valid, hard_conflicts, soft_warnings)
        """
        hard_conflicts = []
        soft_warnings = []

        # 1. Faculty Availability check
        avail = faculty_availability.get((day_name, slot_number), True)
        if not avail:
            hard_conflicts.append(f"Faculty {faculty_info.get('name')} is marked as UNAVAILABLE on {day_name} at Period {slot_number}.")

        # 2. Section strength vs Classroom Capacity
        student_count = section_info.get("student_count", 0)
        room_capacity = classroom_info.get("capacity", 0)
        if room_capacity < student_count:
            hard_conflicts.append(
                f"Classroom capacity ({room_capacity}) is smaller than Section strength ({student_count})."
            )

        # 3. Room Type Match
        requires_lab = bool(subject_info.get("requires_lab", 0)) or subject_info.get("subject_type") == "Practical / Laboratory"
        room_type = classroom_info.get("room_type", "")
        if requires_lab and "Lab" not in room_type:
            hard_conflicts.append(f"Subject '{subject_info.get('name')}' is a laboratory course and requires a Laboratory room.")
        elif not requires_lab and "Lab" in room_type:
            soft_warnings.append(f"Scheduling theory subject '{subject_info.get('name')}' in a Laboratory ({classroom_info.get('room_number')}).")

        # 4. Check collisions with other timetable entries
        faculty_day_hours = 0
        faculty_week_hours = 0
        section_day_subjects = []

        for e in existing_entries:
            if current_entry_id and e.get("id") == current_entry_id:
                continue

            e_day = e["day_name"]
            e_slot = e["slot_number"]
            e_fac = e["faculty_id"]
            e_sec = e["section_id"]
            e_room = e["classroom_id"]
            e_sub = e["subject_id"]

            # Same day and slot collisions:
            if e_day == day_name and e_slot == slot_number:
                # Section double booking
                if e_sec == section_id:
                    hard_conflicts.append(
                        f"Section '{section_info.get('section_name')}' already has '{e.get('subject_name')}' scheduled at {day_name} Period {slot_number}."
                    )
                # Faculty double booking
                if e_fac == faculty_id:
                    hard_conflicts.append(
                        f"Faculty '{faculty_info.get('name')}' is already teaching Section '{e.get('section_name')}' ({e.get('subject_name')}) at {day_name} Period {slot_number}."
                    )
                # Classroom double booking
                if e_room == classroom_id:
                    hard_conflicts.append(
                        f"Classroom '{classroom_info.get('room_number')}' is already occupied by Section '{e.get('section_name')}' at {day_name} Period {slot_number}."
                    )

            # Accumulate workload
            if e_fac == faculty_id:
                faculty_week_hours += 1
                if e_day == day_name:
                    faculty_day_hours += 1

            if e_sec == section_id and e_day == day_name:
                section_day_subjects.append(e_sub)

        # 5. Faculty Max Hours Per Day / Week checks
        max_day = faculty_info.get("max_hours_per_day", 4)
        max_week = faculty_info.get("max_hours_per_week", 18)

        # Include the current proposed period
        if faculty_day_hours + 1 > max_day:
            hard_conflicts.append(
                f"Faculty '{faculty_info.get('name')}' exceeds daily workload limit ({faculty_day_hours + 1}/{max_day} hours on {day_name})."
            )

        if faculty_week_hours + 1 > max_week:
            hard_conflicts.append(
                f"Faculty '{faculty_info.get('name')}' exceeds weekly workload limit ({faculty_week_hours + 1}/{max_week} hours)."
            )

        # 6. Theory subject repetition on the same day warning
        if not requires_lab and subject_id in section_day_subjects:
            soft_warnings.append(
                f"Subject '{subject_info.get('name')}' is already scheduled on {day_name} for this section."
            )

        is_valid = len(hard_conflicts) == 0
        return is_valid, hard_conflicts, soft_warnings

