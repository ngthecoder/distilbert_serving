import matplotlib
import matplotlib.pyplot as plt

cpu_limits = [100,200,300,400,500]

latencies = [14.4792746, 6.3408954, 2.708912, 2.4040909, 1.9817448]

plt.plot(cpu_limits, latencies, marker="o")
plt.xlabel("CPU Limit (Millicore)")
plt.ylabel("Latency (Seconds)")
plt.title("Latencies under Different CPU Limits")
plt.savefig("cpu_latency_graph.png")