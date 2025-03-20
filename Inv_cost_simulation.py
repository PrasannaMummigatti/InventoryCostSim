import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.interpolate import make_interp_spline


def simulate_inventory_policy(poisson_lambda, periods, holding_cost_rate, shortage_cost_rate, ordering_cost, s, Q_values, lead_time=2):
    results = []
    np.random.seed(42)
    demand = np.random.poisson(poisson_lambda, periods)

    for Q in Q_values:
        inventory = s
        total_ordering_cost = 0
        total_holding_cost = 0
        total_shortage_cost = 0
        inventory_levels = []
        reorder_points = []
        arrivals = []
        pending_orders = []
        order_pending = False  # Tracks if an order is already placed

        for t in range(periods):
            # Process arrivals
            arriving_orders = [qty for (arrival, qty) in pending_orders if arrival == t]
            inventory += sum(arriving_orders)

            if arriving_orders:
                arrivals.append(t)  # Mark order arrival
                order_pending = False  # Order fulfilled, reset flag

            # Remove fulfilled orders
            pending_orders = [(arrival, qty) for (arrival, qty) in pending_orders if arrival > t]

            # Reorder if inventory < s and no order is pending
            if inventory < s and not order_pending:
                total_ordering_cost += ordering_cost
                pending_orders.append((t + lead_time, Q))
                reorder_points.append(t)  # Mark reorder time
                order_pending = True  # Flag that an order is in transit

            # Apply demand
            inventory -= demand[t]
            if inventory < 0:
                total_shortage_cost += shortage_cost_rate * abs(inventory)
                inventory = 0  

            total_holding_cost += holding_cost_rate * inventory  
            inventory_levels.append(inventory)

        total_cost = total_ordering_cost + total_holding_cost + total_shortage_cost
        results.append((Q, total_ordering_cost, total_holding_cost, total_shortage_cost, total_cost, inventory_levels, demand, reorder_points, arrivals))

    return results

# Parameters
poisson_lambda = 10   
periods = 50          
holding_cost_rate = 1  
shortage_cost_rate = 5  
ordering_cost = 300    
s = 25               
Q_values = [10,20,30,50,60,70,80,90,100]  
lead_time = 2        

# Run simulation
results = simulate_inventory_policy(poisson_lambda, periods, holding_cost_rate, shortage_cost_rate, ordering_cost, s, Q_values, lead_time)

# Extract optimal Q data
optimal_index = np.argmin([res[4] for res in results])
optimal_Q = results[optimal_index][0]
optimal_inventory_levels = results[optimal_index][5]
optimal_demand = results[optimal_index][6]
reorder_times = results[optimal_index][7]
arrival_times = results[optimal_index][8]

# ---- 1️⃣ Cost vs. Order Quantity (Static Plot) ----
Q_vals = [res[0] for res in results]
ordering_costs = [res[1] for res in results]
holding_costs = [res[2] for res in results]
shortage_costs = [res[3] for res in results]
total_costs = [res[4] for res in results]

fig1, ax = plt.subplots(figsize=(8, 6))

"""
ax.plot(Q_vals, ordering_costs, label="Ordering Cost", color='blue')
ax.plot(Q_vals, holding_costs, label="Holding Cost", color='green')
ax.plot(Q_vals, shortage_costs, label="Shortage Cost", color='orange')
ax.plot(Q_vals, total_costs, label="Total Cost", color='red', linewidth=2)
"""
# Generate smooth curves using cubic spline interpolation
Q_smooth = np.linspace(0, 100, 30)  # More points for smooth curves
ordering_smooth = make_interp_spline(Q_vals, ordering_costs, k=2)(Q_smooth)
holding_smooth = make_interp_spline(Q_vals, holding_costs, k=2)(Q_smooth)
shortage_smooth = make_interp_spline(Q_vals, shortage_costs, k=2)(Q_smooth)
total_smooth = make_interp_spline(Q_vals, total_costs, k=2)(Q_smooth)

