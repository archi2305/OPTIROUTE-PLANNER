class DeliveryManager:
    def __init__(self):
        self.deliveries = []

    def add_delivery(self, delivery):
        self.deliveries.append(delivery)

    def show_deliveries(self):
        for d in self.deliveries:
            print(d.order_id, d.destination, d.priority, d.deadline)