# streamlit_schedule_maker.py
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from copy import deepcopy

# --------------------- Data models ---------------------
class Teacher:
    def __init__(self, name, notes=''):
        self.name = name
        self.notes = notes

    def to_dict(self):
        return {"name": self.name, "notes": self.notes}

    @staticmethod
    def from_dict(d):
        return Teacher(d['name'], d.get('notes',''))

class ClassGroup:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"name": self.name}

    @staticmethod
    def from_dict(d):
        return ClassGroup(d['name'])

class Period:
    def __init__(self, label, start_time, end_time, is_break=False):
        self.label = label
        self.start_time = start_time
        self.end_time = end_time
        self.is_break = is_break

    def to_dict(self):
        return {
            "label": self.label,
            "start": self.start_time,
            "end": self.end_time,
            "is_break": self.is_break
        }

    @staticmethod
    def from_dict(d):
        return Period(d['label'], d['start'], d['end'], d.get('is_break', False))

class ScheduleProject:
    """
    periods_by_day: dict day_name -> list[Period]
    timetable keys are "DayName|period_index|class_index" -> {"subject":..., "teacher":...}
    """
    def __init__(self):
        self.teachers = []
        self.class_groups = []
        self.periods_by_day = {}   # day -> [Period,...]
        self.timetable = {}

    def to_dict(self):
        return {
            "teachers": [t.to_dict() for t in self.teachers],
            "class_groups": [c.to_dict() for c in self.class_groups],
            "periods_by_day": {
                day: [p.to_dict() for p in plist] for day, plist in self.periods_by_day.items()
            },
            "days": list(self.periods_by_day.keys()),
            "timetable": self.timetable
        }

    @staticmethod
    def from_dict(d):
        p = ScheduleProject()
        p.teachers = [Teacher.from_dict(x) for x in d.get('teachers', [])]
        p.class_groups = [ClassGroup.from_dict(x) for x in d.get('class_groups', [])]

        # prefer new structure 'periods_by_day'
        if d.get('periods_by_day'):
            p.periods_by_day = {
                day: [Period.from_dict(x) for x in plist]
                for day, plist in d['periods_by_day'].items()
            }
        else:
            # backward compatibility: single 'periods' used for all days
            days = d.get('days') or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            common = [Period.from_dict(x) for x in d.get('periods', [])]
            for day in days:
                p.periods_by_day[day] = [Period(pp.label, pp.start_time, pp.end_time, pp.is_break) for pp in common]

        p.timetable = d.get('timetable', {})
        return p

# --------------------- Helpers ---------------------
def copy_periods(periods):
    return [Period(p.label, p.start_time, p.end_time, p.is_break) for p in periods]

def remove_period_for_day(proj: ScheduleProject, day: str, idx: int):
    """Remove a period at index idx for day and shift timetable indices for that day."""
    new_tt = {}
    for k, v in proj.timetable.items():
        parts = k.split('|')
        if len(parts) != 3:
            new_tt[k] = v
            continue
        kday, pidx, cidx = parts
        if kday != day:
            new_tt[k] = v
            continue
        pidx = int(pidx)
        if pidx == idx:
            # drop this entry
            continue
        if pidx > idx:
            newk = f"{kday}|{pidx-1}|{cidx}"
        else:
            newk = k
        new_tt[newk] = v
    proj.timetable = new_tt
    # remove period from list
    proj.periods_by_day[day].pop(idx)

def move_period_for_day(proj: ScheduleProject, day: str, idx: int, newidx: int):
    """Swap two periods for a day and remap timetable pidx accordingly (swap pidx idx <-> newidx)."""
    periods = proj.periods_by_day[day]
    periods[idx], periods[newidx] = periods[newidx], periods[idx]
    # remap timetable keys for that day: swap pidx idx and newidx
    tt = {}
    for k, v in proj.timetable.items():
        parts = k.split('|')
        if len(parts) != 3:
            tt[k] = v
            continue
        kday, pidx, cidx = parts
        if kday != day:
            tt[k] = v
            continue
        pidx = int(pidx)
        if pidx == idx:
            pidx = newidx
        elif pidx == newidx:
            pidx = idx
        tt[f"{kday}|{pidx}|{cidx}"] = v
    proj.timetable = tt

