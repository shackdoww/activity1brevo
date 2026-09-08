import tkinter as tk
from tkinter import messagebox, ttk

from notifications import SERVICES  # The ONLY model import.

NAVY = "#1F3864"
BAND = "#17375E"
CREAM = "#FFF2CC"
INK = "#1A1A2E"
MINT = "#CCFFCC"


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

        tk.Label(self, text="Message:", font=("Calibri", 11), bg="white").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )

        self.message = tk.StringVar(
            value="Grades are now viewable in the portal."
        )
        tk.Entry(
            self,
            textvariable=self.message,
            width=52,
            font=("Calibri", 11),
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(10, 0))

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
        ).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=12)

        tk.Button(
            self,
            text="Clear Log",
            command=self.on_clear,
            font=("Calibri", 10),
            relief="flat",
            padx=10,
            pady=5,
        ).grid(row=4, column=2, sticky="w", pady=12)

        tk.Label(
            self,
            text="Delivery Log",
            font=("Calibri", 11, "bold"),
            fg=BAND,
            bg="white",
        ).grid(row=5, column=0, columnspan=3, sticky="w")

        self.log = tk.Text(
            self,
            height=12,
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
        self.log.grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 10))

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
        self.proof.grid(row=7, column=0, columnspan=3, sticky="w")

    def on_send(self) -> None:
        label = self.channel.get()
        service = SERVICES[label]()

        try:
            line = service.notify(self.message.get())
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
