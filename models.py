from dataclasses import dataclass


@dataclass
class MenuItem:
    id: str
    name: str
    image_path: str
    price: float = 0.0
    brew_seconds: int = 25
