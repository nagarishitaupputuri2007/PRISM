import json
from pathlib import Path
from typing import Any


PRODUCT_FILE = (
    Path(__file__).parent
    / "known_products.json"
)


def load_products() -> dict[str, Any]:

    with open(
        PRODUCT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


PRODUCTS = load_products()


def get_known_product(
    product_name: str
) -> dict[str, Any] | None:

    return PRODUCTS.get(
        product_name.lower()
    )

def is_known_product(
    product_name: str
) -> bool:

    return (
        product_name.lower()
        in PRODUCTS
    )

def is_known_product(
    product_name: str
) -> bool:

    return (
        product_name.lower()
        in PRODUCTS
    )