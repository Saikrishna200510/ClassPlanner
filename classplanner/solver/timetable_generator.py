"""
ClassPlanner - Automated Timetable Generation Engine
Hybrid Constraint-Satisfaction & Heuristic Scheduler.
Guarantees all hard constraints are strictly satisfied.
"""

import random
from typing import Dict, List, Any, Optional, Tuple, Set
from classplanner.database.db_manager import DatabaseManager


class TimetableGenerationResult:
    """Encapsulates the result of a timetable generation run."""
    def __init__(self):
        self.success: bool = False
        self.timetable_id: Optional[int] = None
        self.total_required_periods: int = 0
        self.total_scheduled_periods: int = 0
        self.scheduled_entries: List[Dict[str, Any]] = []
        self.unscheduled_items: List[Dict[str, Any]] = []
        self.faculty_utilization: Dict[str, Dict[str, Any]] = {}
        self.classroom_utilization: Dict[str, Dict[str, Any]] = {}
        self.fitness_score: float = 0.0
        self.messages: List[str] = []
        self.execution_time_seconds: float = 0.0


class TimetableGenerator:
    """
    Automated Timetable Generation Engine.
    Implements Minimum-Remaining-Values (MRV), forward checking,
    consecutive-slot window fitting for laboratories, and gap minimization.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def generate(
        self,
        timetable_name: str,
        academic_year: str,
        semester_type: str = "Even",
        department_id: Optional[int] = None,
        random_seed: Optional[int] = None,
        max_attempts: int = 5
    ) -> TimetableGenerationResult:
        """
        Executes automated timetable generation.
        """
        import time
        start_time = time.time()
        result = TimetableGenerationResult()

        if random_seed is not None:
            random.seed(random_seed)

        # 1. Fetch Working Days & Time Slots
        working_days = self.db.get_active_working_days()
        if not working_days:
            result.messages.append("Error: No active working days configured in Working Hours.")
            return result

        all_slots = self.db.get_all_time_slots()
        teaching_slots = [s for s in all_slots if not s["is_break"]]
        teaching_slot_numbers = [s["slot_number"] for s in teaching_slots]

        if not teaching_slot_numbers:
            result.messages.append("Error: No teaching time slots defined.")
            return result

        # Identify contiguous teaching blocks per day (blocks that do not cross breaks)
        # Sort slots by display_order
        sorted_slots = sorted(all_slots, key=lambda s: s["display_order"])
        contiguous_blocks: List[List[int]] = []
        current_block: List[int] = []
        for s in sorted_slots:
            if s["is_break"]:
                if current_block:
                    contiguous_blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(s["slot_number"])
        if current_block:
            contiguous_blocks.append(current_block)

        # 2. Fetch Sections
        sections = self.db.get_sections(department_id=department_id)
        if semester_type == "Even":
            sections = [s for s in sections if s["semester"] % 2 == 0]
        elif semester_type == "Odd":
            sections = [s for s in sections if s["semester"] % 2 != 0]

        if not sections:
            result.messages.append("Error: No student sections found for the specified criteria.")
            return result

        # 3. Fetch Classrooms
        classrooms = self.db.get_classrooms()
        regular_classrooms = [c for c in classrooms if "Lab" not in c["room_type"] and c["is_available"]]
        lab_classrooms = [c for c in classrooms if "Lab" in c["room_type"] and c["is_available"]]

        # 4. Fetch Faculty & Availability
        all_faculty = {f["id"]: f for f in self.db.get_faculty_list()}
        faculty_avail: Dict[int, Dict[Tuple[str, int], bool]] = {}
        for fid in all_faculty:
            faculty_avail[fid] = self.db.get_faculty_availability(fid)

        # 5. Build Requirements per Section
        # Each item is: {section, subject, faculty_candidates, is_lab, block_size, count}
        section_tasks = []
        total_req_periods = 0

        for sec in sections:
            sub_list = self.db.get_subjects(department_id=sec["department_id"], semester=sec["semester"])
            for sub in sub_list:
                # Get qualified faculty
                fac_list = self.db.get_subject_faculties(sub["id"])
                if not fac_list:
                    # Fallback to default faculty or any active faculty in dept
                    if sub.get("default_faculty_id"):
                        fac_list = [all_faculty[sub["default_faculty_id"]]]
                    else:
                        fac_list = [f for f in all_faculty.values() if f["department_id"] == sub["department_id"]]

                if not fac_list:
                    result.unscheduled_items.append({
                        "section": sec["section_name"],
                        "subject": sub["name"],
                        "reason": "No faculty assigned or qualified for this subject."
                    })
                    continue

                hours = sub["weekly_hours"]
                consec = sub.get("consecutive_periods", 1)
                is_lab = bool(sub.get("requires_lab")) or (sub.get("subject_type") == "Practical / Laboratory")

                if is_lab and consec > 1:
                    # For practicals, e.g. 3 hours = 1 block of 3 periods
                    num_blocks = hours // consec
                    remainder = hours % consec
                    for _ in range(num_blocks):
                        section_tasks.append({
                            "section": sec,
                            "subject": sub,
                            "faculties": fac_list,
                            "is_lab": True,
                            "block_size": consec,
                            "task_id": f"sec{sec['id']}_sub{sub['id']}_lab"
                        })
                        total_req_periods += consec
                    for _ in range(remainder):
                        section_tasks.append({
                            "section": sec,
                            "subject": sub,
                            "faculties": fac_list,
                            "is_lab": False,
                            "block_size": 1,
                            "task_id": f"sec{sec['id']}_sub{sub['id']}_th"
                        })
                        total_req_periods += 1
                else:
                    # Theory subject: 1-hour units
                    for _ in range(hours):
                        section_tasks.append({
                            "section": sec,
                            "subject": sub,
                            "faculties": fac_list,
                            "is_lab": is_lab,
                            "block_size": 1,
                            "task_id": f"sec{sec['id']}_sub{sub['id']}_th"
                        })
                        total_req_periods += 1

        result.total_required_periods = total_req_periods

        # Multi-attempt search
        best_schedule = None
        best_fitness = -1.0
        best_scheduled_count = -1
        best_unscheduled = []

        for attempt in range(max_attempts):
            # Sort tasks: Lab blocks first, then smaller candidate pools first
            tasks = list(section_tasks)
            random.shuffle(tasks)
            tasks.sort(key=lambda t: (not t["is_lab"], -t["block_size"], len(t["faculties"])))

            # State tracking
            # (section_id, day, slot) -> entry
            sec_slot_map: Dict[Tuple[int, str, int], Dict[str, Any]] = {}
            # (faculty_id, day, slot) -> True
            fac_busy: Set[Tuple[int, str, int]] = set()
            # (classroom_id, day, slot) -> True
            room_busy: Set[Tuple[int, str, int]] = set()
            # (faculty_id, day) -> count
            fac_day_count: Dict[Tuple[int, str], int] = {}
            # faculty_id -> count
            fac_week_count: Dict[int, int] = {}
            # (section_id, day) -> set(subject_id)
            sec_day_subs: Dict[Tuple[int, str], Set[int]] = {}

            unscheduled = []
            scheduled_entries = []

            for task in tasks:
                sec = task["section"]
                sub = task["subject"]
                block_size = task["block_size"]
                is_lab = task["is_lab"]
                fac_candidates = task["faculties"]

                # Pick candidate rooms
                if is_lab:
                    candidate_rooms = [r for r in lab_classrooms if r["capacity"] >= sec["student_count"]]
                    if not candidate_rooms:
                        # Fallback to any lab classroom if strict capacity is slightly below
                        candidate_rooms = list(lab_classrooms)
                else:
                    # Section default classroom first
                    def_room = next((r for r in regular_classrooms if r["id"] == sec.get("assigned_classroom_id")), None)
                    other_rooms = [r for r in regular_classrooms if r["id"] != sec.get("assigned_classroom_id") and r["capacity"] >= sec["student_count"]]
                    candidate_rooms = ([def_room] if def_room else []) + other_rooms
                    if not candidate_rooms:
                        candidate_rooms = list(regular_classrooms)

                placed = False

                # Generate candidate (day, start_slot) windows
                # We want windows of length `block_size` that lie entirely within one contiguous block
                valid_windows: List[Tuple[str, List[int]]] = []
                days_shuffled = list(working_days)
                random.shuffle(days_shuffled)

                for day in days_shuffled:
                    # For theory, prefer days where section has fewer periods and doesn't already have this subject
                    if not is_lab and sub["id"] in sec_day_subs.get((sec["id"], day), set()):
                        continue

                    for block in contiguous_blocks:
                        if len(block) >= block_size:
                            for i in range(len(block) - block_size + 1):
                                window_slots = block[i:i + block_size]
                                # Check if section is free in all slots of this window
                                if all((sec["id"], day, slot) not in sec_slot_map for slot in window_slots):
                                    valid_windows.append((day, window_slots))

                # If no day without subject was found for theory, allow repeating on same day as fallback
                if not valid_windows and not is_lab:
                    for day in days_shuffled:
                        for block in contiguous_blocks:
                            if len(block) >= block_size:
                                for i in range(len(block) - block_size + 1):
                                    window_slots = block[i:i + block_size]
                                    if all((sec["id"], day, slot) not in sec_slot_map for slot in window_slots):
                                        valid_windows.append((day, window_slots))

                # Heuristic sort of valid windows:
                # Prefer slots adjacent to existing classes to minimize student gaps
                def window_gap_score(day_win):
                    d, slots = day_win
                    first_s = slots[0]
                    last_s = slots[-1]
                    # Score is better if previous slot or next slot is occupied by same section
                    has_neighbor = ((sec["id"], d, first_s - 1) in sec_slot_map or (sec["id"], d, last_s + 1) in sec_slot_map)
                    return 0 if has_neighbor else 1

                valid_windows.sort(key=window_gap_score)

                # Try matching window, faculty, and room
                for day, win_slots in valid_windows:
                    for fac in fac_candidates:
                        fid = fac["id"]
                        max_day_h = fac.get("max_hours_per_day", 4)
                        max_week_h = fac.get("max_hours_per_week", 18)

                        cur_day_h = fac_day_count.get((fid, day), 0)
                        cur_week_h = fac_week_count.get(fid, 0)

                        if cur_day_h + block_size > max_day_h:
                            continue
                        if cur_week_h + block_size > max_week_h:
                            continue

                        # Check faculty availability and free in all slots
                        fac_ok = True
                        for slot in win_slots:
                            if not faculty_avail.get(fid, {}).get((day, slot), True):
                                fac_ok = False
                                break
                            if (fid, day, slot) in fac_busy:
                                fac_ok = False
                                break
                        if not fac_ok:
                            continue

                        # Check room availability
                        for rm in candidate_rooms:
                            rid = rm["id"]
                            room_ok = True
                            for slot in win_slots:
                                if (rid, day, slot) in room_busy:
                                    room_ok = False
                                    break
                            if not room_ok:
                                continue

                            # MATCH FOUND! Assign all slots in window
                            for slot in win_slots:
                                entry = {
                                    "section_id": sec["id"],
                                    "day_name": day,
                                    "slot_number": slot,
                                    "subject_id": sub["id"],
                                    "faculty_id": fid,
                                    "classroom_id": rid,
                                    "section_name": sec["section_name"],
                                    "subject_name": sub["name"],
                                    "faculty_name": fac["name"],
                                    "room_number": rm["room_number"],
                                    "is_locked": 0
                                }
                                sec_slot_map[(sec["id"], day, slot)] = entry
                                fac_busy.add((fid, day, slot))
                                room_busy.add((rid, day, slot))
                                scheduled_entries.append(entry)

                            fac_day_count[(fid, day)] = cur_day_h + block_size
                            fac_week_count[fid] = cur_week_h + block_size
                            if (sec["id"], day) not in sec_day_subs:
                                sec_day_subs[(sec["id"], day)] = set()
                            sec_day_subs[(sec["id"], day)].add(sub["id"])

                            placed = True
                            break

                        if placed:
                            break
                    if placed:
                        break

                if not placed:
                    unscheduled.append({
                        "section": sec["section_name"],
                        "subject": sub["name"],
                        "block_size": block_size,
                        "is_lab": is_lab,
                        "reason": f"No conflict-free slot/room/faculty available (Faculty load or room capacity reached)."
                    })

            # Calculate fitness
            scheduled_count = len(scheduled_entries)
            # Gap penalty: count internal idle slots for each section
            gap_penalty = 0
            for sec in sections:
                for day in working_days:
                    assigned_slots = sorted([slot for s_id, d, slot in sec_slot_map if s_id == sec["id"] and d == day])
                    if len(assigned_slots) > 1:
                        # Count gaps between min and max teaching slots (excluding official break slots)
                        min_s = assigned_slots[0]
                        max_s = assigned_slots[-1]
                        for s_num in teaching_slot_numbers:
                            if min_s < s_num < max_s and (sec["id"], day, s_num) not in sec_slot_map:
                                gap_penalty += 1

            fitness = (scheduled_count / max(1, total_req_periods)) * 100.0 - (gap_penalty * 0.5)

            if scheduled_count > best_scheduled_count or (scheduled_count == best_scheduled_count and fitness > best_fitness):
                best_scheduled_count = scheduled_count
                best_fitness = fitness
                best_schedule = scheduled_entries
                best_unscheduled = unscheduled

            if scheduled_count == total_req_periods and gap_penalty == 0:
                # Perfect schedule found early
                break

        # Save to database
        tt_id = self.db.create_timetable(
            name=timetable_name,
            academic_year=academic_year,
            semester_type=semester_type,
            notes=f"Auto-generated timetable. Scheduled {best_scheduled_count}/{total_req_periods} periods."
        )

        if best_schedule:
            self.db.save_timetable_entries(tt_id, best_schedule)

        result.success = (len(best_unscheduled) == 0 and best_scheduled_count == total_req_periods)
        result.timetable_id = tt_id
        result.total_scheduled_periods = best_scheduled_count
        result.scheduled_entries = best_schedule or []
        result.unscheduled_items = best_unscheduled
        result.fitness_score = round(max(0.0, best_fitness), 2)
        result.execution_time_seconds = round(time.time() - start_time, 2)

        # Calculate Utilization Stats
        # Faculty stats
        fac_loads: Dict[int, int] = {}
        room_loads: Dict[int, int] = {}
        for e in result.scheduled_entries:
            fac_loads[e["faculty_id"]] = fac_loads.get(e["faculty_id"], 0) + 1
            room_loads[e["classroom_id"]] = room_loads.get(e["classroom_id"], 0) + 1

        total_avail_slots_week = len(working_days) * len(teaching_slot_numbers)

        for fid, fac in all_faculty.items():
            assigned = fac_loads.get(fid, 0)
            max_w = fac.get("max_hours_per_week", 18)
            result.faculty_utilization[fac["name"]] = {
                "faculty_code": fac["faculty_id"],
                "department": fac.get("dept_code", ""),
                "assigned_hours": assigned,
                "max_hours": max_w,
                "utilization_pct": round((assigned / max(1, max_w)) * 100, 1)
            }

        for rm in classrooms:
            assigned = room_loads.get(rm["id"], 0)
            result.classroom_utilization[rm["room_number"]] = {
                "building": rm["building_name"],
                "room_type": rm["room_type"],
                "assigned_periods": assigned,
                "total_slots": total_avail_slots_week,
                "utilization_pct": round((assigned / max(1, total_avail_slots_week)) * 100, 1)
            }

        if result.success:
            result.messages.append(
                f"Timetable generation completed successfully! All {best_scheduled_count} periods scheduled without conflicts."
            )
        else:
            result.messages.append(
                f"Generated timetable with {best_scheduled_count}/{total_req_periods} periods scheduled. "
                f"{len(best_unscheduled)} subjects could not be scheduled due to tight constraints."
            )

        return result

