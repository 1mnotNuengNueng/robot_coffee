# pages/menu_page.py
import os
import tkinter as tk
from typing import List
from models import MenuItem

ASSETS_DIR = os.path.dirname(os.path.dirname(__file__))


class MenuPage(tk.Frame):
    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, bg="#f5f5f5")
        self.controller = controller
        self._images_cache: List[tk.PhotoImage] = []

        # ==== ส่วนหัวด้านบนไว้แสดงสถานะเครื่องกำลังชง ====
        header = tk.Frame(self, bg="#f5f5f5")
        header.pack(fill=tk.X, padx=10, pady=(8, 2))

        title = tk.Label(
            header,
            text="Robot Coffee Kiosk",
            font=("Segoe UI", 16, "bold"),
            bg="#f5f5f5",
            fg="#333333",
        )
        title.pack(side=tk.LEFT)

        self.busy_label = tk.Label(
            header,
            text="Ready",
            font=("Segoe UI", 11),
            bg="#f5f5f5",
            fg="green",
        )
        self.busy_label.pack(side=tk.RIGHT)

        # ==== พื้นที่วางการ์ดเมนู ====
        grid_frame = tk.Frame(self, bg="#f5f5f5")
        grid_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # ให้ column/row ของ grid นี้มีขนาด uniform กัน
        for c in range(2):
            grid_frame.columnconfigure(c, weight=1, uniform="menu_col")
        for r in range(2):
            grid_frame.rowconfigure(r, weight=1, uniform="menu_row")

        # สร้างการ์ดจาก controller.menu_items
        for idx, item in enumerate(self.controller.menu_items):
            r, c = divmod(idx, 2)
            card = self._build_menu_card(grid_frame, item)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

    # =====================================================================
    #   สร้าง card แต่ละใบให้ขนาดเท่ากัน + ปุ่ม ORDER NOW เท่ากัน
    # =====================================================================
    def _build_menu_card(self, parent: tk.Misc, item: MenuItem) -> tk.Frame:
        frame = tk.Frame(
            parent,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=8,
            pady=8,
            width=230,
            height=330,   # << เพิ่มความสูง (เดิม 260) ให้พอสำหรับรูป + ราคา + ปุ่ม
            bg="white",
        )
        frame.grid_propagate(False)  # ยังใช้ได้อยู่ แต่ตอนนี้ความสูงพอแล้ว

        frame.columnconfigure(0, weight=1)
        for ridx, weight in ((0, 0), (1, 0), (2, 1), (3, 0), (4, 0)):
            frame.rowconfigure(ridx, weight=weight)

        name_lbl = tk.Label(
            frame,
            text=item.name,
            font=("Segoe UI", 12, "bold"),
            bg="white",
            wraplength=180,
            justify="center",
        )
        name_lbl.grid(row=0, column=0, pady=(4, 2), sticky="n")

        img_label = tk.Label(frame, bg="white")
        img_label.grid(row=1, column=0, pady=(2, 2))

        img = self._load_image(item.image_path)
        if img is not None:
            img_label.configure(image=img)
            self._images_cache.append(img)
        else:
            img_label.configure(text="No Image", fg="gray", bg="white")

        price_lbl = tk.Label(
            frame,
            text=f"{item.price:,.2f} ฿",
            font=("Segoe UI", 11),
            bg="white",
            fg="#444444",
        )
        price_lbl.grid(row=3, column=0, pady=(4, 2))

        btn = tk.Button(
            frame,
            text="ORDER NOW",
            font=("Segoe UI", 11, "bold"),
            bg="#ff9800",
            fg="white",
            activebackground="#ffa733",
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda it=item: self.controller.start_payment(it),
        )
        btn.grid(
            row=4,
            column=0,
            pady=(6, 2),
            sticky="ew",
            ipady=6,   # สูงเท่ากันทุกปุ่ม
        )

        return frame


    # โหลดรูปภาพจาก path
    def _load_image(self, path: str) -> tk.PhotoImage | None:
        if not os.path.isfile(path):
            return None
        try:
            img = tk.PhotoImage(file=path)
            w, h = img.width(), img.height()

            # ให้รูปไม่เกิน 110x110 จะได้เหลือที่ให้ price + button
            max_size = 110
            if w > max_size or h > max_size:
                scale = max(w / max_size, h / max_size)
                subsample = int(scale) if scale > 1 else 1
                img = img.subsample(subsample, subsample)

            return img
        except Exception:
            return None


    # เมธอดนี้ถูกเรียกจาก app.on_countdown_update()
    def set_busy_status(self, remaining: int, total: int) -> None:
        if remaining > 0 and total > 0:
            self.busy_label.config(
                text=f"กำลังชง... {remaining}s",
                fg="orange"
            )
        else:
            self.busy_label.config(
                text="Ready",
                fg="green"
            )