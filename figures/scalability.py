import matplotlib.pyplot as plt
import numpy as np

figurePath = "Presentation Images/"

x_positions = ["Measurement Client", "AUX Client"]

measHeights = [100, 300, 500]
width = 0.8

colors = ['steelblue', 'orange']

plt.gcf().set_size_inches(1, 0.5)
plt.rcParams.update({'font.size': 15})
plt.figure()

plt.bar([1, 2], [100, 0], width, color=colors)
plt.ylim(0, 500)
plt.xticks(np.array([1, 2]), x_positions)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "First Step.png", bbox_inches='tight')
plt.figure()

plt.bar([1, 2], [300, 0], width, color=colors)
plt.ylim(0, 500)
plt.xticks(np.array([1, 2]), x_positions)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "Third Step.png", bbox_inches='tight')
plt.figure()

plt.bar([1, 2], [500, 0], width, color=colors)
plt.ylim(0, 500)
plt.xticks(np.array([1, 2]), x_positions)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "Fifth Step.png", bbox_inches='tight')
plt.figure()

plt.bar([1, 2], [100, 500], width, color=colors)
plt.ylim(0, 500)
plt.xticks(np.array([1, 2]), x_positions)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "Sixth Step.png", bbox_inches='tight')
plt.figure()

plt.bar([1, 2], [500, 500], width, color=colors)
plt.ylim(0, 500)
plt.xticks(np.array([1, 2]), x_positions)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "Tenth Step.png", bbox_inches='tight')
plt.figure()


plt.gcf().set_size_inches(33, 10)
plt.rcParams.update({'font.size': 30})

x_ints = []
for i in range(0, 16):
    x_ints.append(i)

heights = []
colors = []
names = []
for i in x_ints:
    heights.append(500)
    colors.append("orange")
    names.append("AUX Client " + str(i))
colors[0] = 'steelblue'
names[0] = "Measurement Client"

print(names)

plt.bar(x_ints, heights, width, color=colors)
plt.ylim(0, 500)
# plt.xticks(np.array(list(map(lambda x: x-.5, x_ints))), names, rotation = -90)
plt.xticks(np.array(x_ints), names, rotation = 90)
plt.ylabel("Requests Per Second")
plt.savefig(figurePath + "Final Step.png", bbox_inches='tight', pad_inches = 0.1)
plt.figure()