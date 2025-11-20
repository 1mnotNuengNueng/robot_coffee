import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

# Import shared model and pages
from models import MenuItem
from pages.menu_page import MenuPage
from pages.payment_page import PaymentPage
from pages.countdown_page import CountdownPage

# Reuse the socket sender and defaults from socket_code.py
try:
    from socket_code import SocketSender, HOST, PORT, TIMEOUT
except Exception:  # Fallback if file not yet present
    HOST = os.getenv("ROBOT_COFFEE_HOST", "127.0.0.1")
    PORT = int(os.getenv("ROBOT_COFFEE_PORT", "50117"))
    TIMEOUT = float(os.getenv("ROBOT_COFFEE_TIMEOUT", "3.0"))

    class SocketSender:  # type: ignore
        def __init__(self, host: str, port: int, timeout: float = 3.0) -> None:
            import socket

            self.host = host
            self.port = port
            self.timeout = timeout
            self._socket_mod = socket

        def send(self, message: str) -> None:
            with self._socket_mod.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall(message.encode("utf-8"))


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "images")

class CoffeeKioskApp(tk.Tk):
    def __init__(self, sender: SocketSender, menu_items: List[MenuItem]) -> None:  # type: ignore[name-defined]
        super().__init__()
        self.sender = sender
        self.menu_items = menu_items
        self.selected_item: Optional[MenuItem] = None
        self.waiting_for_admin = False

        # Window setup (customer window)
        self.title("Robot Coffee")
        self.geometry("520x600")
        self.resizable(False, False)

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.pages = {
            "menu": MenuPage(container, self),
            "payment": PaymentPage(container, self),
            "countdown": CountdownPage(container, self),
        }
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page("menu")
        self.admin_window = AdminWindow(self)

    def show_page(self, name: str) -> None:
        # ไม่ต้อง cancel countdown ที่นี่แล้ว
        page = self.pages[name]
        page.lift()

        # Refresh dynamic pages
        if name == "payment":
            self.pages["payment"].refresh()  # type: ignore[attr-defined]


    def on_countdown_update(self, remaining: int, total: int) -> None:
        """Sync brewing countdown state to the menu page."""
        # แค่ส่งต่อไปให้ MenuPage อัปเดตข้อความ "Ready / กำลังชง...xxs"
        self.pages["menu"].set_busy_status(remaining, total)  # type: ignore[attr-defined]


    def start_payment(self, item: MenuItem) -> None:
        self.selected_item = item
        self.waiting_for_admin = False
        self.admin_window.clear_request()
        self.show_page("payment")
        self.pages["payment"].set_waiting(False, "")  # type: ignore[attr-defined]

    def request_payment_authorization(self) -> None:
        """Customer asks the admin to confirm the payment before brewing."""
        item = self.selected_item
        if item is None:
            messagebox.showwarning("No selection", "Please pick a drink first.")
            return
        if self.waiting_for_admin:
            return

        self.waiting_for_admin = True
        self.pages["payment"].set_waiting(True, "Waiting for admin confirmation...")  # type: ignore[attr-defined]
        self.admin_window.show_request(item)

    def on_payment_confirmed(self) -> None:
        item = self.selected_item
        if not item:
            return

        self.waiting_for_admin = False
        self.pages["payment"].set_waiting(False, "Approved by admin. Brewing now...")  # type: ignore[attr-defined]
        self.admin_window.clear_request(status="Approved")

        # Attempt to send the selection over socket
        try:
            self.sender.send(item.id)
        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                (
                    f"Failed to send '{item.id}' to {self.sender.host}:{self.sender.port}\n\n"  # type: ignore[attr-defined]
                    f"{e}"
                ),
            )
        # Proceed to countdown regardless; user can still receive their coffee
        self.show_page("countdown")
        self.pages["countdown"].start(item.brew_seconds)  # type: ignore[attr-defined]

    def on_payment_rejected(self) -> None:
        """Admin rejected or cancelled the payment."""
        if not self.waiting_for_admin:
            return
        self.waiting_for_admin = False
        self.pages["payment"].set_waiting(False, "Admin rejected the payment.")  # type: ignore[attr-defined]
        self.admin_window.clear_request(status="Rejected")
        messagebox.showinfo("Payment not approved", "Please try again or choose another drink.")


