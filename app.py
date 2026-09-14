import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from notifications import SERVICES  # The ONLY model import.

NAVY = "#1F3864"
BAND = "#17375E"
CREAM = "#FFF2CC"
INK = "#1A1A2E"
MINT = "#CCFFCC"

BASE_DIR = Path(__file__).resolve().parent
GRADES_FILE = BASE_DIR / "grades.txt"


def parse_grades():
    if not GRADES_FILE.exists():
        raise FileNotFoundError(f"grades.txt was not found at: {GRADES_FILE}")

    lines = [
        line.strip()
        for line in GRADES_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not lines:
        raise ValueError("grades.txt is empty.")

    student_info = lines[0]
    grades = []

    for line in lines[1:]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            code, subject, units, grade = parts
            grades.append((code, subject, units, grade))
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
    rows = [
        f"{code} - {subject}: {grade} (Units: {units})"
        for code, subject, units, grade in grades
    ]
    total_units, weighted_average = calculate_totals(grades)
    average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"

    return (
        "Student: " + student_info
        + "\n\nGrades:\n"
        + "\n".join(rows)
        + f"\n\nTotal Units: {total_units:g}"
        + f"\nWeighted Average: {average_text}"
    )


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

        fields = [
            ("Course Code", self.code_var),
            ("Course Title", self.subject_var),
            ("Units", self.units_var),
            ("Grade", self.grade_var),
        ]

        for row, (label, variable) in enumerate(fields):
            tk.Label(
                self,
                text=label + ":",
                font=("Calibri", 10, "bold"),
                bg="white",
            ).grid(row=row, column=0, sticky="w", padx=(14, 8), pady=6)
            tk.Entry(
                self,
                textvariable=variable,
                font=("Calibri", 10),
                width=38,
            ).grid(row=row, column=1, padx=(0, 14), pady=6)

        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", padx=14, pady=(5, 14))

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            relief="flat",
            padx=12,
            pady=4,
        ).pack(side="right", padx=(7, 0))
        tk.Button(
            button_frame,
            text="Save",
            command=self.validate_and_save,
            bg=NAVY,
            fg="white",
            activebackground=BAND,
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=4,
        ).pack(side="right")

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

        self.result = (
            code,
            subject,
            f"{unit_value:g}",
            f"{grade_value:.2f}",
        )
        self.destroy()