# Plotting smooth curves
#ax.figure(figsize=(10, 6))
ax.plot(Q_smooth, ordering_smooth, linestyle='-', label="Ordering Cost", color="blue")
ax.plot(Q_smooth, holding_smooth, linestyle='-', label="Holding Cost", color="green")
ax.plot(Q_smooth, shortage_smooth, linestyle='-', label="Shortage Cost", color="red")
ax.plot(Q_smooth, total_smooth, linestyle='--', label="Total Cost", color="black", linewidth=2)



# Mark the optimal Q
ax.axvline(optimal_Q, color='black', linestyle='dotted', label=f"Optimal Q = {optimal_Q}")
ax.plot(optimal_Q, min(total_costs), 'rx', markersize=10, label="Min Total Cost")
ax.text(optimal_Q, min(total_costs), f" ({optimal_Q}, {min(total_costs)})", verticalalignment='bottom')


ax.set_xlabel("Order Quantity (Q)")
ax.set_ylabel("Cost")
ax.set_title("Cost vs. Order Quantity")
ax.legend()
ax.grid(True)
plt.show()

# ---- Animated Demand & Inventory Plot ----
fig, axs = plt.subplots(2, 1, figsize=(10, 10))
plt.subplots_adjust(hspace=0.4)

# ---- Demand as a Bar Chart ----
ax1 = axs[0]
ax1.set_xlim(0, periods)
ax1.set_ylim(0, max(optimal_demand) + 5)
ax1.set_xlabel("Time Period")
ax1.set_ylabel("Demand")
ax1.set_title("Demand Over Time-Assuming Poisson Distribution with lambda=10")
ax1.grid(True)

bars_demand = ax1.bar(range(periods), [0] * periods, color="green", label="Demand")
ax1.legend()

# ---- Inventory Levels Over Time (Step Plot) ----
ax2 = axs[1]
ax2.set_xlim(0, periods)
ax2.set_ylim(0, max(max(optimal_inventory_levels) + 5, s * 1.5))
ax2.set_xlabel("Time Period")
ax2.set_ylabel("Inventory Level")
ax2.set_title(f"Inventory Levels Over Time (Optimal Q = {optimal_Q}, s = {s} and Lead Time = {lead_time} \n Total Cost = {min(total_costs)},ordering cost = {ordering_cost}/Order,holding cost = {holding_cost_rate}/day/unit,shortage cost = {shortage_cost_rate}/event")
ax2.grid(True)

line_inventory, = ax2.step([], [], where='mid', linestyle='-', color="blue", label="Inventory Level")
ax2.axhline(s, color='red', linestyle='dotted', label="Reorder Level (s)")

# Reorder and Arrival markers
reorder_marks, = ax2.plot([], [], 'rx', markersize=8, label="Reorder Point (s)")
arrival_marks, = ax2.plot([], [], 'gx', markersize=8, label="Order Arrival (s)")

ax2.legend()

# ---- Animation Function ----
def update(frame):
    if frame < periods:  
        # Update demand bars
        for i in range(frame + 1):
            bars_demand[i].set_height(optimal_demand[i])

        # Update inventory step plot
        line_inventory.set_data(range(frame+1), optimal_inventory_levels[:frame+1])

        # Reorder Points (red "x") at s level
        reorder_x = [t for t in reorder_times if t <= frame]
        reorder_y = [s] * len(reorder_x)
        reorder_marks.set_data(reorder_x, reorder_y)

        # Arrivals (green "x") at s level
        arrival_x = [t for t in arrival_times if t <= frame]
        arrival_y = [s] * len(arrival_x)
        arrival_marks.set_data(arrival_x, arrival_y)

    return bars_demand, line_inventory, reorder_marks, arrival_marks

# Create animation
ani = animation.FuncAnimation(fig, update, frames=periods, interval=300, blit=False)

plt.show()