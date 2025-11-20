import tkinter as tk
from tkinter import ttk
from typing import Optional


class CountdownPage(tk.Frame):
    """
    หน้าจอนับถอยหลังขณะชงกาแฟ

    controller ที่ส่งเข้ามาต้องมีเมธอด:
      - show_page(name: str) -> None
      - on_countdown_update(remaining: int, total: int) -> None  (มีหรือไม่มีก็ได้ ใช้เช็คด้วย hasattr)
    """

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, bg="#f5f5f5")
        self.controller = controller
        self.remaining = 0
        self.total = 1
        self._after_id: Optional[str] = None

        # ===== Title =====
        tk.Label(
            self,
            text="กำลังชงกาแฟ",
            font=("Segoe UI", 16, "bold"),
            bg="#f5f5f5",
        ).pack(pady=(16, 8))

        # ===== ตัวเลขเวลา =====
        self.time_var = tk.StringVar(value="00s")
        tk.Label(
            self,
            textvariable=self.time_var,
            font=("Consolas", 28, "bold"),
            bg="#f5f5f5",
        ).pack(pady=(4, 12))

        # ===== Progress bar =====
        self.progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            length=360,
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(pady=(6, 10))

        # ===== ปุ่มกลับหน้าหลัก =====
        tk.Button(
            self,
            text="กลับไปหน้าหลัก",
            font=("Segoe UI", 11),
            command=lambda: self.controller.show_page("menu"),
        ).pack(pady=(10, 0))

    # ------------------------------------------------------------------ #
    #   เริ่มนับถอยหลัง
    # ------------------------------------------------------------------ #
    def start(self, seconds: int) -> None:
        """เริ่มนับถอยหลังใหม่ด้วยเวลาที่กำหนด (วินาที)"""
        self.cancel()  # ยกเลิกของเก่า (ถ้ามี)
        self.total = max(1, int(seconds))
        self.remaining = self.total

        # อัปเดต UI รอบแรก
        self._update_ui()

        # แจ้ง controller ว่าเริ่มชงแล้ว
        if hasattr(self.controller, "on_countdown_update"):
            self.controller.on_countdown_update(self.remaining, self.total)  # type: ignore[attr-defined]

        # เริ่ม tick ทุก 1 วินาที
        self._after_id = self.after(1000, self._tick)

    # ------------------------------------------------------------------ #
    #   หนึ่ง tick ต่อ 1 วินาที
    # ------------------------------------------------------------------ #
    def _tick(self) -> None:
        # ถ้าจบแล้ว
        if self.remaining <= 0:
            self.remaining = 0
            self._update_ui()
            if hasattr(self.controller, "on_countdown_update"):
                self.controller.on_countdown_update(0, self.total)  # type: ignore[attr-defined]
            # กลับหน้าเมนูอัตโนมัติ
            self.controller.show_page("menu")
            self._after_id = None
            return

        # ลดเวลา
        self.remaining -= 1
        self._update_ui()

        # แจ้ง controller ให้ไปอัปเดตหัวมุมขวาของเมนู
        if hasattr(self.controller, "on_countdown_update"):
            self.controller.on_countdown_update(self.remaining, self.total)  # type: ignore[attr-defined]

        # นัดตัวเองอีกครั้งใน 1 วินาที
        self._after_id = self.after(1000, self._tick)

    # ------------------------------------------------------------------ #
    #   อัปเดต label + progress bar
    # ------------------------------------------------------------------ #
    def _update_ui(self) -> None:
        self.time_var.set(f"{self.remaining:02d}s")
        pct = int(100 * (self.total - self.remaining) / self.total) if self.total > 0 else 0
        self.progress["value"] = pct

    # ------------------------------------------------------------------ #
    #   ยกเลิกนับถอยหลัง (ใช้ตอนเปลี่ยนหน้า/เริ่มรอบใหม่)
    # ------------------------------------------------------------------ #
    def cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.remaining = 0
        self.total = 1
        self.progress["value"] = 0
        self.time_var.set("00s")
