from operations import *
from network import *
import numpy as np
import zipfile
import os


def scatter(width, height, density):
    x = np.random.uniform(0, width, int(density * width * height))
    y = np.random.uniform(0, height, int(density * width * height))
    return x, y


def grid(width, height, rows, cols):
    rad_x = width / (2 * cols)
    rad_y = height / (2 * rows)
    x = np.repeat(np.linspace(rad_x, width - rad_x, cols), rows)
    y = np.tile(np.linspace(rad_y, height - rad_y, rows), cols)
    return x, y


class InvalidPathException(Exception): pass


class Load(Operation):
    def __init__(self, name, appendix=None, path='./', force_init=False):
        super().__init__()
        self.name = name
        self.appendix = appendix
        self.path = path if path[-1] == '/' else path + '/'
        self.force_init = force_init


    def to_save(self):
        return Save(self.name, self.appendix, self.path)

    
    def execute(self, net: NetworkData) -> None:
        appendix = '-' + self.appendix if self.appendix else ''
        path = self.path + self.name + appendix + '.5gn'
        if not self.force_init:
            zipname = path + '.zip'
            if os.path.exists(zipname):
                print(f'Reading from {zipname}...')
                self._load_zip(zipname, net)
        
        ininame = path + '.ini'
        if os.path.exists(ininame):
            print(f'Reading from {ininame}...')
            self._load_ini(ininame, net)
        else:
            raise InvalidPathException()
        

    def _load_ini(self, name, net):
        config = configparser.ConfigParser()
        config.read(name)

        net.channel = self._load_channel_info(config['channel'])

        ues = config['ues']
        net.ues['x'], net.ues['y'] = self._gen_positions(net.channel, ues['pos'])
        net.ues['id'] = net.ues.index
        net.ues['max_power'] = float(ues['max_power'])

        gnbs = config['gnbs']
        net.gnbs['x'], net.gnbs['y'] = self._gen_positions(net.channel, gnbs['pos'])
        net.gnbs['id'] = net.gnbs.index

        self._gen_connections(net)


    def _load_zip(self, name, net):
        with zipfile.ZipFile(name, 'r') as zip_file:
            net.ues = pd.read_csv(zip_file.open('ues.csv'))
            net.gnbs = pd.read_csv(zip_file.open('gnbs.csv'))
            net.conns = pd.read_csv(zip_file.open('conns.csv'))
            parser = configparser.ConfigParser()
            inistr = zip_file.read('channel.ini').decode('utf-8')
            parser.read_string(inistr)
            net.channel = self._load_channel_info(parser['channel'])
            return net


    def _load_channel_info(self, data):
        area = tuple(int(d) for d in data['area'].split('x'))
        bandwidth = tuple(float(d) for d in data['bandwidth'].split('-'))
        return Channel(
            float(data['noise']), area, bandwidth)
    

    def _gen_positions(self, channel, pos):
        method, args = pos.split(':')
        if method == 'grid':
            rows, cols = tuple(int(d) for d in args.split('x'))
            return grid(*channel.area, rows, cols)
        elif method == 'scatter':
            return scatter(*channel.area, float(args))
        

    def _gen_connections(self, net):
        net.conns = net.ues.merge(net.gnbs, 'cross', suffixes=('_ue', '_gnb'))



class Save(Operation):
    def __init__(self, name, appendix=None, path='./'):
        self.name = name
        self.appendix = appendix
        self.path = path


    def to_load(self, force_init=False):
        return Load(self.name, self.appendix, self.path, force_init)
    

    def execute(self, net):
        appendix = '-' + self.appendix if self.appendix else ''
        path = self.path + self.name + appendix + '.5gn.zip'
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('ues.csv', net.ues.to_csv(index=False))
            zip_file.writestr('gnbs.csv', net.gnbs.to_csv(index=False))
            zip_file.writestr('conns.csv', net.conns.to_csv(index=False))
            zip_file.writestr('channel.ini', net.channel.to_ini())

