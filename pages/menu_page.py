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

        header = tk.Frame(self, bg="#f5f5f5")
        header.pack(fill=tk.X, padx=10, pady=(8, 2))

        title = tk.Label(
            header,
            text="CPE Robot Coffee",
            font=("Segoe UI", 20, "bold"),
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

        grid_frame = tk.Frame(self, bg="#f5f5f5")
        grid_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=30)

        # มีแค่ 1 column / 1 row
        grid_frame.columnconfigure(0, weight=1, uniform="menu_col")
        grid_frame.rowconfigure(0, weight=1, uniform="menu_row")

        if self.controller.menu_items:
            item = self.controller.menu_items[0]
            card = self._build_menu_card(grid_frame, item)
            card.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

    def _build_menu_card(self, parent: tk.Misc, item: MenuItem) -> tk.Frame:
        frame = tk.Frame(
            parent,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=8,
            pady=8,
            width=360,
            height=420,  # สูงพอสำหรับรูป + ราคา + ปุ่ม
            bg="white",
        )
        frame.grid_propagate(False)

        frame.columnconfigure(0, weight=1)
        for ridx, weight in ((0, 0), (1, 0), (2, 1), (3, 0), (4, 0)):
            frame.rowconfigure(ridx, weight=weight)

        name_lbl = tk.Label(
            frame,
            text=item.name,
            font=("Segoe UI", 18, "bold"),
            bg="white",
            wraplength=280,
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
            font=("Segoe UI", 14),
            bg="white",
            fg="#444444",
        )
        price_lbl.grid(row=3, column=0, pady=(4, 2))

        btn = tk.Button(
            frame,
            text="ORDER NOW",
            font=("Segoe UI", 14, "bold"),
            bg="#2E7D32",
            fg="white",
            activebackground="#256628",
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
            ipady=10,
        )

        return frame

    # โหลดรูปภาพจาก path
    def _load_image(self, path: str) -> tk.PhotoImage | None:
        if not os.path.isfile(path):
            return None
        try:
            img = tk.PhotoImage(file=path)
            w, h = img.width(), img.height()

            max_size = 240
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
            self.busy_label.config(text=f"กำลังชง... {remaining}s", fg="orange")
        else:
            self.busy_label.config(text="Ready", fg="green")
