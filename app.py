import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from notifications import SERVICES

BASE_DIR = Path(__file__).resolve().parent
GRADES_FILE = BASE_DIR / "grades.txt"
STUDENTS_FILE = BASE_DIR / "students.json"

BG = "#F5F7FB"
CARD = "#FFFFFF"
SIDEBAR = "#172033"
SIDEBAR_TEXT = "#D7DCE7"
SIDEBAR_MUTED = "#8F9AAF"
PRIMARY = "#3157D5"
PRIMARY_HOVER = "#2749BC"
TEXT = "#182033"
MUTED = "#6F7A8F"
BORDER = "#E3E7EF"
SOFT = "#EEF2FF"
DANGER = "#C94343"
FONT = "Segoe UI"


def parse_grades():
    if not GRADES_FILE.exists():
        raise FileNotFoundError(f"grades.txt was not found at: {GRADES_FILE}")
    lines = [line.strip() for line in GRADES_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError("grades.txt is empty.")
    student_info = lines[0]
    grades = []
    for line in lines[1:]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            grades.append(tuple(parts))
        elif len(parts) == 3:
            code, subject_with_units, grade = parts
            tokens = subject_with_units.rsplit(maxsplit=1)
            if len(tokens) == 2 and tokens[1].replace(".", "", 1).isdigit():
                subject, units = tokens
            else:
                subject, units = subject_with_units, "-"
            grades.append((code, subject, units, grade))
        else:
            raise ValueError(f"Invalid grade entry in grades.txt: {line}")
    return student_info, grades


def save_grades(student_info, grades):
    lines = [student_info]
    lines.extend(f"{code}, {subject}, {units}, {grade}" for code, subject, units, grade in grades)
    GRADES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def calculate_totals(grades):
    total_units = 0.0
    weighted_points = 0.0
    for _code, _subject, units, grade in grades:
        try:
            unit_value = float(units)
            grade_value = float(grade)
        except (TypeError, ValueError):
            continue
        total_units += unit_value
        weighted_points += unit_value * grade_value
    weighted_average = weighted_points / total_units if total_units else None
    return total_units, weighted_average


def load_grades() -> str:
    student_info, grades = parse_grades()
    rows = [f"{code} - {subject}: {grade} (Units: {units})" for code, subject, units, grade in grades]
    total_units, weighted_average = calculate_totals(grades)
    average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"
    return "Student: " + student_info + "\n\nGrades:\n" + "\n".join(rows) + f"\n\nTotal Units: {total_units:g}\nWeighted Average: {average_text}"


def save_students(students):
    STUDENTS_FILE.write_text(json.dumps(students, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_students():
    if not STUDENTS_FILE.exists():
        try:
            student_info, grades = parse_grades()
        except (FileNotFoundError, ValueError):
            students = []
        else:
            parts = [part.strip() for part in student_info.split(",", 1)]
            students = [{
                "name": parts[0] if parts else student_info,
                "program_year": parts[1] if len(parts) > 1 else "",
                "academic_period": "",
                "grades": [list(row) for row in grades],
            }]
        save_students(students)
        return students
    try:
        data = json.loads(STUDENTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"students.json contains invalid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("students.json must contain a list of students.")
    return data


class ModernDialog(tk.Toplevel):
    def __init__(self, parent, title, subtitle):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=CARD, padx=24, pady=20)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(header, text=title, font=(FONT, 16, "bold"), fg=TEXT, bg=CARD).pack(anchor="w")
        tk.Label(header, text=subtitle, font=(FONT, 9), fg=MUTED, bg=CARD).pack(anchor="w", pady=(4, 0))

        self.body = tk.Frame(self, bg=BG, padx=24, pady=20)
        self.body.grid(row=1, column=0, sticky="ew")

        self.buttons = tk.Frame(self, bg=CARD, padx=24, pady=16)
        self.buttons.grid(row=2, column=0, sticky="ew")
        tk.Button(self.buttons, text="Cancel", command=self.destroy, font=(FONT, 9, "bold"), bg="#F0F2F6", fg=TEXT, activebackground="#E5E8EE", relief="flat", bd=0, padx=18, pady=9, cursor="hand2").pack(side="right")
        self.save_button = tk.Button(self.buttons, text="Save Changes", font=(FONT, 9, "bold"), bg=PRIMARY, fg="white", activebackground=PRIMARY_HOVER, activeforeground="white", relief="flat", bd=0, padx=20, pady=9, cursor="hand2")
        self.save_button.pack(side="right", padx=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda _event: self.destroy())

    def field(self, row, label, variable, width=42):
        tk.Label(self.body, text=label, font=(FONT, 9, "bold"), fg=TEXT, bg=BG).grid(row=row, column=0, sticky="w", pady=(0, 6))
        entry = tk.Entry(self.body, textvariable=variable, font=(FONT, 10), width=width, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY)
        entry.grid(row=row + 1, column=0, sticky="ew", ipady=8, pady=(0, 14))
        return entry


class StudentDialog(ModernDialog):
    def __init__(self, parent, values=None):
        super().__init__(parent, "Student Information", "Add a student or update their academic information.")
        values = values or ("", "", "")
        self.result = None
        self.name_var = tk.StringVar(value=values[0])
        self.program_var = tk.StringVar(value=values[1])
        self.period_var = tk.StringVar(value=values[2])
        self.name_entry = self.field(0, "Student Name", self.name_var)
        self.field(2, "Program / Year", self.program_var)
        self.field(4, "Academic Period", self.period_var)
        self.save_button.configure(command=self.validate_and_save)
        self.after(50, self.name_entry.focus_set)

    def validate_and_save(self):
        name = self.name_var.get().strip()
        program = self.program_var.get().strip()
        period = self.period_var.get().strip()
        if not name or not program:
            messagebox.showwarning("Missing information", "Student Name and Program / Year are required.", parent=self)
            return
        self.result = (name, program, period)
        self.destroy()


class GradeDialog(ModernDialog):
    def __init__(self, parent, values=None):
        super().__init__(parent, "Subject & Grade", "Enter the course information and final grade.")
        values = values or ("", "", "", "")
        self.result = None
        self.code_var = tk.StringVar(value=values[0])
        self.subject_var = tk.StringVar(value=values[1])
        self.units_var = tk.StringVar(value=values[2])
        self.grade_var = tk.StringVar(value=values[3])
        self.code_entry = self.field(0, "Course Code", self.code_var)
        self.field(2, "Course Title", self.subject_var)
        self.field(4, "Units", self.units_var)
        self.field(6, "Grade", self.grade_var)
        self.save_button.configure(command=self.validate_and_save)
        self.after(50, self.code_entry.focus_set)

    def validate_and_save(self):
        code = self.code_var.get().strip()
        subject = self.subject_var.get().strip()
        units = self.units_var.get().strip()
        grade = self.grade_var.get().strip()
        if not code or not subject or not units or not grade:
            messagebox.showwarning("Missing information", "Complete all four fields.", parent=self)
            return
        try:
            unit_value = float(units)
            grade_value = float(grade)
        except ValueError:
            messagebox.showwarning("Invalid value", "Units and grade must be numbers.", parent=self)
            return
        if unit_value <= 0:
            messagebox.showwarning("Invalid units", "Units must be greater than zero.", parent=self)
            return
        if grade_value < 1.0 or grade_value > 5.0:
            messagebox.showwarning("Invalid grade", "Grade must be between 1.00 and 5.00.", parent=self)
            return
        self.result = (code, subject, f"{unit_value:g}", f"{grade_value:.2f}")
        self.destroy()


class NotificationApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.master = master
        self.students = []
        self.selected_student_index = None
        self.grades = []
        self.setup_styles()
        self.build_ui()
        self.load_students_into_table()
        self.on_content_mode_changed()
        self.on_channel_changed()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Modern.Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, rowheight=36, font=(FONT, 9), borderwidth=0)
        style.configure("Modern.Treeview.Heading", background="#F7F8FB", foreground=MUTED, font=(FONT, 8, "bold"), relief="flat", borderwidth=0, padding=(10, 9))
        style.map("Modern.Treeview", background=[("selected", SOFT)], foreground=[("selected", PRIMARY)])
        style.configure("Modern.Vertical.TScrollbar", troughcolor="#F7F8FB", background="#CBD2DE", borderwidth=0, arrowsize=10)
        style.configure("Modern.TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT, bordercolor=BORDER, arrowcolor=MUTED, padding=7)

    def button(self, parent, text, command, primary=False, danger=False):
        bg = DANGER if danger else PRIMARY if primary else "#EEF1F5"
        fg = "white" if primary or danger else TEXT
        active = "#B63838" if danger else PRIMARY_HOVER if primary else "#E2E6EC"
        return tk.Button(parent, text=text, command=command, font=(FONT, 9, "bold"), bg=bg, fg=fg, activebackground=active, activeforeground=fg, relief="flat", bd=0, padx=14, pady=8, cursor="hand2")

    def card(self, parent, padx=18, pady=16):
        return tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=padx, pady=pady)

    def build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self, bg=SIDEBAR, width=225)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR, padx=22, pady=24)
        brand.pack(fill="x")
        tk.Label(brand, text="N", font=(FONT, 18, "bold"), fg="white", bg=PRIMARY, width=2, pady=4).pack(side="left")
        brand_text = tk.Frame(brand, bg=SIDEBAR)
        brand_text.pack(side="left", padx=(10, 0))
        tk.Label(brand_text, text="NDMU", font=(FONT, 13, "bold"), fg="white", bg=SIDEBAR).pack(anchor="w")
        tk.Label(brand_text, text="Notification Console", font=(FONT, 8), fg=SIDEBAR_MUTED, bg=SIDEBAR).pack(anchor="w")

        tk.Label(sidebar, text="WORKSPACE", font=(FONT, 8, "bold"), fg=SIDEBAR_MUTED, bg=SIDEBAR, padx=22).pack(anchor="w", pady=(22, 10))
        nav = tk.Frame(sidebar, bg=SIDEBAR, padx=12)
        nav.pack(fill="x")
        self.students_nav = self.nav_button(nav, "▣   Students", self.show_students, True)
        self.notifications_nav = self.nav_button(nav, "↗   Notifications", self.show_notifications, False)

        sidebar_bottom = tk.Frame(sidebar, bg=SIDEBAR, padx=22, pady=22)
        sidebar_bottom.pack(side="bottom", fill="x")
        tk.Label(sidebar_bottom, text="Factory Method", font=(FONT, 8, "bold"), fg=SIDEBAR_TEXT, bg=SIDEBAR).pack(anchor="w")
        tk.Label(sidebar_bottom, text="One notify() interface.\nMultiple delivery channels.", font=(FONT, 8), fg=SIDEBAR_MUTED, bg=SIDEBAR, justify="left").pack(anchor="w", pady=(5, 0))

        main = tk.Frame(self, bg=BG, padx=28, pady=24)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        main.rowconfigure(3, weight=0, minsize=190)
        self.main = main

        header = tk.Frame(main, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        self.page_title = tk.Label(header, text="Students", font=(FONT, 24, "bold"), fg=TEXT, bg=BG)
        self.page_title.pack(side="left")
        self.page_subtitle = tk.Label(header, text="Manage students, academic records, and notifications", font=(FONT, 9), fg=MUTED, bg=BG)
        self.page_subtitle.pack(side="left", padx=(14, 0), pady=(10, 0))
        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")
        self.button(actions, "+  Add Student", self.on_add_student, primary=True).pack(side="left")

        stats = tk.Frame(main, bg=BG)
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(3):
            stats.columnconfigure(i, weight=1)
        self.stat_card(stats, 0, "STUDENTS", "0", "Registered records", "student_count")
        self.stat_card(stats, 1, "CURRENT UNITS", "0", "Selected student's units", "units_count")
        self.stat_card(stats, 2, "WEIGHTED AVERAGE", "N/A", "Selected student's average", "average_value")

        content = tk.Frame(main, bg=BG)
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=5)
        content.rowconfigure(0, weight=1)
        self.content = content
        self.build_students_card(content)
        self.build_details_card(content)
        self.build_notification_card(main)

    def nav_button(self, parent, text, command, active):
        frame = tk.Frame(parent, bg=PRIMARY if active else SIDEBAR, padx=12, pady=10, cursor="hand2")
        frame.pack(fill="x", pady=2)
        label = tk.Label(frame, text=text, font=(FONT, 9, "bold" if active else "normal"), fg="white" if active else SIDEBAR_TEXT, bg=PRIMARY if active else SIDEBAR, cursor="hand2")
        label.pack(anchor="w")
        frame.bind("<Button-1>", lambda _event: command())
        label.bind("<Button-1>", lambda _event: command())
        return frame

    def set_active_nav(self, active):
        for frame, selected in ((self.students_nav, active == "students"), (self.notifications_nav, active == "notifications")):
            frame.configure(bg=PRIMARY if selected else SIDEBAR)
            label = frame.winfo_children()[0]
            label.configure(bg=PRIMARY if selected else SIDEBAR, fg="white" if selected else SIDEBAR_TEXT, font=(FONT, 9, "bold" if selected else "normal"))

    def show_students(self):
        self.set_active_nav("students")
        self.page_title.configure(text="Students")
        self.page_subtitle.configure(text="Manage students, academic records, and notifications")
        self.student_search.focus_set()

    def show_notifications(self):
        self.set_active_nav("notifications")
        self.page_title.configure(text="Notifications")
        self.page_subtitle.configure(text="Send grades or custom messages through your selected channel")
        self.master.after_idle(self.focus_notification)

    def focus_notification(self):
        self.recipient_entry.focus_set()
        self.notification_card.configure(highlightbackground=PRIMARY, highlightthickness=2)
        self.master.after(500, lambda: self.notification_card.configure(highlightbackground=BORDER, highlightthickness=1))

    def stat_card(self, parent, column, label, value, subtitle, attr):
        frame = self.card(parent, 16, 12)
        frame.grid(row=0, column=column, sticky="ew", padx=(0, 10 if column < 2 else 0))
        tk.Label(frame, text=label, font=(FONT, 8, "bold"), fg=MUTED, bg=CARD).pack(anchor="w")
        variable = tk.StringVar(value=value)
        setattr(self, attr, variable)
        tk.Label(frame, textvariable=variable, font=(FONT, 18, "bold"), fg=TEXT, bg=CARD).pack(anchor="w", pady=(3, 0))
        tk.Label(frame, text=subtitle, font=(FONT, 8), fg=MUTED, bg=CARD).pack(anchor="w", pady=(2, 0))

    def build_students_card(self, parent):
        card = self.card(parent, 18, 15)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        card.rowconfigure(2, weight=1)
        card.columnconfigure(0, weight=1)
        title_row = tk.Frame(card, bg=CARD)
        title_row.grid(row=0, column=0, sticky="ew")
        tk.Label(title_row, text="Student Directory", font=(FONT, 12, "bold"), fg=TEXT, bg=CARD).pack(side="left")
        self.student_search = tk.StringVar()
        search = tk.Entry(title_row, textvariable=self.student_search, font=(FONT, 8), bg="#F7F8FB", fg=TEXT, relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, width=20)
        search.pack(side="right", ipady=6)
        self.student_search.trace_add("write", lambda *_args: self.refresh_student_rows())
        tk.Label(card, text="Search students", font=(FONT, 7), fg=MUTED, bg=CARD).grid(row=1, column=0, sticky="e", pady=(2, 8))

        table_frame = tk.Frame(card, bg=CARD)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.students_table = ttk.Treeview(table_frame, columns=("name", "program", "period"), show="headings", style="Modern.Treeview", selectmode="browse", height=8)
        self.students_table.heading("name", text="STUDENT")
        self.students_table.heading("program", text="PROGRAM")
        self.students_table.heading("period", text="PERIOD")
        self.students_table.column("name", width=230, anchor="w", stretch=True)
        self.students_table.column("program", width=125, anchor="w", stretch=False)
        self.students_table.column("period", width=105, anchor="w", stretch=False)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.students_table.yview, style="Modern.Vertical.TScrollbar")
        self.students_table.configure(yscrollcommand=scroll.set)
        self.students_table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.students_table.bind("<<TreeviewSelect>>", self.on_student_selected)
        self.students_table.bind("<Double-1>", lambda _event: self.on_edit_student())

        buttons = tk.Frame(card, bg=CARD)
        buttons.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self.button(buttons, "Edit", self.on_edit_student).pack(side="left")
        self.button(buttons, "Delete", self.on_delete_student, danger=True).pack(side="left", padx=(7, 0))
        self.button(buttons, "Save", self.on_save_students).pack(side="right")

    def build_details_card(self, parent):
        card = self.card(parent, 18, 15)
        card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        card.rowconfigure(3, weight=1)
        card.columnconfigure(0, weight=1)

        top = tk.Frame(card, bg=CARD)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        self.avatar = tk.Label(top, text="--", font=(FONT, 13, "bold"), fg=PRIMARY, bg=SOFT, width=4, pady=8)
        self.avatar.grid(row=0, column=0, rowspan=2, sticky="nw")
        identity = tk.Frame(top, bg=CARD)
        identity.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        self.student_name = tk.StringVar(value="No student selected")
        self.program_year = tk.StringVar(value="Select a student from the directory")
        self.academic_period = tk.StringVar(value="")
        tk.Label(identity, textvariable=self.student_name, font=(FONT, 14, "bold"), fg=TEXT, bg=CARD).pack(anchor="w")
        tk.Label(identity, textvariable=self.program_year, font=(FONT, 9), fg=MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))
        self.period_badge = tk.Label(identity, textvariable=self.academic_period, font=(FONT, 8, "bold"), fg=PRIMARY, bg=SOFT, padx=8, pady=3)
        self.period_badge.pack(anchor="w", pady=(7, 0))

        tk.Frame(card, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew", pady=14)

        title = tk.Frame(card, bg=CARD)
        title.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        tk.Label(title, text="Academic Records", font=(FONT, 11, "bold"), fg=TEXT, bg=CARD).pack(side="left")
        self.button(title, "+  Add Subject", self.on_add_grade, primary=True).pack(side="right")

        table_frame = tk.Frame(card, bg=CARD)
        table_frame.grid(row=3, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.grades_table = ttk.Treeview(table_frame, columns=("course_code", "course_title", "units", "grade"), show="headings", style="Modern.Treeview", selectmode="browse", height=10)
        self.grades_table.heading("course_code", text="CODE")
        self.grades_table.heading("course_title", text="COURSE TITLE")
        self.grades_table.heading("units", text="UNITS")
        self.grades_table.heading("grade", text="GRADE")
        self.grades_table.column("course_code", width=100, minwidth=90, anchor="w", stretch=False)
        self.grades_table.column("course_title", width=330, minwidth=220, anchor="w", stretch=True)
        self.grades_table.column("units", width=70, minwidth=60, anchor="center", stretch=False)
        self.grades_table.column("grade", width=75, minwidth=65, anchor="center", stretch=False)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.grades_table.yview, style="Modern.Vertical.TScrollbar")
        self.grades_table.configure(yscrollcommand=scroll.set)
        self.grades_table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.grades_table.bind("<Double-1>", lambda _event: self.on_edit_grade())

        bottom = tk.Frame(card, bg=CARD)
        bottom.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.button(bottom, "Edit", self.on_edit_grade).pack(side="left")
        self.button(bottom, "Delete", self.on_delete_grade, danger=True).pack(side="left", padx=(7, 0))
        self.button(bottom, "Save Grades", self.on_save_grades).pack(side="right")

    def build_notification_card(self, parent):
        card = self.card(parent, 18, 12)
        card.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        card.columnconfigure(1, weight=1)
        self.notification_card = card

        heading = tk.Frame(card, bg=CARD)
        heading.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        tk.Label(heading, text="Send Notification", font=(FONT, 11, "bold"), fg=TEXT, bg=CARD).pack(side="left")
        tk.Label(heading, text="Notify the selected student through your chosen channel", font=(FONT, 8), fg=MUTED, bg=CARD).pack(side="left", padx=(12, 0))

        tk.Label(card, text="CONTENT", font=(FONT, 8, "bold"), fg=MUTED, bg=CARD).grid(row=1, column=0, sticky="w")
        self.content_mode = tk.StringVar(value="Grades")
        self.content_box = ttk.Combobox(card, textvariable=self.content_mode, values=["Grades", "Message Only"], state="readonly", width=15, style="Modern.TCombobox")
        self.content_box.grid(row=1, column=1, sticky="w")
        self.content_box.bind("<<ComboboxSelected>>", self.on_content_mode_changed)

        tk.Label(card, text="CHANNEL", font=(FONT, 8, "bold"), fg=MUTED, bg=CARD).grid(row=1, column=2, sticky="e", padx=(18, 8))
        self.channel = tk.StringVar(value=list(SERVICES)[0])
        self.channel_box = ttk.Combobox(card, textvariable=self.channel, values=list(SERVICES), state="readonly", width=15, style="Modern.TCombobox")
        self.channel_box.grid(row=1, column=3, sticky="e")
        self.channel_box.bind("<<ComboboxSelected>>", self.on_channel_changed)

        self.recipient_label = tk.Label(card, text="RECIPIENT", font=(FONT, 8, "bold"), fg=MUTED, bg=CARD)
        self.recipient_label.grid(row=2, column=0, sticky="w", pady=(8, 0), padx=(0, 8))
        self.recipient = tk.StringVar()
        self.recipient_entry = tk.Entry(card, textvariable=self.recipient, font=(FONT, 9), bg="#F7F8FB", fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY)
        self.recipient_entry.grid(row=2, column=1, columnspan=3, sticky="ew", ipady=6, pady=(8, 0))

        self.message_label = tk.Label(card, text="MESSAGE", font=(FONT, 8, "bold"), fg=MUTED, bg=CARD)
        self.message_label.grid(row=3, column=0, sticky="nw", pady=(8, 0), padx=(0, 8))
        self.message_text = tk.Text(card, height=2, font=(FONT, 9), wrap="word", bg="#F7F8FB", fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY)
        self.message_text.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(8, 0))

        footer = tk.Frame(card, bg=CARD)
        footer.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self.recipient_hint = tk.Label(footer, text="", font=(FONT, 8), fg=MUTED, bg=CARD)
        self.recipient_hint.pack(side="left")
        self.button(footer, "Send Notification  →", self.on_send, primary=True).pack(side="right")

    def refresh_student_rows(self):
        search = self.student_search.get().strip().lower()
        selected_name = None
        if self.selected_student_index is not None and self.selected_student_index < len(self.students):
            selected_name = self.students[self.selected_student_index].get("name", "")
        for item in self.students_table.get_children():
            self.students_table.delete(item)
        for index, student in enumerate(self.students):
            name = student.get("name", "")
            program = student.get("program_year", "")
            period = student.get("academic_period", "")
            if search and search not in f"{name} {program} {period}".lower():
                continue
            item = self.students_table.insert("", "end", iid=f"student_{index}", values=(name, program, period))
            if selected_name and name == selected_name:
                self.students_table.selection_set(item)
                self.students_table.focus(item)
        self.student_count.set(str(len(self.students)))

    def load_students_into_table(self, select_index=None):
        try:
            self.students = load_students()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Student data error", str(exc))
            self.students = []
        self.refresh_student_rows()
        if self.students:
            index = 0 if select_index is None else max(0, min(select_index, len(self.students) - 1))
            item_id = f"student_{index}"
            if self.students_table.exists(item_id):
                self.students_table.selection_set(item_id)
                self.students_table.focus(item_id)
                self.students_table.see(item_id)
        else:
            self.selected_student_index = None
            self.grades = []
            self.refresh_grade_table()

    def get_selected_student_index(self):
        selection = self.students_table.selection()
        if not selection:
            return None
        item_id = selection[0]
        if item_id.startswith("student_"):
            try:
                return int(item_id.split("_", 1)[1])
            except ValueError:
                return None
        return None

    def on_student_selected(self, _event=None):
        index = self.get_selected_student_index()
        if index is None or index >= len(self.students):
            return
        self.selected_student_index = index
        student = self.students[index]
        self.grades = [tuple(row) for row in student.get("grades", [])]
        name = student.get("name", "")
        self.student_name.set(name or "Unnamed student")
        self.program_year.set(student.get("program_year", "") or "Program / Year not specified")
        self.academic_period.set(student.get("academic_period", "") or "Academic period not specified")
        initials = "".join(part[0] for part in name.split()[:2]).upper() or "--"
        self.avatar.configure(text=initials)
        self.refresh_grade_table()
        if self.content_mode.get() == "Grades":
            self.on_content_mode_changed()

    def on_add_student(self):
        dialog = StudentDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        name, program, period = dialog.result
        self.students.append({"name": name, "program_year": program, "academic_period": period, "grades": []})
        if not self.on_save_students(silent=True):
            self.students.pop()
            return
        self.student_search.set("")
        self.load_students_into_table(len(self.students) - 1)

    def on_edit_student(self):
        index = self.get_selected_student_index()
        if index is None:
            messagebox.showwarning("Select a student", "Select a student to edit first.", parent=self)
            return
        student = self.students[index]
        dialog = StudentDialog(self, (student.get("name", ""), student.get("program_year", ""), student.get("academic_period", "")))
        self.wait_window(dialog)
        if dialog.result is None:
            return
        name, program, period = dialog.result
        student["name"] = name
        student["program_year"] = program
        student["academic_period"] = period
        self.on_save_students(silent=True)
        self.student_search.set("")
        self.load_students_into_table(index)

    def on_delete_student(self):
        index = self.get_selected_student_index()
        if index is None:
            messagebox.showwarning("Select a student", "Select a student to delete first.", parent=self)
            return
        student = self.students[index]
        name = student.get("name", "this student")
        if not messagebox.askyesno("Delete Student", f"Delete {name} and all of their grade records?", parent=self):
            return
        del self.students[index]
        self.on_save_students(silent=True)
        new_index = min(index, len(self.students) - 1) if self.students else None
        self.load_students_into_table(new_index)

    def on_save_students(self, silent=False):
        try:
            save_students(self.students)
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return False
        if not silent:
            messagebox.showinfo("Students saved", "Student data has been saved to students.json.", parent=self)
        return True

    def refresh_grade_table(self):
        for item in self.grades_table.get_children():
            self.grades_table.delete(item)
        for grade in self.grades:
            self.grades_table.insert("", "end", values=grade)
        self.refresh_from_table()

    def refresh_from_table(self):
        self.grades = [tuple(self.grades_table.item(item, "values")) for item in self.grades_table.get_children()]
        total_units, weighted_average = calculate_totals(self.grades)
        self.units_count.set(f"{total_units:g}")
        self.average_value.set(f"{weighted_average:.2f}" if weighted_average is not None else "N/A")

    def save_current_student_grades(self):
        if self.selected_student_index is None:
            return False
        self.refresh_from_table()
        self.students[self.selected_student_index]["grades"] = [list(row) for row in self.grades]
        try:
            save_students(self.students)
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return False
        return True

    def on_add_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Add or select a student before adding grades.", parent=self)
            return
        dialog = GradeDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.grades_table.insert("", "end", values=dialog.result)
        self.refresh_from_table()
        self.save_current_student_grades()

    def on_edit_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student first.", parent=self)
            return
        selection = self.grades_table.selection()
        if not selection:
            messagebox.showwarning("Select a subject", "Select a subject to edit first.", parent=self)
            return
        item = selection[0]
        values = self.grades_table.item(item, "values")
        dialog = GradeDialog(self, values)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.grades_table.item(item, values=dialog.result)
        self.refresh_from_table()
        self.save_current_student_grades()

    def on_delete_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student first.", parent=self)
            return
        selection = self.grades_table.selection()
        if not selection:
            messagebox.showwarning("Select a subject", "Select a subject to delete first.", parent=self)
            return
        item = selection[0]
        values = self.grades_table.item(item, "values")
        if not messagebox.askyesno("Delete Subject", f"Delete {values[0]} - {values[1]}?", parent=self):
            return
        self.grades_table.delete(item)
        self.refresh_from_table()
        self.save_current_student_grades()

    def on_save_grades(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student first.", parent=self)
            return
        if self.save_current_student_grades():
            messagebox.showinfo("Grades saved", "The selected student's grades have been saved.", parent=self)

    def on_content_mode_changed(self, _event=None):
        if self.content_mode.get() == "Grades":
            self.message_text.configure(state="normal")
            self.message_text.delete("1.0", "end")
            self.message_text.insert("1.0", self.build_message())
            self.message_text.configure(state="disabled")
            self.message_label.configure(text="PREVIEW")
        else:
            self.message_text.configure(state="normal")
            self.message_text.delete("1.0", "end")
            self.message_label.configure(text="MESSAGE")

    def on_channel_changed(self, _event=None):
        channel = self.channel.get().lower()
        if channel == "email":
            self.recipient_hint.configure(text="Enter an email address.")
        elif channel == "sms":
            self.recipient_hint.configure(text="Enter a phone number.")
        elif channel == "push":
            self.recipient_hint.configure(text="Enter a Firebase Cloud Messaging token.")
        else:
            self.recipient_hint.configure(text="Enter the recipient identifier for this channel.")

    def build_message(self):
        if self.selected_student_index is None:
            return "Select a student to generate their grade summary."
        student = self.students[self.selected_student_index]
        grades = [tuple(row) for row in student.get("grades", [])]
        lines = [f"Student: {student.get('name', '')}", f"Program / Year: {student.get('program_year', '')}"]
        if student.get("academic_period"):
            lines.append(f"Academic Period: {student.get('academic_period')}")
        lines.extend(["", "Grades:"])
        for code, subject, units, grade in grades:
            lines.append(f"{code} - {subject}: {grade} ({units} units)")
        total_units, average = calculate_totals(grades)
        lines.extend(["", f"Total Units: {total_units:g}", f"Weighted Average: {average:.2f}" if average is not None else "Weighted Average: N/A"])
        return "\n".join(lines)

    def on_send(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student before sending a notification.", parent=self)
            return
        recipient = self.recipient.get().strip()
        if not recipient:
            messagebox.showwarning("Recipient required", "Enter a recipient first.", parent=self)
            self.recipient_entry.focus_set()
            return
        if self.content_mode.get() == "Grades":
            message = self.build_message()
        else:
            message = self.message_text.get("1.0", "end").strip()
            if not message:
                messagebox.showwarning("Message required", "Enter a message first.", parent=self)
                self.message_text.focus_set()
                return
        service_class = SERVICES.get(self.channel.get())
        if service_class is None:
            messagebox.showerror("Channel error", "The selected notification channel is not configured.", parent=self)
            return
        try:
            service = service_class()
            service.set_recipient(recipient)
            service.notify(message)
        except Exception as exc:
            messagebox.showerror("Notification failed", str(exc), parent=self)
            return
        messagebox.showinfo("Notification sent", f"Notification sent through {self.channel.get()}.", parent=self)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("NDMU Notification Console")
    root.geometry("1400x950")
    root.minsize(1150, 800)
    app = NotificationApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
