import pickle
import datetime
import os


class Ticket:
    def __init__(self, ticket_type="", date="", quantity=0, price=0, qr=""):
        self.ticket_type = ticket_type
        self.date = date
        self.quantity = quantity
        self.price = price
        self.qr = qr

    def __str__(self):
        return f"{self.ticket_type} | {self.date} | {self.quantity} шт."

    def to_dict(self):
        return {
            'ticket_type': self.ticket_type,
            'date': self.date,
            'quantity': self.quantity,
            'price': self.price,
            'qr': self.qr,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ticket_type=data.get('ticket_type', ''),
            date=data.get('date', ''),
            quantity=data.get('quantity', 0),
            price=data.get('price', 0),
            qr=data.get('qr', ''),
        )


class User:
    def __init__(self, id=0, first_name="", last_name="", email="",
                 password="", time=None, tickets=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.time = time if time is not None else datetime.datetime.now()
        self.tickets = tickets if tickets is not None else []

    def add_ticket(self, ticket):
        self.tickets.append(ticket)

    def remove_ticket(self, index):
        if 0 <= index < len(self.tickets):
            del self.tickets[index]

    def update_ticket(self, index, ticket):
        if 0 <= index < len(self.tickets):
            self.tickets[index] = ticket

    def _to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'password': self.password,
            'time': self.time,
            'tickets': [t.to_dict() for t in self.tickets],
        }

    @classmethod
    def _from_dict(cls, data):
        return cls(
            id=data['id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            time=data['time'],
            tickets=[Ticket.from_dict(t) for t in data.get('tickets', [])],
        )


class PickleStorage:
    def __init__(self, container, folder="ks2", filename="users.dat"):
        self.container = container
        self.folder = folder
        self.filename = os.path.join(folder, filename)

    def store(self):
        os.makedirs(self.folder, exist_ok=True)
        payload = (
            self.container.maxID,
            {uid: u._to_dict() for uid, u in self.container.items.items()},
        )
        with open(self.filename, "wb") as f:
            pickle.dump(payload, f)

    def load(self):
        if not os.path.exists(self.filename):
            return
        with open(self.filename, "rb") as f:
            self.container.maxID, raw = pickle.load(f)
        self.container.items = {uid: User._from_dict(d) for uid, d in raw.items()}


class UserRegistry:
    def __init__(self):
        self.items = dict()
        self.maxID = 0
        self.storage = PickleStorage(self)
        self.storage.load()

    def find_by_email(self, email):
        for u in self.items.values():
            if u.email == email:
                return u
        return None

    def add(self, first_name, last_name, email, password):
        if self.find_by_email(email):
            return None
        self.maxID += 1
        user = User(
            id=self.maxID,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        self.items[user.id] = user
        self.storage.store()
        return user

    def authenticate(self, email, password):
        user = self.find_by_email(email)
        if user and user.password == password:
            return user
        return None

    def get(self, user_id):
        return self.items.get(user_id)

    def save(self):
        self.storage.store()

    def update_profile(self, user_id, **fields):
        user = self.items.get(user_id)
        if not user:
            return None
        for k, v in fields.items():
            if hasattr(user, k) and v is not None:
                setattr(user, k, v)
        self.save()
        return user

    def reset_password_lookup(self, first_name, last_name, email):
        for u in self.items.values():
            if (u.first_name == first_name
                    and u.last_name == last_name
                    and u.email == email):
                return u.password
        return None


registry = UserRegistry()
