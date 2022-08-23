import matplotlib.pyplot as plt
import numpy as np

figurePath = "Presentation Images/"

x_positions = ["Measurement Client", "AUX Client"]


plt.rcParams.update({'font.size': 30})

x_ints = []
for i in range(0, 16):
    x_ints.append(i)

heights = []
colors = []
names = []
for i in x_ints:
    heights.append(0)
    colors.append("orange")
    names.append("AUX Client " + str(i))
colors[0] = 'steelblue'
names[0] = "Measurement Client"


def makeFigure(title, fnHeights):
    plt.figure()
    plt.gcf().set_size_inches(33, 10)
    plt.bar(x_ints, fnHeights, 0.8, color=colors)
    plt.ylim(0, 500)
    # plt.xticks(np.array(list(map(lambda x: x-.5, x_ints))), names, rotation = -90)
    plt.xticks(np.array(x_ints), names, rotation = 90)
    plt.ylabel("Requests Per Second")
    plt.title("Global RPS: " + str(sum(fnHeights)))
    print("Global RPS: " + str(sum(fnHeights)))
    plt.savefig(figurePath + title + ".png", bbox_inches='tight', pad_inches = 0.1)
    plt.close()


measHeights = [100, 200, 300, 400, 500]
nextAuxIndex = 1
for i in range(0, len(x_ints) * 5 + 1):
    makeFigure("Step " + str(i), heights)
    if(heights[len(heights) - 1] == 500 & heights[0] >= 400):
        heights[0] = 500
    elif heights[0] == 500:
            heights[0] = 100
            heights[nextAuxIndex] = 500
            nextAuxIndex += 1
    else:
        heights[0] += 100
