import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from notifications import SERVICES

NAVY = "#1F3864"
BAND = "#17375E"
CREAM = "#FFF2CC"
INK = "#1A1A2E"

BASE_DIR = Path(__file__).resolve().parent
GRADES_FILE = BASE_DIR / "grades.txt"
STUDENTS_FILE = BASE_DIR / "students.json"


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
    return "Student: " + student_info + "\n\nGrades:\n" + "\n".join(rows) + f"\n\nTotal Units: {total_units:g}" + f"\nWeighted Average: {average_text}"


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


class StudentDialog(tk.Toplevel):
    def __init__(self, parent, title, values=None):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg="white")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        values = values or ("", "", "")
        self.name_var = tk.StringVar(value=values[0])
        self.program_var = tk.StringVar(value=values[1])
        self.period_var = tk.StringVar(value=values[2])
        fields = [("Student Name", self.name_var), ("Program / Year", self.program_var), ("Academic Period", self.period_var)]
        for row, (label, variable) in enumerate(fields):
            tk.Label(self, text=label + ":", font=("Calibri", 10, "bold"), bg="white").grid(row=row, column=0, sticky="w", padx=(14, 8), pady=6)
            tk.Entry(self, textvariable=variable, font=("Calibri", 10), width=38).grid(row=row, column=1, padx=(0, 14), pady=6)
        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=3, column=0, columnspan=2, sticky="e", padx=14, pady=(5, 14))
        tk.Button(button_frame, text="Cancel", command=self.destroy, relief="flat", padx=12, pady=4).pack(side="right", padx=(7, 0))
        tk.Button(button_frame, text="Save", command=self.validate_and_save, bg=NAVY, fg="white", activebackground=BAND, activeforeground="white", relief="flat", padx=14, pady=4).pack(side="right")
        self.bind("<Return>", lambda _event: self.validate_and_save())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def validate_and_save(self):
        name = self.name_var.get().strip()
        program = self.program_var.get().strip()
        period = self.period_var.get().strip()
        if not name or not program:
            messagebox.showwarning("Missing information", "Student Name and Program / Year are required.", parent=self)
            return
        self.result = (name, program, period)
        self.destroy()


