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
    """Read grades.txt and return student info and structured grade rows."""
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
        elif len(parts) == 3:
            code, subject_with_units, grade = parts
            tokens = subject_with_units.rsplit(maxsplit=1)
            if len(tokens) == 2 and tokens[1].replace(".", "", 1).isdigit():
                subject, units = tokens
            else:
                subject = subject_with_units
                units = "-"
        else:
            grades.append((line, "", "", ""))
            continue

        grades.append((code, subject, units, grade))

    return student_info, grades


def calculate_totals(grades):
    """Return total units and weighted average for valid numeric grade rows."""
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
    """Read grades.txt and convert it into the notification message."""
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


class NotificationApp(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padx=16, pady=14, bg="white")

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
            font=("Calibri", 10, "italic"),
            fg="#595959",
            bg="white",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        tk.Label(self, text="Channel:", font=("Calibri", 11), bg="white").grid(
            row=2, column=0, sticky="w"
        )

        self.channel = tk.StringVar(value=list(SERVICES)[0])
        ttk.Combobox(
            self,
            textvariable=self.channel,
            values=list(SERVICES),
            state="readonly",
            width=18,
        ).grid(row=2, column=1, sticky="w", padx=(8, 0))

        tk.Label(self, text="Email Recipient:", font=("Calibri", 11), bg="white").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )

        self.recipient = tk.StringVar()
        tk.Entry(
            self,
            textvariable=self.recipient,
            width=52,
            font=("Calibri", 11),
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(10, 0))

        info_frame = tk.LabelFrame(
            self,
            text="Student Information",
            font=("Calibri", 10, "bold"),
            bg="white",
            fg=BAND,
            padx=10,
            pady=7,
        )
        info_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))

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
            tk.Label(
                info_frame,
                text=f"{label}:",
                font=("Calibri", 9, "bold"),
                bg="white",
            ).grid(row=0, column=column * 2, sticky="w", padx=(0, 5))
            tk.Label(
                info_frame,
                textvariable=variable,
                font=("Calibri", 9),
                bg="white",
            ).grid(row=0, column=column * 2 + 1, sticky="w", padx=(0, 18))

        tk.Label(self, text="Grades from grades.txt:", font=("Calibri", 11), bg="white").grid(
            row=5, column=0, sticky="nw", pady=(10, 0)
        )

        table_frame = tk.Frame(self, bg="white")
        table_frame.grid(row=5, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(10, 0))

        columns = ("course_code", "course_title", "units", "grade")
        self.grades_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=9,
        )
        self.grades_table.heading("course_code", text="Course Code")
        self.grades_table.heading("course_title", text="Course Title")
        self.grades_table.heading("units", text="Units")
        self.grades_table.heading("grade", text="Grade")

        self.grades_table.column("course_code", width=125, anchor="w")
        self.grades_table.column("course_title", width=300, anchor="w")
        self.grades_table.column("units", width=65, anchor="center")
        self.grades_table.column("grade", width=65, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.grades_table.yview)
        self.grades_table.configure(yscrollcommand=scrollbar.set)
        self.grades_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        summary_frame = tk.Frame(self, bg=CREAM, padx=10, pady=7)
        summary_frame.grid(row=6, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(6, 0))

        self.total_units_label = tk.Label(
            summary_frame,
            text="Total Units: --",
            font=("Calibri", 10, "bold"),
            bg=CREAM,
            fg=BAND,
        )
        self.total_units_label.grid(row=0, column=0, sticky="w", padx=(0, 30))

        self.weighted_average_label = tk.Label(
            summary_frame,
            text="Weighted Average: --",
            font=("Calibri", 10, "bold"),
            bg=CREAM,
            fg=BAND,
        )
        self.weighted_average_label.grid(row=0, column=1, sticky="w")

        tk.Button(
            self,
            text="Reload Grades",
            command=self.on_reload,
            font=("Calibri", 10),
            relief="flat",
            padx=10,
            pady=5,
        ).grid(row=7, column=1, sticky="w", padx=(8, 0), pady=12)

        tk.Button(
            self,
            text="Send Notification",
            command=self.on_send,
            font=("Calibri", 10, "bold"),
            bg=NAVY,
            fg="white",
            activebackground=BAND,
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
        ).grid(row=7, column=2, sticky="w", pady=12)

        tk.Button(
            self,
            text="Clear Log",
            command=self.on_clear,
            font=("Calibri", 10),
            relief="flat",
            padx=10,
            pady=5,
        ).grid(row=8, column=2, sticky="w", pady=(0, 12))

        tk.Label(
            self,
            text="Delivery Log",
            font=("Calibri", 11, "bold"),
            fg=BAND,
            bg="white",
        ).grid(row=9, column=0, columnspan=3, sticky="w")

        self.log = tk.Text(
            self,
            height=10,
            width=76,
            font=("Courier New", 10),
            bg=INK,
            fg=MINT,
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            state="disabled",
        )
        self.log.grid(row=10, column=0, columnspan=3, sticky="w", pady=(4, 10))

        self.proof = tk.Label(
            self,
            text="",
            font=("Calibri", 10),
            bg=CREAM,
            fg="#333333",
            justify="left",
            anchor="w",
            padx=10,
            pady=8,
            width=74,
        )
        self.proof.grid(row=11, column=0, columnspan=3, sticky="w")

        try:
            self.populate_grades_table()
        except (FileNotFoundError, ValueError) as exc:
            self.student_name.set("Unable to load grades.txt")
            self.program_year.set(str(exc))

    def populate_grades_table(self) -> None:
        student_info, grades = parse_grades()

        for item in self.grades_table.get_children():
            self.grades_table.delete(item)

        name = student_info
        program_year = "Not specified"
        if "," in student_info:
            name, program_year = [part.strip() for part in student_info.split(",", 1)]

        for code, subject, units, grade in grades:
            self.grades_table.insert("", "end", values=(code, subject, units, grade))

        total_units, weighted_average = calculate_totals(grades)
        average_text = f"{weighted_average:.2f}" if weighted_average is not None else "N/A"

        self.student_name.set(name)
        self.program_year.set(program_year)
        self.total_units_label.configure(text=f"Total Units: {total_units:g}")
        self.weighted_average_label.configure(text=f"Weighted Average: {average_text}")

    def on_reload(self) -> None:
        try:
            self.populate_grades_table()
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Grades file error", str(exc))
            return

        self.write("Loaded grades.txt successfully.")

    def on_send(self) -> None:
        label = self.channel.get()
        service = SERVICES[label]()

        recipient = self.recipient.get().strip()
        if label == "Email" and not recipient:
            messagebox.showwarning("Recipient required", "Enter an email recipient first.")
            return

        if label == "Email":
            import os
            os.environ["BREVO_RECIPIENT_EMAIL"] = recipient

        message = load_grades()

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
    NotificationApp(root).pack()
    root.mainloop()


if __name__ == "__main__":
    main()
