import numpy as np
from dataclasses import dataclass


@dataclass
class BeamData:
    beamwidth: float
    gain_main: float
    gain_side: float


    def upa_antenna(antenna_count):
        rec_sqrt_n = 1 / np.sqrt(antenna_count)
        return BeamData(
            beamwidth=2*np.pi*rec_sqrt_n,
            gain_main=antenna_count,
            gain_side=np.sin(3*np.pi*rec_sqrt_n/2)**-2
        )
    

if __name__ == "__main__":
    from matplotlib import pyplot as plt
    import sys
    sys.path.append(sys.path[0] + "/../utils/")
    import plotutils as pu

    sqrt_N = np.arange(2, 33, 2)
    N = sqrt_N ** 2
    beams = BeamData.upa_antenna(N)

    tp2p = beams.beamwidth / (2*np.pi)
    factor = beams.gain_main / (tp2p * (beams.gain_main - beams.gain_side) + beams.gain_side)

    fig, ax = plt.subplots()
    ax.scatter(sqrt_N, factor, marker='D', s=16)
    ax.set_xticks(
        sqrt_N,
        labels=[f"{n}x{n}" for n in sqrt_N],
        rotation=45
    )
    ax.set_yticks(
        range(0, 15, 2),
        labels=[f"{n}" for n in range(0, 15, 2)]
    )
    ax.set_xlabel("Antenna mátrix mérete")
    ax.set_ylabel("$\gamma'/\gamma$")
    #fig.set_size_inches(4, 3)
    pu.export_plot(fig, "beamf_snr_ratio.pgf", 3.5)
    #plt.show()


    sqrt_N = np.array([4,8,12,16,24,28,32])
    N = sqrt_N ** 2
    beams = BeamData.upa_antenna(N)

    tp2p = beams.beamwidth / (2*np.pi)
    factor = beams.gain_main / (tp2p * (beams.gain_main - beams.gain_side) + beams.gain_side)

    tex_str = (
        r'\begin{tabular}{|c||' + 'c|' * len(sqrt_N) + '}\n\t\\hline\n'
        '\tMátrix mérete &' + '&'. join([f"${n}{{\\times{n}}}$" for n in sqrt_N]) + r' \\' +
        '\n\t\\hline\n\t$\gamma\'/\gamma$ &' + '&'. join([f"{f:.2f}" for f in factor]) + r' \\' +
        '\n\t\\hline\n\\end{tabular}'
    )
    with open('beamf_snr_ratio.tex', 'w', encoding='utf-8') as f:
        f.write(tex_str)