from model.operations import *
from model.network import *
import numpy as np
import zipfile
import os
import configparser
from io import StringIO


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

        # Print all fields of config
        for section in config.sections():
            print(f"Section: {section}")
            for key, value in config.items(section):
                print(f"{key}: {value}")

        net.channel = self._load_channel_info(config['channel'])
        net.mcst = self._load_mcs_table(config['mcs_table'])

        ues = config['ues']
        net.ues['x'], net.ues['y'] = self._gen_positions(net.channel, ues['pos'])
        net.ues['id'] = net.ues.index
        self.read_ue_props(net, ues)

        gnbs = config['gnbs']
        net.gnbs['x'], net.gnbs['y'] = self._gen_positions(net.channel, gnbs['pos'])
        net.gnbs['id'] = net.gnbs.index
        self.read_gnb_props(net, gnbs)


    def _load_zip(self, name, net):
        with zipfile.ZipFile(name, 'r') as zip_file:
            net.ues = pd.read_csv(zip_file.open('ues.csv'))
            net.gnbs = pd.read_csv(zip_file.open('gnbs.csv'))
            file_names = [name for name in zip_file.namelist() if name.startswith('conns/')]
            for file_name in file_names:
                col_name = file_name[6:-4]
                with zip_file.open(file_name) as file:
                    net.conns[col_name] = np.loadtxt(file)

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
    

    def _load_mcs_table(self, data):
        return MCSTable(
            int(data['levels']),
            float(data['min_snr']),
            float(data['spacing']),
            float(data['efficiency'])
        )
    

    def _gen_positions(self, channel, pos):
        method, args = pos.split(':')
        if method == 'grid':
            rows, cols = tuple(int(d) for d in args.split('x'))
            return grid(*channel.area, rows, cols)
        elif method == 'scatter':
            return scatter(*channel.area, float(args))


    def read_ue_props(self, net, ues):
        if 'gain' in ues: net.ues['gain'] = float(ues['gain'])
        if 'demand' in ues: net.ues['demand'] = float(ues['demand'])
        if 'max_power' in ues: net.ues['max_power'] = float(ues['max_power'])


    def read_gnb_props(self, net, gnbs):
        if 'gain' in gnbs: net.gnbs['gain'] = float(gnbs['gain'])


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

        config = configparser.ConfigParser()
        self.channel_to_ini(net.channel, config)
        self.mcs_to_ini(net.mcst, config)

        config_str = ''
        with StringIO() as strio:
            config.write(strio)
            strio.seek(0)
            config_str = strio.read()

        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('ues.csv', net.ues.to_csv(index=False))
            zip_file.writestr('gnbs.csv', net.gnbs.to_csv(index=False))
            zip_file.writestr('channel.ini', config_str)
            for col_name, col_data in net.conns.items():
                with StringIO() as strio:
                    np.savetxt(strio, col_data)
                    strio.seek(0)
                    zip_file.writestr(f'conns/{col_name}.txt', strio.read())


    def channel_to_ini(self, channel, config):
        config['channel'] = {
            'noise': str(channel.noise),
            'area': f'{channel.area[0]}x{channel.area[1]}',
            'bandwidth': f'{channel.bandwidth[0]}-{channel.bandwidth[1]}'
        }


    def mcs_to_ini(self, mcs, config):
        config['mcs_table'] = {
            'levels': str(mcs.levels),
            'min_snr': str(mcs.min_snr),
            'spacing': str(mcs.spacing),
            'efficiency': str(mcs.efficiency)
        }