class AdminWindow(tk.Toplevel):
    """Secondary window for staff to approve or reject orders."""

    def __init__(self, controller: CoffeeKioskApp) -> None:
        super().__init__(controller)
        self.controller = controller
        self.title("Robot Coffee - Admin")
        self.geometry("420x260")
        self.resizable(False, False)

        tk.Label(self, text="Admin Console", font=("Segoe UI", 14, "bold")).pack(pady=(10, 6))

        info = tk.Frame(self, padx=10, pady=6)
        info.pack(fill=tk.X)

        tk.Label(info, text="Pending drink:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(info, text="Price:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w")

        self.item_var = tk.StringVar(value="-")
        self.price_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="Waiting for customer order.")

        tk.Label(info, textvariable=self.item_var, anchor="w").grid(row=0, column=1, sticky="w", padx=(6, 0))
        tk.Label(info, textvariable=self.price_var, anchor="w").grid(row=1, column=1, sticky="w", padx=(6, 0))

        tk.Label(self, textvariable=self.status_var, fg="steelblue").pack(pady=(4, 8))

        btns = tk.Frame(self, pady=8)
        btns.pack()
        self.approve_btn = tk.Button(btns, text="Approve & brew", width=16, command=self._approve, state=tk.DISABLED)
        self.reject_btn = tk.Button(btns, text="Reject", width=10, command=self._reject, state=tk.DISABLED)
        self.approve_btn.grid(row=0, column=0, padx=6)
        self.reject_btn.grid(row=0, column=1, padx=6)

        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.lift()

    def show_request(self, item: MenuItem) -> None:
        self.item_var.set(item.name)
        self.price_var.set(f"{item.price:,.2f}")
        self.status_var.set("Customer waiting for approval.")
        self.approve_btn.config(state=tk.NORMAL)
        self.reject_btn.config(state=tk.NORMAL)
        self.deiconify()
        self.lift()

    def clear_request(self, status: str = "Waiting for customer order.") -> None:
        self.item_var.set("-")
        self.price_var.set("-")
        self.status_var.set(status)
        self.approve_btn.config(state=tk.DISABLED)
        self.reject_btn.config(state=tk.DISABLED)

    def _approve(self) -> None:
        self.controller.on_payment_confirmed()

    def _reject(self) -> None:
        self.controller.on_payment_rejected()

    def _handle_close(self) -> None:
        # Keep the admin window available; hide instead of closing.
        self.withdraw()


def default_menu() -> List[MenuItem]:
    # Default 4-menu configuration; replace image files with your own.
    return [
        MenuItem(id="coffee1", name="บราซิล", image_path=os.path.join(ASSETS_DIR, "brazilain.png"), price=19.0, brew_seconds=25),
        MenuItem(id="coffee2", name="อราบิก้า", image_path=os.path.join(ASSETS_DIR, "arabica.webp"), price=19.0, brew_seconds=25),
        MenuItem(id="coffee3", name="ผสม", image_path=os.path.join(ASSETS_DIR, "mixed.jpg"), price=19.0, brew_seconds=25),
        MenuItem(id="coffee4", name="น้ำแข็ง", image_path=os.path.join(ASSETS_DIR, "ice.webp"), price=19.0, brew_seconds=25),
    ]


def main() -> None:
    sender = SocketSender(HOST, PORT, TIMEOUT)  # type: ignore[name-defined]
    app = CoffeeKioskApp(sender, default_menu())
    app.mainloop()


if __name__ == "__main__":
    main()