class NotificationApp(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padx=14, pady=10, bg="white")
        self.columnconfigure(1, weight=1)
        self.student_info = ""
        self.grades = []

        tk.Label(
            self,
            text="NDMU University Notification Console",
            font=("Calibri", 15, "bold"),
            fg=NAVY,
            bg="white",
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        tk.Label(
            self,
            text="Factory Method - the channel varies, notify() does not.",
            font=("Calibri", 9, "italic"),
            fg="#595959",
            bg="white",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 7))

        settings = tk.LabelFrame(
            self,
            text="Notification Settings",
            font=("Calibri", 10, "bold"),
            bg="white",
            fg=BAND,
            padx=8,
            pady=6,
        )
        settings.grid(row=2, column=0, columnspan=3, sticky="ew")
        settings.columnconfigure(1, weight=1)

        tk.Label(settings, text="Send:", font=("Calibri", 10, "bold"), bg="white").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )

        self.content_mode = tk.StringVar(value="Grades")
        mode_frame = tk.Frame(settings, bg="white")
        mode_frame.grid(row=0, column=1, sticky="w")

        tk.Radiobutton(
            mode_frame,
            text="Grades",
            variable=self.content_mode,
            value="Grades",
            command=self.on_content_mode_changed,
            font=("Calibri", 10),
            bg="white",
            activebackground="white",
        ).pack(side="left")
        tk.Radiobutton(
            mode_frame,
            text="Message Only",
            variable=self.content_mode,
            value="Message Only",
            command=self.on_content_mode_changed,
            font=("Calibri", 10),
            bg="white",
            activebackground="white",
        ).pack(side="left", padx=(12, 0))

        tk.Label(settings, text="Channel:", font=("Calibri", 10, "bold"), bg="white").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(5, 0)
        )
        self.channel = tk.StringVar(value=list(SERVICES)[0])
        self.channel_box = ttk.Combobox(
            settings,
            textvariable=self.channel,
            values=list(SERVICES),
            state="readonly",
            width=18,
        )
        self.channel_box.grid(row=1, column=1, sticky="w", pady=(5, 0))
        self.channel_box.bind("<<ComboboxSelected>>", self.on_channel_changed)

        self.recipient_label = tk.Label(
            settings,
            text="Recipient Email:",
            font=("Calibri", 10, "bold"),
            bg="white",
        )
        self.recipient_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(5, 0))
        self.recipient = tk.StringVar()
        tk.Entry(settings, textvariable=self.recipient, width=52, font=("Calibri", 10)).grid(
            row=2, column=1, sticky="w", pady=(5, 0)
        )

        self.recipient_hint = tk.Label(
            settings,
            text="Enter the email address where the notification should be sent.",
            font=("Calibri", 8),
            fg="#666666",
            bg="white",
        )
        self.recipient_hint.grid(row=3, column=1, sticky="w", pady=(2, 0))

        self.message_label = tk.Label(
            self,
            text="Custom Message:",
            font=("Calibri", 10, "bold"),
            bg="white",
        )
        self.message_label.grid(row=4, column=0, sticky="nw", pady=(8, 0))

        self.message_text = tk.Text(
            self,
            height=3,
            width=64,
            font=("Calibri", 10),
            wrap="word",
            relief="solid",
            borderwidth=1,
        )
        self.message_text.grid(row=4, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 0))

        info_frame = tk.LabelFrame(
            self,
            text="Student Information",
            font=("Calibri", 9, "bold"),
            bg="white",
            fg=BAND,
            padx=8,
            pady=5,
        )
        info_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        self.student_name = tk.StringVar(value="--")
        self.program_year = tk.StringVar(value="--")
        self.academic_period = tk.StringVar(value="Not specified in grades.txt")

        for column, (label, variable) in enumerate(
            [
                ("Name", self.student_name),
                ("Program / Year", self.program_year),
                ("Academic Period", self.academic_period),
            ]
        ):
            tk.Label(info_frame, text=f"{label}:", font=("Calibri", 8, "bold"), bg="white").grid(
                row=0, column=column * 2, sticky="w", padx=(0, 4)
            )
            tk.Label(info_frame, textvariable=variable, font=("Calibri", 8), bg="white").grid(
                row=0, column=column * 2 + 1, sticky="w", padx=(0, 15)
            )

        self.grades_section = tk.Frame(self, bg="white")
        self.grades_section.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(7, 0))
        self.grades_section.columnconfigure(1, weight=1)

        self.grades_label = tk.Label(
            self.grades_section,
            text="Grades:",
            font=("Calibri", 10, "bold"),
            bg="white",
        )
        self.grades_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        self.table_frame = tk.Frame(self.grades_section, bg="white")
        self.table_frame.grid(row=0, column=1, sticky="w")

        columns = ("course_code", "course_title", "units", "grade")
        self.grades_table = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=6)
        self.grades_table.heading("course_code", text="Course Code")
        self.grades_table.heading("course_title", text="Course Title")
        self.grades_table.heading("units", text="Units")
        self.grades_table.heading("grade", text="Grade")
        self.grades_table.column("course_code", width=105, anchor="w")
        self.grades_table.column("course_title", width=260, anchor="w")
        self.grades_table.column("units", width=55, anchor="center")
        self.grades_table.column("grade", width=55, anchor="center")

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.grades_table.yview)
        self.grades_table.configure(yscrollcommand=scrollbar.set)
        self.grades_table.grid(row=0, column=0)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grades_table.bind("<Double-1>", lambda _event: self.on_edit_grade())

        grade_buttons = tk.Frame(self.grades_section, bg="white")
        grade_buttons.grid(row=2, column=1, sticky="w", pady=(5, 0))

        tk.Button(
            grade_buttons,
            text="Add Subject",
            command=self.on_add_grade,
            font=("Calibri", 9, "bold"),
            bg=NAVY,
            fg="white",
            activebackground=BAND,
            activeforeground="white",
            relief="flat",
            padx=10,
            pady=3,
        ).pack(side="left")
        tk.Button(
            grade_buttons,
            text="Edit Selected",
            command=self.on_edit_grade,
            font=("Calibri", 9),
            relief="flat",
            padx=10,
            pady=3,
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            grade_buttons,
            text="Delete Selected",
            command=self.on_delete_grade,
            font=("Calibri", 9),
            relief="flat",
            padx=10,
            pady=3,
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            grade_buttons,
            text="Save Grades",
            command=self.on_save_grades,
            font=("Calibri", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3,
        ).pack(side="left", padx=(6, 0))

        self.summary_frame = tk.Frame(self.grades_section, bg=CREAM, padx=8, pady=4)
        self.summary_frame.grid(row=3, column=1, sticky="ew", pady=(4, 0))
        self.total_units_label = tk.Label(
            self.summary_frame,
            text="Total Units: --",
            font=("Calibri", 9, "bold"),
            bg=CREAM,
            fg=BAND,
        )
        self.total_units_label.pack(side="left", padx=(0, 25))
        self.weighted_average_label = tk.Label(
            self.summary_frame,
            text="Weighted Average: --",
            font=("Calibri", 9, "bold"),
            bg=CREAM,
            fg=BAND,
        )
        self.weighted_average_label.pack(side="left")

        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=7)

        tk.Button(
            button_frame,
            text="Reload Grades",
            command=self.on_reload,
            font=("Calibri", 9),
            relief="flat",
            padx=9,
            pady=3,
        ).pack(side="left")
        tk.Button(
            button_frame,
            text="Send Notification",
            command=self.on_send,
            font=("Calibri", 9, "bold"),
            bg=NAVY,
            fg="white",
            activebackground=BAND,
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
        ).pack(side="right")
        tk.Button(
            button_frame,
            text="Clear Log",
            command=self.on_clear,
            font=("Calibri", 9),
            relief="flat",
            padx=9,
            pady=3,
        ).pack(side="right", padx=(0, 8))

        tk.Label(self, text="Delivery Log", font=("Calibri", 10, "bold"), fg=BAND, bg="white").grid(
            row=8, column=0, columnspan=3, sticky="w"
        )
        self.log = tk.Text(
            self,
            height=5,
            width=76,
            font=("Courier New", 8),
            bg=INK,
            fg=MINT,
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            state="disabled",
        )
        self.log.grid(row=9, column=0, columnspan=3, sticky="w", pady=(3, 6))

        self.proof = tk.Label(
            self,
            text="",
            font=("Calibri", 8),
            bg=CREAM,
            fg="#333333",
            justify="left",
            anchor="w",
            padx=7,
            pady=5,
            width=80,
        )
        self.proof.grid(row=10, column=0, columnspan=3, sticky="w")

        try:
            self.populate_grades_table()
        except (FileNotFoundError, ValueError) as exc:
            self.student_name.set("Unable to load grades.txt")
            self.program_year.set(str(exc))

        self.on_content_mode_changed()
        self.on_channel_changed()

    def on_channel_changed(self, _event=None) -> None:
        labels = {
            "Email": ("Recipient Email:", "Enter the email address where the notification should be sent."),
            "SMS": ("Recipient Phone:", "Use an international number such as +639171234567."),
            "Push": ("Recipient FCM ID:", "Enter the Firebase device target used by your push setup."),
            "WhatsApp": ("Recipient Phone:", "Use an international WhatsApp number such as +639171234567."),
        }
        label, hint = labels.get(self.channel.get(), ("Recipient:", "Enter the destination for this notification channel."))
        self.recipient_label.configure(text=label)
        self.recipient_hint.configure(text=hint)

    def populate_grades_table(self) -> None:
        self.student_info, self.grades = parse_grades()

        for item in self.grades_table.get_children():
            self.grades_table.delete(item)

        name = self.student_info
        program_year = "Not specified"
        if "," in self.student_info:
            name, program_year = [part.strip() for part in self.student_info.split(",", 1)]

        for code, subject, units, grade in self.grades:
            self.grades_table.insert("", "end", values=(code, subject, units, grade))

        total_units, weighted_average = calculate_totals(self.grades)
        average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"
        self.student_name.set(name)
        self.program_year.set(program_year)
        self.total_units_label.configure(text=f"Total Units: {total_units:g}")
        self.weighted_average_label.configure(text=f"Weighted Average: {average_text}")

    def refresh_from_table(self):
        self.grades = [self.grades_table.item(item, "values") for item in self.grades_table.get_children()]
        self.grades = [tuple(row) for row in self.grades]
        total_units, weighted_average = calculate_totals(self.grades)
        average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"
        self.total_units_label.configure(text=f"Total Units: {total_units:g}")
        self.weighted_average_label.configure(text=f"Weighted Average: {average_text}")

    def on_add_grade(self):
        dialog = GradeDialog(self, "Add Subject / Grade")
        self.wait_window(dialog)
        if dialog.result is None:
            return

        self.grades_table.insert("", "end", values=dialog.result)
        self.refresh_from_table()
        self.write(f"Added subject: {dialog.result[0]} - {dialog.result[1]}")
        self.on_save_grades(silent=True)

    def on_edit_grade(self):
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
        self.write(f"Modified subject: {dialog.result[0]} - {dialog.result[1]}")
        self.on_save_grades(silent=True)

    def on_delete_grade(self):
        selection = self.grades_table.selection()
        if not selection:
            messagebox.showwarning("Select a subject", "Select a subject to delete first.")
            return

        values = self.grades_table.item(selection[0], "values")
        if not messagebox.askyesno(
            "Delete Subject",
            f"Delete {values[0]} - {values[1]}?",
        ):
            return

        self.grades_table.delete(selection[0])
        self.refresh_from_table()
        self.write(f"Deleted subject: {values[0]} - {values[1]}")
        self.on_save_grades(silent=True)

    def on_save_grades(self, silent=False):
        try:
            self.refresh_from_table()
            save_grades(self.student_info, self.grades)
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return False

        if not silent:
            messagebox.showinfo("Grades saved", "Subject and grade data has been saved to grades.txt.")
            self.write("Saved grade changes to grades.txt.")
        return True

    def on_content_mode_changed(self) -> None:
        is_message_only = self.content_mode.get() == "Message Only"
        if is_message_only:
            self.message_label.configure(fg=INK)
            self.message_text.configure(state="normal", bg="white", fg="black")
            self.grades_label.configure(fg="#999999")
            self.grades_section.grid_remove()
        else:
            self.message_label.configure(fg="#999999")
            self.message_text.configure(state="disabled", bg="#F2F2F2", fg="#777777")
            self.grades_label.configure(fg=INK)
            self.grades_section.grid()

    def on_reload(self) -> None:
        try:
            self.populate_grades_table()
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Grades file error", str(exc))
            return
        self.write("Loaded grades.txt successfully.")

    def on_send(self) -> None:
        label = self.channel.get()
        recipient = self.recipient.get().strip()

        if not recipient:
            messagebox.showwarning("Recipient required", f"Enter a recipient for {label} first.")
            return

        service = SERVICES[label]()
        service.set_recipient(recipient)

        if self.content_mode.get() == "Message Only":
            message = self.message_text.get("1.0", "end").strip()
            if not message:
                messagebox.showwarning("Message required", "Enter a message first.")
                return
        else:
            try:
                message = load_grades()
            except (FileNotFoundError, ValueError) as exc:
                messagebox.showerror("Grades file error", str(exc))
                return

        try:
            line = service.notify(message)
        except ValueError as exc:
            messagebox.showwarning("Invalid message", str(exc))
            return
        except RuntimeError as exc:
            self.write(f"{label} ERROR -> {exc}")
            messagebox.showerror("Notification failed", str(exc))
            return

        self.write(line)
        self.proof.configure(
            text=(
                f"Mode: {self.content_mode.get()} | "
                f"Creator used: {type(service).__name__} | "
                f"Product built: {type(service.create_notification()).__name__}\n"
                "app.py names neither class - it only calls notify()."
            )
        )

    def on_clear(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.proof.configure(text="")

    def write(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    root.title("CSPC 103 - Factory Method Notification Console")
    root.configure(bg="white")
    root.resizable(False, False)
    root.geometry("700x760")
    NotificationApp(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