def remove_class_global(proj: ScheduleProject, class_idx: int):
    """Remove a class group and shift class indices in timetable across all days."""
    new_tt = {}
    for k, v in proj.timetable.items():
        parts = k.split('|')
        if len(parts) != 3:
            new_tt[k] = v
            continue
        kday, pidx, cidx = parts
        cidx = int(cidx)
        if cidx == class_idx:
            continue
        if cidx > class_idx:
            newk = f"{kday}|{pidx}|{cidx-1}"
        else:
            newk = k
        new_tt[newk] = v
    proj.timetable = new_tt
    proj.class_groups.pop(class_idx)

# --------------------- Streamlit UI ---------------------
st.set_page_config(page_title="School Schedule Maker", layout="wide")

# default days & default periods to populate new days
DEFAULT_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DEFAULT_PERIODS = [
    Period('P1', '08:00', '08:45'),
    Period('P2', '08:50', '09:35'),
    Period('P3', '09:50', '10:35'),
    Period('Break', '10:35', '10:50', is_break=True),
    Period('P4', '10:50', '11:35'),
    Period('P5', '11:40', '12:25'),
]

# initialize session state
if "project" not in st.session_state:
    proj = ScheduleProject()
    # initialize days list
    st.session_state.days = DEFAULT_DAYS.copy()
    # create per-day periods as copies of default
    for day in st.session_state.days:
        proj.periods_by_day[day] = copy_periods(DEFAULT_PERIODS)
    st.session_state.project = proj

if "days" not in st.session_state:
    st.session_state.days = DEFAULT_DAYS.copy()

proj: ScheduleProject = st.session_state.project

st.title("📅 School Schedule Maker — per-day periods")

# ---------------- Sidebar: manage days, teachers, classes, periods ----------------
st.sidebar.header("Manage")

# Days editor
with st.sidebar.expander("Days of Week", expanded=True):
    new_day = st.text_input("Add Day (unique name)", key="new_day_input")
    if st.button("Add Day"):
        day = (new_day or "").strip()
        if not day:
            st.warning("Day name cannot be empty")
        elif day in st.session_state.days:
            st.warning("Day already exists")
        else:
            st.session_state.days.append(day)
            # give it a copy of default periods
            proj.periods_by_day[day] = copy_periods(DEFAULT_PERIODS)
            st.rerun()

    st.write("Existing days:")
    for i, day in enumerate(list(st.session_state.days)):
        cols = st.columns([3, 1, 1])
        cols[0].write(day)
        if cols[1].button("Rename", key=f"rename_day_{i}"):
            # simple inline rename prompt via session_state flag
            st.session_state[f"rename_target_{i}"] = day
            st.rerun()
        if cols[2].button("❌", key=f"del_day_{i}"):
            # remove day and its periods and timetable entries
            removed = st.session_state.days.pop(i)
            if removed in proj.periods_by_day:
                del proj.periods_by_day[removed]
            # remove all timetable entries for that day
            proj.timetable = {k: v for k, v in proj.timetable.items() if not k.startswith(f"{removed}|")}
            st.rerun()

    # handle renames (one at a time)
    for i in range(len(st.session_state.days)+1):
        key = f"rename_target_{i}"
        if key in st.session_state:
            old = st.session_state[key]
            newname = st.text_input(f"Rename '{old}' to:", key=f"rename_input_{i}")
            if st.button("Save Rename", key=f"save_rename_{i}"):
                newname = (newname or "").strip()
                if not newname:
                    st.warning("Name cannot be empty")
                elif newname in st.session_state.days and newname != old:
                    st.warning("A day with that name already exists")
                else:
                    # change days list order-preserving
                    idx = st.session_state.days.index(old)
                    st.session_state.days[idx] = newname
                    # move periods_by_day
                    proj.periods_by_day[newname] = proj.periods_by_day.pop(old, [])
                    # update timetable keys: replace starting day name
                    new_tt = {}
                    for k, v in proj.timetable.items():
                        parts = k.split('|')
                        if parts[0] == old:
                            newk = f"{newname}|{parts[1]}|{parts[2]}"
                        else:
                            newk = k
                        new_tt[newk] = v
                    proj.timetable = new_tt
                    del st.session_state[key]
                    st.rerun()
            if st.button("Cancel Rename", key=f"cancel_rename_{i}"):
                del st.session_state[key]
                st.rerun()

