import logging

from nameko.events import event_handler
from nameko.rpc import rpc

from products import dependencies, schemas
from products.exceptions import NotFound

logger = logging.getLogger(__name__)


class ProductsService:

    name = 'products'

    storage = dependencies.Storage()

    @rpc
    def get(self, product_id):
        logger.info(f"Fetching product with id: {product_id}")
        product = self.storage.get(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            raise NotFound(f"Product with id {product_id} not found")
        return schemas.Product().dump(product).data

    @rpc
    def list(self):
        logger.info("Listing all products")
        products = self.storage.list()
        products = list(products)
        logger.info(f"{len(products)} products found")
        return schemas.Product(many=True).dump(products).data

    @rpc
    def create(self, product):
        logger.info(f"Creating new product: {product}")
        product = schemas.Product(strict=True).load(product).data
        self.storage.create(product)
        logger.info(f"Product created successfully: {product}")

    @rpc
    def delete(self, product_id):
        logger.info(f"Deleting product with id: {product_id}")
        product = self.storage.get(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            raise NotFound(f"Product with id {product_id} not found")
        self.storage.delete(product_id)
        logger.info(f"Product {product_id} deleted successfully")

    @event_handler('orders', 'order_created')
    def handle_order_created(self, payload):
        logger.info(f"Handling new order: {payload['order']['id']}")
        for product in payload['order']['order_details']:
            logger.info(f"Decrementing stock for product {product['product_id']} by {product['quantity']}")
            self.storage.decrement_stock(
                product['product_id'], product['quantity'])
        logger.info(f"Order {payload['order']['id']} processed successfully")