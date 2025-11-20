import os
import tkinter as tk
from typing import Optional

DEFAULT_QR_IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "qr.png")
DEFAULT_QR_IMAGE = os.path.normpath(DEFAULT_QR_IMAGE)


class PaymentPage(tk.Frame):
    """Shows QR for payment and waits for admin approval before brewing.

    Expects the controller to expose:
      - selected_item: Optional[MenuItem]
      - show_page(name: str) -> None
      - request_payment_authorization() -> None
    """

    def __init__(self, parent: tk.Misc, controller) -> None:  # controller: CoffeeKioskApp
        super().__init__(parent)
        self.controller = controller
        self._qr_img_ref: Optional[tk.PhotoImage] = None

        self.title_var = tk.StringVar(value="สแกนเพื่อชำระเงิน")
        tk.Label(self, textvariable=self.title_var, font=("Segoe UI", 16, "bold")).pack(pady=(12, 4))

        # Price display
        self.price_var = tk.StringVar(value="ราคา: -")
        tk.Label(self, textvariable=self.price_var, font=("Segoe UI", 14)).pack(pady=(0, 8))

        self.qr_label = tk.Label(self)
        self.qr_label.pack(pady=(6, 6))

        btns = tk.Frame(self)
        btns.pack(pady=(8, 0))

        self.pay_btn = tk.Button(btns, text="ยืนยันการชำระเงิน", width=20, command=self._request_admin)
        self.pay_btn.grid(row=0, column=0, padx=6)
        self.back_btn = tk.Button(btns, text="กลับไปหน้าหลัก", width=20, command=lambda: self.controller.show_page("menu"))
        self.back_btn.grid(row=0, column=1, padx=6)

        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, fg="steelblue").pack(pady=(6, 0))

        info = ("qr.png")
        self.hint = tk.Label(self, fg="gray")
        self.hint.pack(pady=(10, 0))

    def refresh(self) -> None:
        item = getattr(self.controller, "selected_item", None)
        self.title_var.set(f"สแกนเพื่อชำระเงิน - {item.name}" if item else "สแกนเพื่อชำระเงิน")

        # Update price display if available on the selected item
        if item is not None:
            price = getattr(item, "price", None)
            if isinstance(price, (int, float)):
                self.price_var.set(f"ราคา: {price:,.2f} ฿")
            else:
                self.price_var.set("ราคา: -")
        else:
            self.price_var.set("ราคา: -")

        qr_path = os.getenv("COFFEE_QR_IMAGE", DEFAULT_QR_IMAGE)
        if os.path.exists(qr_path):
            try:
                # Try Pillow first (supports PNG/JPEG and more)
                from PIL import Image, ImageTk  # type: ignore
                with Image.open(qr_path) as im:
                    im = im.convert("RGBA")
                    im.thumbnail((300, 300), Image.LANCZOS)
                    img = ImageTk.PhotoImage(im)
                self.qr_label.configure(image=img ,text="")
                self._qr_img_ref = img
            except Exception:
                try:
                    # Fallback to Tk PhotoImage (PNG/GIF)
                    img = tk.PhotoImage(file=qr_path)
                    w, h = img.width(), img.height()
                    if w > 300 or h > 300:
                        sx = max(1, (w + 300 - 1) // 300)
                        sy = max(1, (h + 300 - 1) // 300)
                        img = img.subsample(sx, sy)
                    self.qr_label.configure(image=img,text="")
                    self._qr_img_ref = img
                except Exception:
                    self.qr_label.configure(text="Invalid QR image", image="", fg="gray")
                    self._qr_img_ref = None
        else:
            self.qr_label.configure(text="QR image not found\nqr.png (project root)", image="", fg="gray")
            self._qr_img_ref = None

    def _request_admin(self) -> None:
        self.controller.request_payment_authorization()

    def set_waiting(self, waiting: bool, note: str) -> None:
        """Enable/disable the page while awaiting admin approval."""
        state = tk.DISABLED if waiting else tk.NORMAL
        self.pay_btn.configure(state=state)
        self.back_btn.configure(state=state)
        self.status_var.set(note)