class GradeDialog(tk.Toplevel):
    def __init__(self, parent, title, values=None):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg="white")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        values = values or ("", "", "", "")
        self.code_var = tk.StringVar(value=values[0])
        self.subject_var = tk.StringVar(value=values[1])
        self.units_var = tk.StringVar(value=values[2])
        self.grade_var = tk.StringVar(value=values[3])
        fields = [("Course Code", self.code_var), ("Course Title", self.subject_var), ("Units", self.units_var), ("Grade", self.grade_var)]
        for row, (label, variable) in enumerate(fields):
            tk.Label(self, text=label + ":", font=("Calibri", 10, "bold"), bg="white").grid(row=row, column=0, sticky="w", padx=(14, 8), pady=6)
            tk.Entry(self, textvariable=variable, font=("Calibri", 10), width=38).grid(row=row, column=1, padx=(0, 14), pady=6)
        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", padx=14, pady=(5, 14))
        tk.Button(button_frame, text="Cancel", command=self.destroy, relief="flat", padx=12, pady=4).pack(side="right", padx=(7, 0))
        tk.Button(button_frame, text="Save", command=self.validate_and_save, bg=NAVY, fg="white", activebackground=BAND, activeforeground="white", relief="flat", padx=14, pady=4).pack(side="right")
        self.bind("<Return>", lambda _event: self.validate_and_save())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

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
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padx=14, pady=10, bg="white")
        self.columnconfigure(1, weight=1)
        self.students = []
        self.selected_student_index = None
        self.grades = []

        tk.Label(self, text="NDMU University Notification Console", font=("Calibri", 15, "bold"), fg=NAVY, bg="white").grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(self, text="Factory Method - the channel varies, notify() does not.", font=("Calibri", 9, "italic"), fg="#595959", bg="white").grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 7))

        settings = tk.LabelFrame(self, text="Notification Settings", font=("Calibri", 10, "bold"), bg="white", fg=BAND, padx=8, pady=6)
        settings.grid(row=2, column=0, columnspan=3, sticky="ew")
        settings.columnconfigure(1, weight=1)
        tk.Label(settings, text="Send:", font=("Calibri", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.content_mode = tk.StringVar(value="Grades")
        mode_frame = tk.Frame(settings, bg="white")
        mode_frame.grid(row=0, column=1, sticky="w")
        tk.Radiobutton(mode_frame, text="Grades", variable=self.content_mode, value="Grades", command=self.on_content_mode_changed, font=("Calibri", 10), bg="white", activebackground="white").pack(side="left")
        tk.Radiobutton(mode_frame, text="Message Only", variable=self.content_mode, value="Message Only", command=self.on_content_mode_changed, font=("Calibri", 10), bg="white", activebackground="white").pack(side="left", padx=(12, 0))

        tk.Label(settings, text="Channel:", font=("Calibri", 10, "bold"), bg="white").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(5, 0))
        self.channel = tk.StringVar(value=list(SERVICES)[0])
        self.channel_box = ttk.Combobox(settings, textvariable=self.channel, values=list(SERVICES), state="readonly", width=18)
        self.channel_box.grid(row=1, column=1, sticky="w", pady=(5, 0))
        self.channel_box.bind("<<ComboboxSelected>>", self.on_channel_changed)
        self.recipient_label = tk.Label(settings, text="Recipient Email:", font=("Calibri", 10, "bold"), bg="white")
        self.recipient_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(5, 0))
        self.recipient = tk.StringVar()
        tk.Entry(settings, textvariable=self.recipient, width=52, font=("Calibri", 10)).grid(row=2, column=1, sticky="w", pady=(5, 0))
        self.recipient_hint = tk.Label(settings, text="Enter the email address where the notification should be sent.", font=("Calibri", 8), fg="#666666", bg="white")
        self.recipient_hint.grid(row=3, column=1, sticky="w", pady=(2, 0))

        self.message_label = tk.Label(self, text="Custom Message:", font=("Calibri", 10, "bold"), bg="white")
        self.message_label.grid(row=4, column=0, sticky="nw", pady=(8, 0))
        self.message_text = tk.Text(self, height=3, width=64, font=("Calibri", 10), wrap="word", relief="solid", borderwidth=1)
        self.message_text.grid(row=4, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 0))

        students_frame = tk.LabelFrame(self, text="Students", font=("Calibri", 10, "bold"), bg="white", fg=BAND, padx=8, pady=6)
        students_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        student_table_frame = tk.Frame(students_frame, bg="white")
        student_table_frame.grid(row=0, column=0, sticky="w")
        self.students_table = ttk.Treeview(student_table_frame, columns=("name", "program", "period"), show="headings", height=5)
        self.students_table.heading("name", text="Student Name")
        self.students_table.heading("program", text="Program / Year")
        self.students_table.heading("period", text="Academic Period")
        self.students_table.column("name", width=220, anchor="w")
        self.students_table.column("program", width=180, anchor="w")
        self.students_table.column("period", width=150, anchor="w")
        student_scrollbar = ttk.Scrollbar(student_table_frame, orient="vertical", command=self.students_table.yview)
        self.students_table.configure(yscrollcommand=student_scrollbar.set)
        self.students_table.grid(row=0, column=0)
        student_scrollbar.grid(row=0, column=1, sticky="ns")
        self.students_table.bind("<<TreeviewSelect>>", self.on_student_selected)
        self.students_table.bind("<Double-1>", lambda _event: self.on_edit_student())

        student_buttons = tk.Frame(students_frame, bg="white")
        student_buttons.grid(row=1, column=0, sticky="w", pady=(5, 0))
        tk.Button(student_buttons, text="Add Student", command=self.on_add_student, font=("Calibri", 9, "bold"), bg=NAVY, fg="white", activebackground=BAND, activeforeground="white", relief="flat", padx=10, pady=3).pack(side="left")
        tk.Button(student_buttons, text="Edit Selected", command=self.on_edit_student, font=("Calibri", 9), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))
        tk.Button(student_buttons, text="Delete Selected", command=self.on_delete_student, font=("Calibri", 9), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))
        tk.Button(student_buttons, text="Save Students", command=self.on_save_students, font=("Calibri", 9, "bold"), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))

        info_frame = tk.LabelFrame(self, text="Selected Student", font=("Calibri", 9, "bold"), bg="white", fg=BAND, padx=8, pady=5)
        info_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.student_name = tk.StringVar(value="--")
        self.program_year = tk.StringVar(value="--")
        self.academic_period = tk.StringVar(value="--")
        for column, (label, variable) in enumerate([("Name", self.student_name), ("Program / Year", self.program_year), ("Academic Period", self.academic_period)]):
            tk.Label(info_frame, text=f"{label}:", font=("Calibri", 8, "bold"), bg="white").grid(row=0, column=column * 2, sticky="w", padx=(0, 4))
            tk.Label(info_frame, textvariable=variable, font=("Calibri", 8), bg="white").grid(row=0, column=column * 2 + 1, sticky="w", padx=(0, 15))

        self.grades_section = tk.Frame(self, bg="white")
        self.grades_section.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(7, 0))
        self.grades_section.columnconfigure(1, weight=1)
        tk.Label(self.grades_section, text="Grades:", font=("Calibri", 10, "bold"), bg="white").grid(row=0, column=0, sticky="nw", padx=(0, 8))
        self.table_frame = tk.Frame(self.grades_section, bg="white")
        self.table_frame.grid(row=0, column=1, sticky="w")
        self.grades_table = ttk.Treeview(self.table_frame, columns=("course_code", "course_title", "units", "grade"), show="headings", height=6)
        self.grades_table.heading("course_code", text="Course Code")
        self.grades_table.heading("course_title", text="Course Title")
        self.grades_table.heading("units", text="Units")
        self.grades_table.heading("grade", text="Grade")
        self.grades_table.column("course_code", width=105, anchor="w")
        self.grades_table.column("course_title", width=260, anchor="w")
        self.grades_table.column("units", width=55, anchor="center")
        self.grades_table.column("grade", width=55, anchor="center")
        grade_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.grades_table.yview)
        self.grades_table.configure(yscrollcommand=grade_scrollbar.set)
        self.grades_table.grid(row=0, column=0)
        grade_scrollbar.grid(row=0, column=1, sticky="ns")
        self.grades_table.bind("<Double-1>", lambda _event: self.on_edit_grade())

        grade_buttons = tk.Frame(self.grades_section, bg="white")
        grade_buttons.grid(row=2, column=1, sticky="w", pady=(5, 0))
        tk.Button(grade_buttons, text="Add Subject", command=self.on_add_grade, font=("Calibri", 9, "bold"), bg=NAVY, fg="white", activebackground=BAND, activeforeground="white", relief="flat", padx=10, pady=3).pack(side="left")
        tk.Button(grade_buttons, text="Edit Selected", command=self.on_edit_grade, font=("Calibri", 9), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))
        tk.Button(grade_buttons, text="Delete Selected", command=self.on_delete_grade, font=("Calibri", 9), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))
        tk.Button(grade_buttons, text="Save Grades", command=self.on_save_grades, font=("Calibri", 9, "bold"), relief="flat", padx=10, pady=3).pack(side="left", padx=(6, 0))

        self.summary_frame = tk.Frame(self.grades_section, bg=CREAM, padx=8, pady=4)
        self.summary_frame.grid(row=3, column=1, sticky="ew", pady=(4, 0))
        self.total_units_var = tk.StringVar(value="Total Units: 0")
        self.average_var = tk.StringVar(value="Weighted Average: N/A")
        tk.Label(self.summary_frame, textvariable=self.total_units_var, font=("Calibri", 9, "bold"), bg=CREAM, fg=INK).pack(side="left")
        tk.Label(self.summary_frame, textvariable=self.average_var, font=("Calibri", 9, "bold"), bg=CREAM, fg=INK).pack(side="left", padx=(18, 0))

        self.log = tk.Text(self, height=5, width=82, font=("Consolas", 9), state="disabled", bg="#F7F7F7", relief="solid", borderwidth=1)
        self.log.grid(row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))
        tk.Button(self, text="Send Notification", command=self.on_send, font=("Calibri", 10, "bold"), bg=NAVY, fg="white", activebackground=BAND, activeforeground="white", relief="flat", padx=16, pady=5).grid(row=9, column=1, sticky="e", pady=(8, 0))

        self.load_students_into_table()
        self.on_content_mode_changed()
        self.on_channel_changed()

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def load_students_into_table(self, select_index=None):
        try:
            self.students = load_students()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Student data error", str(exc))
            self.students = []
        for item in self.students_table.get_children():
            self.students_table.delete(item)
        for student in self.students:
            self.students_table.insert("", "end", values=(student.get("name", ""), student.get("program_year", ""), student.get("academic_period", "")))
        if self.students:
            index = 0 if select_index is None else max(0, min(select_index, len(self.students) - 1))
            items = self.students_table.get_children()
            self.students_table.selection_set(items[index])
            self.students_table.focus(items[index])
            self.students_table.see(items[index])
        else:
            self.selected_student_index = None
            self.grades = []
            self.refresh_grade_table()

    def get_selected_student_index(self):
        selection = self.students_table.selection()
        if not selection:
            return None
        items = self.students_table.get_children()
        return items.index(selection[0])

    def on_student_selected(self, _event=None):
        index = self.get_selected_student_index()
        if index is None or index >= len(self.students):
            return
        self.selected_student_index = index
        student = self.students[index]
        self.grades = [tuple(row) for row in student.get("grades", [])]
        self.student_name.set(student.get("name", "--"))
        self.program_year.set(student.get("program_year", "--"))
        self.academic_period.set(student.get("academic_period", "") or "--")
        self.refresh_grade_table()
        self.write(f"Selected student: {student.get('name', '')}")

    def on_add_student(self):
        dialog = StudentDialog(self, "Add Student")
        self.wait_window(dialog)
        if dialog.result is None:
            return
        name, program, period = dialog.result
        self.students.append({"name": name, "program_year": program, "academic_period": period, "grades": []})
        self.on_save_students(silent=True)
        self.load_students_into_table(len(self.students) - 1)
        self.write(f"Added student: {name}")

    def on_edit_student(self):
        index = self.get_selected_student_index()
        if index is None:
            messagebox.showwarning("Select a student", "Select a student to edit first.")
            return
        student = self.students[index]
        dialog = StudentDialog(self, "Edit Student", (student.get("name", ""), student.get("program_year", ""), student.get("academic_period", "")))
        self.wait_window(dialog)
        if dialog.result is None:
            return
        name, program, period = dialog.result
        student["name"] = name
        student["program_year"] = program
        student["academic_period"] = period
        self.on_save_students(silent=True)
        self.load_students_into_table(index)
        self.write(f"Modified student: {name}")

    def on_delete_student(self):
        index = self.get_selected_student_index()
        if index is None:
            messagebox.showwarning("Select a student", "Select a student to delete first.")
            return
        student = self.students[index]
        name = student.get("name", "this student")
        if not messagebox.askyesno("Delete Student", f"Delete {name} and all of their grade records?"):
            return
        del self.students[index]
        self.on_save_students(silent=True)
        new_index = min(index, len(self.students) - 1) if self.students else None
        self.load_students_into_table(new_index)
        self.write(f"Deleted student: {name}")

    def on_save_students(self, silent=False):
        try:
            save_students(self.students)
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return False
        if not silent:
            messagebox.showinfo("Students saved", "Student data has been saved to students.json.")
            self.write("Saved student changes to students.json.")
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
        self.total_units_var.set(f"Total Units: {total_units:g}")
        average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"
        self.average_var.set(f"Weighted Average: {average_text}")

    def save_current_student_grades(self):
        if self.selected_student_index is None:
            return False
        self.refresh_from_table()
        self.students[self.selected_student_index]["grades"] = [list(row) for row in self.grades]
        try:
            save_students(self.students)
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return False
        return True

    def on_add_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Add or select a student before adding grades.")
            return
        dialog = GradeDialog(self, "Add Subject / Grade")
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.grades_table.insert("", "end", values=dialog.result)
        self.refresh_from_table()
        self.save_current_student_grades()
        self.write(f"Added subject: {dialog.result[0]} - {dialog.result[1]}")

    def on_edit_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student first.")
            return
        selection = self.grades_table.selection()
        if not selection:
            messagebox.showwarning("Select a subject", "Select a subject to edit first.")
            return
        item = selection[0]
        values = self.grades_table.item(item, "values")
        dialog = GradeDialog(self, "Edit Subject / Grade", values)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.grades_table.item(item, values=dialog.result)
        self.refresh_from_table()
        self.save_current_student_grades()
        self.write(f"Modified subject: {dialog.result[0]} - {dialog.result[1]}")

    def on_delete_grade(self):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student first.")
            return
        selection = self.grades_table.selection()
        if not selection:
            messagebox.showwarning("Select a subject", "Select a subject to delete first.")
            return
        item = selection[0]
        values = self.grades_table.item(item, "values")
        if not messagebox.askyesno("Delete Subject", f"Delete {values[0]} - {values[1]}?"):
            return
        self.grades_table.delete(item)
        self.refresh_from_table()
        self.save_current_student_grades()
        self.write(f"Deleted subject: {values[0]} - {values[1]}")

    def on_save_grades(self, silent=False):
        if self.selected_student_index is None:
            messagebox.showwarning("Select a student", "Select a student before saving grades.")
            return False
        if not self.save_current_student_grades():
            return False
        if not silent:
            messagebox.showinfo("Grades saved", "Grade data has been saved for the selected student.")
            self.write("Saved grade changes to students.json.")
        return True

    def on_content_mode_changed(self):
        if self.content_mode.get() == "Grades":
            self.message_text.configure(state="disabled")
            self.message_label.configure(fg="#999999")
        else:
            self.message_text.configure(state="normal")
            self.message_label.configure(fg=INK)

    def on_channel_changed(self, _event=None):
        channel = self.channel.get()
        if channel == "Email":
            self.recipient_label.configure(text="Recipient Email:")
            self.recipient_hint.configure(text="Enter the email address where the notification should be sent.")
        elif channel == "SMS":
            self.recipient_label.configure(text="Recipient Phone:")
            self.recipient_hint.configure(text="Use an international number such as +639171234567.")
        elif channel == "Push":
            self.recipient_label.configure(text="FCM Device Token:")
            self.recipient_hint.configure(text="Enter the Firebase Cloud Messaging device registration token.")
        else:
            self.recipient_label.configure(text="WhatsApp Number:")
            self.recipient_hint.configure(text="Enter the recipient's phone number.")

    def build_message(self):
        if self.content_mode.get() == "Message Only":
            message = self.message_text.get("1.0", "end").strip()
            if not message:
                raise ValueError("Custom message must not be empty.")
            return message
        if self.selected_student_index is None:
            raise ValueError("Select a student before sending grades.")
        student = self.students[self.selected_student_index]
        grades = [tuple(row) for row in student.get("grades", [])]
        rows = [f"{code} - {subject}: {grade} (Units: {units})" for code, subject, units, grade in grades]
        total_units, weighted_average = calculate_totals(grades)
        average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"
        return (
            f"Student: {student.get('name', '')}\n"
            f"Program / Year: {student.get('program_year', '')}\n"
            f"Academic Period: {student.get('academic_period', '') or 'Not specified'}\n\n"
            "Grades:\n"
            + ("\n".join(rows) if rows else "No grade records.")
            + f"\n\nTotal Units: {total_units:g}"
            + f"\nWeighted Average: {average_text}"
        )

    def on_send(self):
        try:
            message = self.build_message()
            recipient = self.recipient.get().strip()
            service = SERVICES[self.channel.get()]()
            service.set_recipient(recipient)
            result = service.notify(message)
            self.write(result)
            messagebox.showinfo("Notification sent", result)
        except (ValueError, RuntimeError, KeyError) as exc:
            messagebox.showerror("Notification failed", str(exc))


def main():
    root = tk.Tk()
    root.title("NDMU University Notification Console")
    root.geometry("760x860")
    root.minsize(760, 760)
    root.configure(bg="white")
    app = NotificationApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
