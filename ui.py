"""Tkinter presentation layer for GestureOS."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import cv2
from PIL import Image, ImageTk


class GestureOSUI:
    """Owns widgets only; application logic stays in main.py."""

    def __init__(self, on_start_stop: Callable[[], None], on_exit: Callable[[], None],
                 on_settings: Callable[[], None], on_voice: Callable[[bool], None],
                 on_mouse: Callable[[bool], None]) -> None:
        self.root = tk.Tk()
        self.root.title("GestureOS")
        self.root.geometry("900x650")
        self.root.minsize(760, 560)
        self.root.configure(bg="#18202a")
        self.root.protocol("WM_DELETE_WINDOW", on_exit)
        self._photo = None
        self._on_start_stop, self._on_settings = on_start_stop, on_settings
        self.voice_enabled, self.mouse_enabled = tk.BooleanVar(), tk.BooleanVar(value=True)
        self._build(on_exit, on_voice, on_mouse)

    def _build(self, on_exit: Callable[[], None], on_voice: Callable[[bool], None], on_mouse: Callable[[bool], None]) -> None:
        main = tk.Frame(self.root, bg="#18202a", padx=16, pady=16)
        main.pack(fill="both", expand=True)
        self.preview = tk.Label(main, text="Camera stopped", bg="#0e131a", fg="#a9b7c6", font=("Segoe UI", 16))
        self.preview.grid(row=0, column=0, rowspan=8, sticky="nsew", padx=(0, 16))
        main.columnconfigure(0, weight=1)
        for row in range(8): main.rowconfigure(row, weight=1)
        self.status = {name: tk.StringVar(value=value) for name, value in {
            "FPS": "0", "Gesture": "No hand", "Voice": "—", "Action": "Stopped"}.items()}
        for row, (name, value) in enumerate(self.status.items()):
            tk.Label(main, text=name.upper(), bg="#18202a", fg="#7f9bb3", anchor="w").grid(row=row, column=1, sticky="ew")
            tk.Label(main, textvariable=value, bg="#223041", fg="white", anchor="w", padx=10).grid(row=row, column=2, sticky="ew", pady=3)
        self.start_button = tk.Button(main, text="Start Detection", command=self._on_start_stop, bg="#42b883", fg="white")
        self.start_button.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(14, 3))
        tk.Checkbutton(main, text="Enable Voice", variable=self.voice_enabled, command=lambda: on_voice(self.voice_enabled.get()), bg="#18202a", fg="white", selectcolor="#223041").grid(row=5, column=1, columnspan=2, sticky="w")
        tk.Checkbutton(main, text="Enable Mouse", variable=self.mouse_enabled, command=lambda: on_mouse(self.mouse_enabled.get()), bg="#18202a", fg="white", selectcolor="#223041").grid(row=6, column=1, columnspan=2, sticky="w")
        tk.Button(main, text="Settings", command=self._on_settings).grid(row=7, column=1, sticky="ew", pady=3)
        tk.Button(main, text="Exit", command=on_exit).grid(row=7, column=2, sticky="ew", pady=3)

    def show_frame(self, frame) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb).resize((600, 450))
        self._photo = ImageTk.PhotoImage(image)
        self.preview.configure(image=self._photo, text="")

    def update_status(self, fps: float, gesture: str, action: str, voice: str | None = None) -> None:
        self.status["FPS"].set(f"{fps:.1f}")
        self.status["Gesture"].set(gesture)
        self.status["Action"].set(action)
        if voice:
            self.status["Voice"].set(voice)

    def set_running(self, running: bool) -> None:
        self.start_button.configure(text="Stop Detection" if running else "Start Detection")

    def show_settings(self, settings: dict[str, object]) -> None:
        messagebox.showinfo("GestureOS Settings", "\n".join(f"{key}: {value}" for key, value in settings.items()))
