"""MAC address Monitoring daemon."""

import logging
import logging.handlers

import threading
import signal
import ipaddress
import daemon
import click
import netifaces
import scapy.all


CONFIG = {}
ADDRESSES = []
WORKERS = []
SHUTDOWN = threading.Event()


logging.basicConfig(format='[%(levelname)-8s] %(message)s')
logger = logging.getLogger(__name__)

syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
logger.addHandler(syslog_handler)

interfaces = netifaces.interfaces()


def get_address_list():
    """Fetch and return a list of addresses."""
    ans, unans = scapy.all.arping(
        net=CONFIG['address'],
        timeout=CONFIG['timeout'],
        verbose=-1  # Disable scapy's log output
    )

    return [x[1].src for x in ans]


def update_address_list():
    """Perform an address list update."""
    logger.debug('Starting address list update')

    global ADDRESSES
    ADDRESSES = get_address_list()

    logger.debug('Address list update completed [addresses=%s]', ADDRESSES)


def perform_update_loop():
    """Perform an address list update loop."""
    while not SHUTDOWN.is_set():
        update_address_list()
        SHUTDOWN.wait(CONFIG['interval'])


def start_client():
    """Start the monitoring client."""
    # Register signal handlers
    signal.signal(signal.SIGINT, stop_client)
    signal.signal(signal.SIGTERM, stop_client)

    # Define workers
    global WORKERS
    WORKERS += [threading.Thread(target=perform_update_loop)]

    # Start all workers
    [x.start() for x in WORKERS]

    # Wait for shutdown
    SHUTDOWN.wait()


def stop_client(signum, frame):
    """Stop the monitoring client."""
    logger.debug('Received signal, shutting down [signal=%s]', signum)

    # Inform workers of shutdown
    SHUTDOWN.set()

    # Join all workers
    [x.join() for x in WORKERS]


@click.command()
@click.option('--debug/--no-debug', '-d', default=False, help='Enable or disable debug output.')
@click.option('--daemon/--no-daemon', default=False, help='Enable or disable daemonizing.')
@click.option('--timeout', '-t', default=5, help='Arping timeout.')
@click.option('--interval', '-i', default=30, help='Polling interval.')
@click.option('--interface', '-if', type=click.Choice(interfaces), help='Network interface to operate on.')
@click.option('--address', '-a', help='Network address to operate on.')
@click.pass_context
def macmond(ctx, **kwargs):
    """MAC address Monitoring daemon."""
    CONFIG.update(kwargs)

    logger.setLevel(logging.DEBUG if CONFIG['debug'] else logging.INFO)
    logger.debug('Starting program [config=%s]', CONFIG)

    if not CONFIG['address']:
        logger.debug('No network address set, falling back to given interface')

        if not CONFIG['interface']:
            logger.critical('No network address or interface set, exiting')
            ctx.exit(1)

        # Determine network address/netmask based on interface name
        logger.debug('Attempting to determine network address for interface [interface=%s]', CONFIG['interface'])
        addrs = netifaces.ifaddresses(CONFIG['interface'])

        if netifaces.AF_INET not in addrs:
            logger.critical('Could not find a valid address [interface=%s]', CONFIG['interface'])
            ctx.exit(1)

        net_addr = addrs[netifaces.AF_INET][0]
        CONFIG['address'] = str(ipaddress.ip_network('%s/%s' % (net_addr['addr'], net_addr['netmask']), strict=False))

        logger.debug('Set network address based on interface [address=%s]', CONFIG['address'])

    if CONFIG['daemon']:
        logger.debug('Daemonizing program')

        with daemon.DaemonContext(files_preserve=[syslog_handler]):
            start_client()
    else:
        start_client()