# Teachers
with st.sidebar.expander("Teachers"):
    t_name = st.text_input("Add teacher name", key="add_teacher_name")
    t_notes = st.text_input("Notes", key="add_teacher_notes")
    if st.button("Add Teacher"):
        if t_name and t_name.strip():
            proj.teachers.append(Teacher(t_name.strip(), (t_notes or "").strip()))
            st.rerun()
        else:
            st.warning("Teacher name required")
    st.markdown("---")
    for i, t in enumerate(proj.teachers):
        cols = st.columns([3, 1])
        cols[0].write(f"{t.name} — {t.notes}")
        if cols[1].button("Remove", key=f"remove_teacher_{i}"):
            proj.teachers.pop(i)
            st.rerun()

# Class groups
with st.sidebar.expander("Class groups"):
    c_name = st.text_input("Add class group (e.g. 10A)", key="add_class_name")
    if st.button("Add Class"):
        if c_name and c_name.strip():
            proj.class_groups.append(ClassGroup(c_name.strip()))
            st.rerun()
        else:
            st.warning("Class name required")
    st.markdown("---")
    for i, c in enumerate(proj.class_groups):
        cols = st.columns([3, 1])
        cols[0].write(c.name)
        if cols[1].button("Remove", key=f"remove_class_{i}"):
            remove_class_global(proj, i)
            st.rerun()

# Periods per-day editor
with st.sidebar.expander("Periods (edit per-day)"):
    if not st.session_state.days:
        st.info("Add at least one day first")
    else:
        day_sel = st.selectbox("Select day to edit", st.session_state.days, key="periods_day_select")
        periods = proj.periods_by_day.get(day_sel, [])
        # list existing periods with expanders for edit
        for i, p in enumerate(list(periods)):
            exp = st.expander(f"{i+1}. {p.label} ({p.start_time}-{p.end_time}) {'[BREAK]' if p.is_break else ''}", expanded=False)
            with exp:
                new_label = st.text_input("Label", value=p.label, key=f"period_label_{day_sel}_{i}")
                new_start = st.text_input("Start (HH:MM)", value=p.start_time, key=f"period_start_{day_sel}_{i}")
                new_end = st.text_input("End (HH:MM)", value=p.end_time, key=f"period_end_{day_sel}_{i}")
                new_break = st.checkbox("Mark as break", value=p.is_break, key=f"period_break_{day_sel}_{i}")
                bcol1, bcol2, bcol3 = st.columns([1,1,1])
                if bcol1.button("Save", key=f"save_period_{day_sel}_{i}"):
                    try:
                        datetime.strptime(new_start.strip(), "%H:%M")
                        datetime.strptime(new_end.strip(), "%H:%M")
                    except Exception:
                        st.error("Time must be HH:MM")
                    else:
                        proj.periods_by_day[day_sel][i] = Period(new_label.strip() or p.label, new_start.strip(), new_end.strip(), new_break)
                        st.rerun()

                if bcol2.button("Move Up", key=f"moveperiod_up_{day_sel}_{i}") and i > 0:
                    move_period_for_day(proj, day_sel, i, i-1)
                    st.rerun()
                if bcol3.button("Move Down", key=f"moveperiod_down_{day_sel}_{i}") and i < len(periods)-1:
                    move_period_for_day(proj, day_sel, i, i+1)
                    st.rerun()

                if st.button("Remove period", key=f"remove_period_{day_sel}_{i}"):
                    remove_period_for_day(proj, day_sel, i)
                    st.rerun()

        st.markdown("---")
        st.write("Add new period to", day_sel)
        add_label = st.text_input("Label", key=f"add_period_label_{day_sel}")
        add_start = st.text_input("Start (HH:MM)", value="08:00", key=f"add_period_start_{day_sel}")
        add_end = st.text_input("End (HH:MM)", value="08:45", key=f"add_period_end_{day_sel}")
        add_break = st.checkbox("Break", value=False, key=f"add_period_break_{day_sel}")
        if st.button("Add Period", key=f"add_period_btn_{day_sel}"):
            try:
                datetime.strptime(add_start.strip(), "%H:%M")
                datetime.strptime(add_end.strip(), "%H:%M")
            except Exception:
                st.error("Time must be HH:MM")
            else:
                proj.periods_by_day.setdefault(day_sel, []).append(Period(add_label.strip() or "P", add_start.strip(), add_end.strip(), add_break))
                st.rerun()

