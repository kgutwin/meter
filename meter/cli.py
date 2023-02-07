import os
import sys
import logging
import argparse

os.environ.setdefault('METER_CONFIG', os.path.expanduser('~/.meter.cfg'))

from meter import sources, config, iot


def print_sources():
    for k, v in vars(sources).items():
        try:
            if not issubclass(v, sources.base.BaseSource):
                continue
            doc = v.__doc__ or ""
            try:
                first_line = doc.strip().splitlines()[0]
                print(k, '--', first_line)
            except IndexError:
                print(k)
        except TypeError:
            pass


def main():
    argparser = config.DefaultArgumentParser()
    argparser.add_argument('source', config_save=False)
    argparser.add_argument('--thing-name', default='pico_w_meter')
    argparser.add_argument('--verbose', '-v', action='count', default=0,
                           config_save=False)
    argparser.add_argument('--setup-iot-assume-role-from', metavar="ACCOUNT-ID",
                           config_save=False,
                           help=("Create a role that can be assumed by the"
                                 " provided ACCOUNT-ID that has access to"
                                 " the meter's IoT Thing"))
    argparser.add_argument('--iot-assume-role-to', '-t',
                           metavar="ACCOUNT-ID-OR-ARN",
                           help=("When communicating with the meter, assume role"
                                 " to the provided ACCOUNT-ID-OR-ARN"))
    argparser.add_argument('--show-temperature', '-T', action='store',
                           type=config.to_bool, default=False,
                           help="log unit temperature")
    argparser.add_argument('--period', '-s', type=int, metavar="SECONDS",
                           default=4, help="minimum time between polling cycles")
    
    options, remaining = argparser.parse_known_args()

    logging.basicConfig(
        format=(
            "%(asctime)s [%(name)s] %(levelname)s - %(message)s"
            if options.verbose < 2 else
            "%(asctime)s [%(name)s(%(filename)s:%(lineno)d)] %(levelname)s - %(message)s"
        ),
        level={
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.DEBUG,
        }[options.verbose]
    )
    logger = logging.getLogger(__name__)

    # handle setup assume role
    if options.setup_iot_assume_role_from:
        iot.create_assume_role(options.setup_iot_assume_role_from)
        print('Done!')
        sys.exit(0)
    
    try:
        source_type = getattr(sources, options.source)
    except AttributeError:
        print(f'source {options.source} not found!')
        print('available sources:')
        print('------------------')
        print_sources()
        sys.exit(1)

    s = source_type(remaining, min_cycle=options.period)
    meter = iot.Meter(
        options.thing_name,
        min_cycle=options.period,
        assume_role=options.iot_assume_role_to,
        show_temp=options.show_temperature,
    )
    try:
        meter.loop(s)
    except KeyboardInterrupt:
        meter.clear()
        logger.warning("Clean exit.")

        
if __name__ == '__main__':
    main()
