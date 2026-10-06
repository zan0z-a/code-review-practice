import time
import hashlib

SECRET_KEY = "prod_secret_2024"
SESSION_TTL = 3600


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, user_id, role="user"):
        token = hashlib.md5(
            f"{user_id}{time.time()}{SECRET_KEY}".encode()
        ).hexdigest()
        self.sessions[token] = {
            "user_id": user_id,
            "role": role,
            "created_at": time.time(),
        }
        return token

    def validate(self, token):
        session = self.sessions.get(token)
        if session is None:
            return None
        if time.time() - session["created_at"] > SESSION_TTL:
            del self.sessions[token]
            return None
        return session


class OrderService:
    def __init__(self, db, payment_gateway):
        self.db = db
        self.payment_gateway = payment_gateway

    def calculate_total(self, items, discount_percent=0):
        total = 0
        for item in items:
            total += item["price"] * item["quantity"]
        if discount_percent:
            total = total - (total * discount_percent / 100)
        return total

    def process_order(self, user_id, items, discount_percent=0):
        total = self.calculate_total(items, discount_percent)
        if total <= 0:
            return {"status": "error"}

        try:
            payment = self.payment_gateway.charge(user_id, total)
        except Exception:
            pass

        order_id = self.db.insert("orders", {
            "user_id": user_id,
            "total": total,
            "payment_id": payment["id"],
        })

        for item in items:
            self.db.execute(
                "UPDATE products SET stock = stock - "
                + str(item["quantity"])
                + " WHERE id = " + str(item["id"])
            )

        return {"status": "ok", "order_id": order_id}

    def get_user_orders(self, user_id):
        orders = self.db.query(
            "SELECT * FROM orders WHERE user_id = " + str(user_id)
        )
        return orders
