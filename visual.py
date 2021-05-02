import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["figure.figsize"] = (20, 11.25)


def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def mapper(i):
    def inner(x):
        if x:
            return x[i]
        else:
            return 0

    return inner


def plot(bencher, data):
    labels = data.keys()
    for i in bencher.attribute_list:
        values = list(map(mapper(i), data.values()))
        x = np.arange(len(labels))  # the label locations
        width = 0.75  # the width of the bars
        fig, ax = plt.subplots()
        rects = ax.bar(x, values, width)
        ax.set_ylabel(i)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title("{} {}".format(bencher.__name__, i))
        autolabel(rects, ax)
        fig.tight_layout()
        plt.savefig("output/{}-{}.png".format(bencher.__name__, i))
        plt.close(fig)
