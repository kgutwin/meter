import os
import argparse
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.environ['METER_CONFIG'])

def to_bool(s):
    return s.lower() in ('yes', 'true', 't', '1')


def write_config():
    with open(os.environ['METER_CONFIG'], 'w') as fp:
        CONFIG.write(fp)


class DefaultArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if 'source' in kwargs:
            self.source = kwargs['source']
            kwargs['prog'] = f'meter {self.source}'
            del(kwargs['source'])
        else:
            self.source = 'MAIN'

        self.config_save = {}
            
        super().__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        option_strings = [i for i in args
                          if i.startswith('--') or not i.startswith('-')]
        dest = kwargs.pop('dest', option_strings and option_strings[0] or None)
        do_save = kwargs.pop('config_save', True)
        if dest:
            dest = dest.lstrip('-').replace('-', '_')
            self.config_save[dest] = do_save
            if self.source in CONFIG and dest in CONFIG[self.source]:
                default_type = str
                if kwargs.get('action') in ('store_true', 'store_false'):
                    default_type = to_bool
                var_type = kwargs.get('type', default_type)
                kwargs['default'] = var_type(CONFIG[self.source][dest])
                if 'required' in kwargs:
                    del(kwargs['required'])

        return super().add_argument(*args, **kwargs)

    def _update_config(self, options):
        if self.source not in CONFIG:
            CONFIG[self.source] = {}
        for k, v in vars(options).items():
            if self.config_save.get(k) and v is not None:
                CONFIG[self.source][k] = str(v)
        write_config()
    
    def parse_args(self, args=None, namespace=None):
        options = super().parse_args(args, namespace)
        self._update_config(options)
        return options

    def parse_known_args(self, args=None, namespace=None):
        if namespace is None:
            namespace = argparse.Namespace()
        self._namespace = namespace
        options, remaining = super().parse_known_args(args, namespace)
        self._update_config(options)
        return options, remaining
    
    def print_help(self, file=None):
        if hasattr(self, '_namespace') and hasattr(self._namespace, 'source'):
            try:
                from meter import sources
                source_type = getattr(sources, self._namespace.source)
            except AttributeError:
                print(f'NOTE: source {self._namespace.source} not found')
                return

            source_type(['--help'])
        else:
            super().print_help(file)
            
