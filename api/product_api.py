import requests


class ProductAPIClient:
    API_URL = "https://fakestoreapi.com"

    def get_product(self, p_id):
        return requests.get(
            f"{self.API_URL}/products/{p_id}",
        ).json()

    def get_product_list(self):
        return requests.get(
            f"{self.API_URL}/products",
        ).json()