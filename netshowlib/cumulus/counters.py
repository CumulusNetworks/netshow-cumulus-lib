# http://pylint-messages.wikidot.com/all-codes
# pylint: disable=R0903
"""
Module responsible for printing countes for the cumulus provider
"""
from netshowlib.cumulus import common
from netshowlib.linux import common as linux_common
import os
import io


def get_ethtool_output(ifacename):
    """
    :return: ethtool output method used by cumulus provider to get ethtool output of a single interface.
    """
    cmd = '/sbin/ethtool -S %s' % (ifacename)
    try:
        ethtool_output = linux_common.exec_command(cmd)
    except linux_common.ExecCommandException:
        return u''
    return ethtool_output


def get_physical_port_counters(ethtool_output):
    """
    :param: array of ethtool output of a specific interface.
    :return: hash of broadcast, unicast, multicast and
    error counters of a specific interface
    """
    counters_hash = {'tx': {}, 'rx': {}}
    fileio = io.StringIO(ethtool_output)
    for line in fileio:
        if len(line.strip()) <= 0:
            continue
        # make all char lowercase
        line = line.lower()
        splitline = line.split()
        rx_tx_hash = {'in': 'rx',
                      'out': 'tx'}
        for _dir, _pkt_dir in rx_tx_hash.items():
            if splitline[0] == 'hwif' + _dir + 'ucastpkts:':
                counters_hash[_pkt_dir]['unicast'] = int(splitline[1])
            elif splitline[0] == 'hwif' + _dir + 'bcastpkts:':
                counters_hash[_pkt_dir]['broadcast'] = int(splitline[1])
            elif splitline[0] == 'hwif' + _dir + 'mcastpkts:':
                counters_hash[_pkt_dir]['multicast'] = int(splitline[1])
            elif splitline[0] == 'hwif' + _dir + 'errors:':
                counters_hash[_pkt_dir]['errors'] = int(splitline[1])
                break
    return counters_hash


def cacheinfo(ifacename=None):
    """
    :return: hash of following format
       ```
          {'swp1': {
               'tx': {
                   'unicast': 1111
                   'broadcast': 1111
                   'multicast': 1111
                   'errors': 1111
                }
                'rx': {
                   'unicast': 1111
                   'broadcast': 1111
                   'multicast': 1111
                   'errors': 1111
                }
             }
          }
       ```
    """
    counters_hash = {}
    if ifacename:
        counters_hash[ifacename] = get_physical_port_counters(
            get_ethtool_output(ifacename))
        return counters_hash

    for _iface in os.listdir(linux_common.SYS_PATH_ROOT):
        if common.is_phy(_iface):
            counters_hash[_iface] = get_physical_port_counters(
                get_ethtool_output(_iface))

    return counters_hash


class Counters(object):
    """
    class responsible for printing counters for the cumulus provider
    """
    def __init__(self, name, cache=None):
        self.tx = {
            'unicast': 0,
            'broadcast': 0,
            'multicast': 0,
            'errors': 0
        }
        self.rx = {
            'unicast': 0,
            'broadcast': 0,
            'multicast': 0,
            'errors': 0
        }
        self.name = name
        if cache:
            self._cache = cache.counters
        else:
            self._cache = None

    def run(self):
        """
        ``run()`` function for this feature updates the cache .
        """
        if not self._cache:
            self._cache = cacheinfo(self.name)

        counter_cache = self._cache.get(self.name)
        if counter_cache:
            self.tx = counter_cache.get('tx')
            self.rx = counter_cache.get('rx')

    @property
    def total_tx(self):
        """
        :return: total tx counters
        """
        if self.tx:
          return self.tx.get('unicast') + \
              self.tx.get('multicast') + \
              self.tx.get('broadcast')

    @property
    def total_rx(self):
        """
        :return: total rx counters
        """
        if self.rx:
          return self.rx.get('unicast') + \
              self.rx.get('multicast') + \
              self.rx.get('broadcast')

    @property
    def total_err(self):
        """
        :return: total  error counters
        """
        if self.rx and self.tx:
          return self.rx.get('errors') + \
              self.tx.get('errors')
        if self.rx:
            return self.rx.get('errors')
        if self.tx:
            return self.tx.get('errors')

    @property
    def all(self):
        """
        :return: all both tx and rx counters as a hash
        """
        return {'tx': self.tx, 'rx': self.rx}
