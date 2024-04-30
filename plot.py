from mlxtend.plotting import plot_decision_regions
import matplotlib.pyplot as plt
import numpy as np


class Predict:

    def __init__(self, f):
        self.f = f

    def predict(self, X):
        return self.f(X)


def plotDecisionBoundary(X, y, title, xlabel, ylabel, fileName, f):
    plt.figure()

    plot_decision_regions(X, y, clf=Predict(f), legend=2)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)

    plt.savefig(fileName)

    plt.show()


def quickF(model):
    def f(X):
        return model.predict(X)

    return f
