def schedule_deliveries(deliveries):

    # sort deliveries by priority (highest first)
    sorted_deliveries = sorted(deliveries, key=lambda x: x.priority, reverse=True)

    print("Delivery Order:")

    for d in sorted_deliveries:
        print(f"Order {d.order_id} → Destination {d.destination} (Priority {d.priority})")

    return sorted_deliveries