# ---------------- Main area: schedule grid ----------------
st.subheader("Schedule grid (per-day periods)")

if not proj.class_groups:
    st.info("Add class groups in the sidebar to start building a timetable.")
else:
    for day in st.session_state.days:
        periods = proj.periods_by_day.get(day, [])
        st.markdown(f"### {day}")
        if not periods:
            st.write("No periods defined for this day.")
            continue

        for p_idx, p in enumerate(periods):
            cols = st.columns(len(proj.class_groups) + 1)
            left = cols[0]
            left.markdown(f"**{p.label}**  \n{p.start_time} — {p.end_time}  " + ("  \n**BREAK**" if p.is_break else ""))
            for c_idx, cls in enumerate(proj.class_groups):
                key = f"{day}|{p_idx}|{c_idx}"
                existing = proj.timetable.get(key, {})
                subj_key = f"subj_{day}_{p_idx}_{c_idx}"
                teach_key = f"teach_{day}_{p_idx}_{c_idx}"

                subj = cols[c_idx+1].text_input(f"{cls.name} subject", value=existing.get('subject', ''), key=subj_key)
                teacher_options = [""] + [t.name for t in proj.teachers]
                current_teacher = existing.get('teacher', '')
                if current_teacher in teacher_options:
                    index = teacher_options.index(current_teacher)
                else:
                    index = 0
                teacher = cols[c_idx+1].selectbox("Teacher", options=teacher_options, index=index, key=teach_key)

                # store assignment
                if subj.strip() or teacher.strip():
                    proj.timetable[key] = {"subject": subj.strip(), "teacher": teacher.strip()}
                else:
                    # if both blank, remove entry if exists
                    if key in proj.timetable:
                        del proj.timetable[key]

# ---------------- Save / Load / Export ----------------
st.subheader("Save / Load / Export")

save_json = json.dumps(proj.to_dict(), indent=2, ensure_ascii=False)
st.download_button("💾 Save JSON", save_json, file_name="schedule.json", mime="application/json")

uploaded = st.file_uploader("Load JSON Project", type="json")
if uploaded:
    try:
        data = json.load(uploaded)
        new_proj = ScheduleProject.from_dict(data)
        # update session state
        st.session_state.project = new_proj
        st.session_state.days = list(new_proj.periods_by_day.keys()) or st.session_state.days
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load: {e}")

if st.button("📤 Export CSV"):
    rows = []
    for day in st.session_state.days:
        periods = proj.periods_by_day.get(day, [])
        for p_idx, p in enumerate(periods):
            for c_idx, cls in enumerate(proj.class_groups):
                key = f"{day}|{p_idx}|{c_idx}"
                entry = proj.timetable.get(key, {})
                rows.append([day, p.label, p.start_time, p.end_time, cls.name, entry.get('subject', ''), entry.get('teacher', '')])
    df = pd.DataFrame(rows, columns=["Day", "Period", "Start", "End", "Class", "Subject", "Teacher"])
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name="schedule.csv", mime="text/csv")
