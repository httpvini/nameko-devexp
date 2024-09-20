import pytest
from unittest.mock import call, patch
from nameko.exceptions import RemoteError
from orders.models import Order, OrderDetail
from orders.schemas import OrderSchema, OrderDetailSchema

#TODO - fix tests that are breaking. 

@pytest.fixture
def order(db_session):
    order = Order()
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def order_details(db_session, order):
    details = [
        OrderDetail(order=order, product_id="the_odyssey", price=99.51, quantity=1),
        OrderDetail(order=order, product_id="the_enigma", price=30.99, quantity=8)
    ]
    db_session.add_all(details)
    db_session.commit()
    return details


@patch('orders.service.OrdersService._get_order_from_cache')
@patch('orders.service.OrdersService._cache_order')
def test_get_order(mock_cache_order, mock_get_cache, orders_rpc, order):
    mock_get_cache.return_value = None
    response = orders_rpc.get_order(order.id)
    
    assert response['id'] == order.id
    mock_cache_order.assert_called_once_with(order.id, response)


@patch('orders.service.OrdersService._get_order_from_cache')
def test_get_order_from_cache(mock_get_cache, orders_rpc, order):
    cached_order = OrderSchema().dump(order).data
    mock_get_cache.return_value = cached_order

    response = orders_rpc.get_order(order.id)
    assert response == cached_order
    mock_get_cache.assert_called_once_with(order.id)


@pytest.mark.usefixtures('db_session')
def test_will_raise_when_order_not_found(orders_rpc):
    with pytest.raises(RemoteError) as err:
        orders_rpc.get_order(999)
    assert err.value.value == 'Order with id 999 not found'


@patch('orders.service.OrdersService._cache_order')
def test_can_create_order(mock_cache_order, orders_service, orders_rpc):
    order_details = [
        {'product_id': "the_odyssey", 'price': 99.99, 'quantity': 1},
        {'product_id': "the_enigma", 'price': 5.99, 'quantity': 8}
    ]
    new_order = orders_rpc.create_order(OrderDetailSchema(many=True).dump(order_details).data)

    assert new_order['id'] > 0
    assert len(new_order['order_details']) == len(order_details)
    
    mock_cache_order.assert_called_once_with(new_order['id'], new_order)

    assert [call(
        'order_created', {'order': {
            'id': new_order['id'],
            'order_details': [
                {'price': '99.99', 'product_id': "the_odyssey", 'id': 1, 'quantity': 1},
                {'price': '5.99', 'product_id': "the_enigma", 'id': 2, 'quantity': 8}
            ]}}
    )] == orders_service.event_dispatcher.call_args_list


@pytest.mark.usefixtures('db_session', 'order_details')
def test_can_update_order(orders_rpc, order):
    order_payload = OrderSchema().dump(order).data
    for order_detail in order_payload['order_details']:
        order_detail['quantity'] += 1

    updated_order = orders_rpc.update_order(order_payload)

    assert updated_order['order_details'] == order_payload['order_details']


def test_can_delete_order(orders_rpc, order, db_session):
    orders_rpc.delete_order(order.id)
    assert not db_session.query(Order).filter_by(id=order.id).count()