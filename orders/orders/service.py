import json
from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import DatabaseSession
from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail
from orders.schemas import OrderSchema
from orders.redis_client import RedisClient

#TODO - fix cache problems. 

class OrdersService:
    name = 'orders'

    db = DatabaseSession(DeclarativeBase)
    event_dispatcher = EventDispatcher()
    redis_cache = RedisClient()
    cache_ttl = 3600

    @rpc
    def get_order(self, order_id):
        cached_order = self._get_order_from_cache(order_id)
        if cached_order:
            return cached_order

        order = self.db.query(Order).get(order_id)
        if not order:
            raise NotFound(f'Order with id {order_id} not found')

        order_data = OrderSchema().dump(order).data
        self._cache_order(order_id, order_data)
        return order_data

    @rpc
    def create_order(self, order_details):
        order = self._create_order_in_db(order_details)
        order_data = OrderSchema().dump(order).data

        self._cache_order(order_data['id'], order_data)
        self._dispatch_order_created_event(order_data)

        return order_data

    def _create_order_in_db(self, order_details):
        order = Order(
            order_details=[
                OrderDetail(
                    product_id=order_detail['product_id'],
                    price=order_detail['price'],
                    quantity=order_detail['quantity']
                )
                for order_detail in order_details
            ]
        )
        self.db.add(order)
        self.db.commit()
        return order

    def _cache_order(self, order_id, order_data):
        cache_key = self._generate_cache_key(order_id)
        order_data_json = json.dumps(order_data)
        self.redis_cache.setex(cache_key, self.cache_ttl, order_data_json)

    def _get_order_from_cache(self, order_id):
        cache_key = self._generate_cache_key(order_id)
        cached_order = self.redis_cache.get(cache_key)
        if cached_order:
            return json.loads(cached_order.decode("utf-8"))
        return None

    def _dispatch_order_created_event(self, order_data):
        self.event_dispatcher('order_created', {'order': order_data})

    def _generate_cache_key(self, order_id):
        return f'order:{order_id}'