import re
import subprocess
import os
import tkinter as tk
from datetime import datetime

DEFAULT_HOST = "khamenei.ir"
LOG_FILE = "internet_log.txt"


def ping_target(target: str) -> tuple[str, str, str]:
    """Ping the target once and return status, ping value, and raw output."""
    try:
        # On Windows, prevent spawning a visible console window for the ping subprocess
        run_kwargs = {
            "capture_output": True,
            "text": True,
            "errors": "ignore",
        }
        if os.name == "nt":
            run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(["ping", "-n", "1", target], **run_kwargs)
    except Exception as exc:
        return "off", "N/A", f"Ping failed: {exc}"

    status = "on" if result.returncode == 0 else "off"
    ping_output = result.stdout
    ping_match = re.search(r"time[=<]([0-9]+)ms", ping_output)
    ping_value = f"{ping_match.group(1)}ms" if ping_match else "N/A"
    return status, ping_value, ping_output


class SaeedPingApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("saeed ping")
        self.root.configure(bg="black")
        self.root.attributes("-alpha", 0.95)
        self.root.geometry("620x420")
        self.root.resizable(False, False)

        self.is_monitoring = False
        self.monitor_job = None

        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        label = tk.Label(
            frame,
            text="Custom host / IP (optional):",
            fg="white",
            bg="black",
            font=("Segoe UI", 10, "bold")
        )
        label.grid(row=0, column=0, sticky="w")

        self.host_entry = tk.Entry(frame, width=36, fg="white", bg="#222222", insertbackground="white")
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.grid(row=1, column=0, sticky="w", pady=(4, 12))

        button_frame = tk.Frame(frame, bg="black")
        button_frame.grid(row=1, column=1, sticky="ne", padx=(12, 0))

        run_button = tk.Button(
            button_frame,
            text="Ping Now",
            command=self.ping_now,
            width=12,
            bg="#444444",
            fg="white",
            activebackground="#666666",
            activeforeground="white"
        )
        run_button.pack(side="top", pady=(0, 8))

        self.monitor_button = tk.Button(
            button_frame,
            text="Start Monitor",
            command=self.toggle_monitor,
            width=12,
            bg="#444444",
            fg="white",
            activebackground="#666666",
            activeforeground="white"
        )
        self.monitor_button.pack(side="top")

        self.log_text = tk.Text(
            frame,
            height=18,
            width=70,
            bg="#111111",
            fg="white",
            insertbackground="white",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#333333",
            state="disabled"
        )
        self.log_text.grid(row=2, column=0, columnspan=2, pady=(12, 0), sticky="nsew")

        self.log_text.tag_configure("status_on", foreground="#7CFC00")
        self.log_text.tag_configure("status_off", foreground="#FF6B6B")
        self.log_text.tag_configure("ping_good", foreground="#7CFC00")
        self.log_text.tag_configure("ping_warn", foreground="#FFD700")
        self.log_text.tag_configure("ping_bad", foreground="#FF6B6B")

        scrollbar = tk.Scrollbar(frame, command=self.log_text.yview)
        scrollbar.grid(row=2, column=2, sticky="ns", pady=(12, 0))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        info_label = tk.Label(
            frame,
            text="Enter a custom host/IP and press Ping Now. The app clears old logs for each new command.",
            fg="#bbbbbb",
            bg="black",
            font=("Segoe UI", 9)
        )
        info_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def log_message(self, message: str, tags: list[str] | None = None) -> None:
        self.log_text.configure(state="normal")
        if tags:
            self.log_text.insert("end", message + "\n", tuple(tags))
        else:
            self.log_text.insert("end", message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def ping_now(self) -> None:
        self.clear_log()
        self._run_ping_cycle()

    def toggle_monitor(self) -> None:
        if self.is_monitoring:
            self.stop_monitor()
        else:
            self.clear_log()
            self.is_monitoring = True
            self.monitor_button.configure(text="Stop Monitor")
            self._run_ping_cycle()

    def stop_monitor(self) -> None:
        self.is_monitoring = False
        if self.monitor_job is not None:
            self.root.after_cancel(self.monitor_job)
            self.monitor_job = None
        self.monitor_button.configure(text="Start Monitor")
        self.log_message("Monitoring stopped.")

    def _run_ping_cycle(self) -> None:
        target = self.host_entry.get().strip() or DEFAULT_HOST
        status, ping_value, raw_output = ping_target(target)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_tag = "status_on" if status == "on" else "status_off"
        ping_ms = None
        ping_tag = "ping_bad"

        if ping_value != "N/A":
            try:
                ping_ms = int(ping_value.replace("ms", ""))
            except ValueError:
                ping_ms = None

        if ping_ms is not None:
            if ping_ms <= 500:
                ping_tag = "ping_good"
            elif ping_ms <= 800:
                ping_tag = "ping_warn"
            else:
                ping_tag = "ping_bad"

        log_line = f"[{now}] {target} -> status: "
        self.log_text.configure(state="normal")
        self.log_text.insert("end", log_line)
        self.log_text.insert("end", status, status_tag)
        self.log_text.insert("end", ", ping: ")
        self.log_text.insert("end", ping_value, ping_tag)
        self.log_text.insert("end", "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(f"[{now}] {target} -> status: {status}, ping: {ping_value}\n")

        if self.is_monitoring:
            self.monitor_job = self.root.after(5000, self._run_ping_cycle)


if __name__ == "__main__":
    root = tk.Tk()
    app = SaeedPingApp(root)
    root.mainloop()
