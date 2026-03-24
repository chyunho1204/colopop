import heapq
from collections import deque

class Order:
    def __init__(self, order_id, time, side, price, quantity):
        self.order_id = order_id
        self.time = time
        self.side = side  # "BUY" or "SELL"
        self.price = price
        self.quantity = quantity

class Execution:
    def __init__(self, exec_id, price, quantity, sell_id, buy_id):
        self.exec_id = exec_id
        self.price = price
        self.quantity = quantity
        self.sell_id = sell_id
        self.buy_id = buy_id

    def __repr__(self):
        return f"[Exec {self.exec_id}] price={self.price}, qty={self.quantity}, sell={self.sell_id}, buy={self.buy_id}"


class MatchingEngine:
    def __init__(self):
        self.buy_book = []   # max heap (use -price)
        self.sell_book = []  # min heap
        self.exec_id = 1

    def process(self, order):
        executions = []

        if order.side == "BUY":
            while self.sell_book and order.quantity > 0:
                best_price, _, sell_order = self.sell_book[0]

                if best_price > order.price:
                    break

                heapq.heappop(self.sell_book)

                trade_qty = min(order.quantity, sell_order.quantity)
                executions.append(
                    Execution(self.exec_id, best_price, trade_qty,
                              sell_order.order_id, order.order_id)
                )
                self.exec_id += 1

                order.quantity -= trade_qty
                sell_order.quantity -= trade_qty

                if sell_order.quantity > 0:
                    heapq.heappush(self.sell_book,
                                   (sell_order.price, sell_order.time, sell_order))

            if order.quantity > 0:
                heapq.heappush(self.buy_book,
                               (-order.price, order.time, order))

        else:  # SELL
            while self.buy_book and order.quantity > 0:
                neg_price, _, buy_order = self.buy_book[0]
                best_price = -neg_price

                if best_price < order.price:
                    break

                heapq.heappop(self.buy_book)

                trade_qty = min(order.quantity, buy_order.quantity)
                executions.append(
                    Execution(self.exec_id, best_price, trade_qty,
                              order.order_id, buy_order.order_id)
                )
                self.exec_id += 1

                order.quantity -= trade_qty
                buy_order.quantity -= trade_qty

                if buy_order.quantity > 0:
                    heapq.heappush(self.buy_book,
                                   (-buy_order.price, buy_order.time, buy_order))

            if order.quantity > 0:
                heapq.heappush(self.sell_book,
                               (order.price, order.time, order))

        return executions
