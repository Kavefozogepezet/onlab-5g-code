import matplotlib
from matplotlib import pyplot as plt


matplotlib.use("pgf")
matplotlib.rcParams.update({
    'pgf.texsystem': 'pdflatex',
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})


def styled_legend(legend):
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square')
    frame.set_linewidth(0.5)


def export_plot(fig, filename: str, width: float):
    size = fig.get_size_inches()
    fig.set_size_inches(width, size[1]/size[0]*width)
    fig.tight_layout(pad=0)
    plt.savefig(filename)
