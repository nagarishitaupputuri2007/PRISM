import json
from pathlib import Path


PRODUCT_FILE = (
    Path(__file__).parent
    / "known_products.json"
)


def load_products() -> dict:

    with open(
        PRODUCT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


PRODUCTS = load_products()


def get_known_product(
    product_name: str
):

    return PRODUCTS.get(
        product_name.lower()
    )