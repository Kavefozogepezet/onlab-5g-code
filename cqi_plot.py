import numpy as np
from scipy.special import erfc, erf
from matplotlib import pyplot as plt
import utils.plotutils as pu


def shannon_limit(snr):
    return np.log2(1 + 10**(snr/10))


def plot_eff_snr(qpsk_snr, qam16_snr, qam64_snr, qpsk_eff, qam16_eff, qam64_eff):
    x = np.linspace(min(qpsk_snr)-1, max(qam64_snr)+1, 40)
    y = shannon_limit(x)

    fit = 4.5234 / shannon_limit(15.3598)
    print(fit)
    
    plt.rcParams.update({'font.size': 9})
    fig, ax = plt.subplots()

    ax.plot(x, y, label='$\eta_{\lim}$', zorder=0)
    ax.plot(x, fit*y, c='red', label='$0.879 \cdot \eta_{\lim}$', zorder=0)

    ax.scatter(qpsk_snr, qpsk_eff, marker='s', color='firebrick', label='QPSK')
    ax.scatter(qam16_snr, qam16_eff, marker='D', color='firebrick', label='16-QAM')
    ax.scatter(qam64_snr, qam64_eff, marker='^', color='firebrick', label='64-QAM')

    ax.set_xlabel('Jel-zaj viszony (dB)')
    ax.set_ylabel('Spektrális hatékonyság (bps/Hz)')
    legend = ax.legend()
    pu.styled_legend(legend)
    pu.export_plot(fig, 'eff_vs_snr.pgf', 2.8)
    #plt.grid()
    #plt.show()


def plot_cqi_snr(qpsk, qam16, qam64):
    qpskx = np.arange(1, len(qpsk)+1)
    qam16x = np.arange(1, len(qam16)+1) + qpskx[-1]
    qam64x = np.arange(1, len(qam64)+1) + qam16x[-1]

    all_snr = [*qpsk, *qam16, *qam64]
    x = np.arange(1, len(all_snr)+1)
    
    fit_line = np.polyfit(x, all_snr, 1)
    fit_line_fn = np.poly1d(fit_line)
    print(fit_line_fn)

    fit_line_fn = lambda x: 1.938*x - 9.682
    fit_y = fit_line_fn(x)

    plt.rcParams.update({'font.size': 9})
    fig, ax = plt.subplots()

    ax.scatter(qpskx, qpsk, marker='s', color='firebrick', label='QPSK')
    ax.scatter(qam16x, qam16, marker='D', color='firebrick', label='16-QAM')
    ax.scatter(qam64x, qam64, marker='^', color='firebrick', label='64-QAM')

    ax.plot(x, fit_y, c='red', label='illesztett', zorder=0)

    ax.set_xlabel('CQI index')
    ax.set_ylabel('Jel-zaj viszony (dB)')
    legend = ax.legend()
    pu.styled_legend(legend)
    pu.export_plot(fig, 'cqi_vs_snr.pgf', 2.8)
    #plt.grid()
    #plt.show()

if __name__ == '__main__':
    qpsk_snr = [-7.8474,-6.2369,-4.3591,-1.9319,0.1509,1.9976]
    qam16_snr = [4.7278,6.2231,8.0591]
    qam64_snr = [9.8585,11.8432,13.4893,15.3598,17.4435,19.2155]

    qpsk_eff = [0.1523,0.2344,0.3770,0.6016,0.8770,1.1758]
    qam16_eff = [1.4766,1.9141,2.4063]
    qam64_eff = [2.7305,3.3223,3.9023,4.5234,5.1152,5.5547]

    plot_eff_snr(qpsk_snr, qam16_snr, qam64_snr, qpsk_eff, qam16_eff, qam64_eff)
    plot_cqi_snr(qpsk_snr, qam16_snr, qam64_snr)

