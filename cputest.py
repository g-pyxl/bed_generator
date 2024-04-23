import matplotlib.pyplot as plt
import numpy as np

# Instance types and their corresponding CPU/RAM values
instance_types = ['t2.micro', 't2.small', 't2.medium', 't2.large', 't2.xlarge', 't2.2xlarge']
cpu_values = [1, 1, 2, 2, 4, 8]
ram_values = [1, 2, 4, 8, 16, 32]

# Mock execution times for each instance type
execution_times = [100, 80, 60, 50, 45, 44]

# Create a figure and axis
fig, ax = plt.subplots(figsize=(8, 6))

# Plot the execution times against the instance types
ax.plot(instance_types, execution_times, marker='o', linestyle='-', linewidth=2)

# Set the title and labels for the plot
ax.set_title('Performance Saturation Across Instance Types')
ax.set_xlabel('Instance Type')
ax.set_ylabel('Execution Time (seconds)')

# Set the tick labels for the x-axis
ax.set_xticks(range(len(instance_types)))
ax.set_xticklabels(instance_types, rotation=45, ha='right')

# Add annotations for CPU and RAM values
for i, (cpu, ram) in enumerate(zip(cpu_values, ram_values)):
    ax.annotate(f'CPU: {cpu}, RAM: {ram}', (i, execution_times[i]), textcoords="offset points", xytext=(0, 10), ha='center')

# Show the plot
plt.tight_layout()
plt.show()