# pylint: disable=W0232
# pylint: disable=E0611
# pylint: disable=E1101
"""
Cumulus Iface module with print functions
"""
from netshowlib import netshowlib as nn
from netshowlib.cumulus import iface as cumulus_iface
from netshow.linux import print_iface as linux_printiface
from tabulate import tabulate
from netshowlib.linux import common as linux_common
from netshow.cumulus.common import _
import inflection


def iface(name, cache=None):
    """
    :return: ``:class:PrintIface`` instance that matches \
        correct iface type of the named interface
    :return: None if interface does not exist
    """
    # create test iface.
    test_iface = cumulus_iface.iface(name, cache=cache)
    if not test_iface.exists():
        return None
    if test_iface.is_bridge():
        bridge = nn.import_module('netshow.cumulus.print_bridge')
        return bridge.PrintBridge(test_iface)
    elif test_iface.is_bond():
        bond = nn.import_module('netshow.cumulus.print_bond')
        return bond.PrintBond(test_iface)
    elif test_iface.is_bondmem():
        bondmem = nn.import_module('netshow.cumulus.print_bond')
        return bondmem.PrintBondMember(test_iface)
    elif test_iface.is_bridgemem():
        bridge = nn.import_module('netshow.cumulus.print_bridge')
        return bridge.PrintBridgeMember(test_iface)
    return PrintIface(test_iface)


class PrintIface(linux_printiface.PrintIface):
    """
    Cumulus Iface class with print functions
    """
    @property
    def connector_type(self):
        """
        :return: prints out string for connector type
        """
        if not hasattr(self.iface, 'connector_type'):
            return None

        _connector = self.iface.connector_type
        if _connector == 4:
            return _('4x10g')
        elif _connector == 3:
            return _('qsfp')
        elif _connector == 2:
            return _('sfp')
        elif _connector == 1:
            return _('rj45')

    def trunk_summary_vlan_aware(self):
        """
        :return list of vlan trunk  info for vlan aware bridge
        """
        _strlist = []
        _strlist.append(_('vlans') + ': ' + ','.join(
            linux_common.create_range('', self.iface.vlan_list)))
        _strlist.append(_('native') + ': ' + ','.join(
            linux_common.create_range('', self.iface.native_vlan)))
        return _strlist

    def access_summary_vlan_aware(self):
        """
        :return: list of access summar port info
        """
        _strlist = []
        _strlist.append(_('native') + ': ' + ','.join(self.iface.vlan_list))
        return _strlist

    def trunk_summary(self):
        """
        :return: summary info for a trunk port
        """
        if self.iface.vlan_filtering:
            return self.trunk_summary_vlan_aware()
        else:
            return linux_printiface.PrintIface.trunk_summary(self)

    def access_summary(self):
        """
        :return: summary info for a access port
        """
        if self.iface.vlan_filtering:
            return self.access_summary_vlan_aware()
        else:
            return linux_printiface.PrintIface.access_summary(self)

    @property
    def port_category(self):
        """
        :return: port type. Via interface discovery determine classify port \
        type
        """
        if self.iface.is_mgmt():
            return _('mgmt')
        elif self.iface.is_svi():
            return _('svi/l3')
        else:
            return super(PrintIface, self).port_category

    @property
    def speed(self):
        """
        used by the functions that print speed info on cumulus linux.
        :return: speed + connector type in one print statement.
        """
        _connector_type = self.connector_type
        _speed = linux_printiface.PrintIface.speed.fget(self)
        if _connector_type:
            return "%s(%s)" % (_speed, _connector_type)
        else:
            return _speed

    def cli_output(self):
        """
        Each PrintIface child should define their own  of this function
        :return: output for 'netshow interface <ifacename>'
        """
        _str = self.cli_header()
        _ip_details = self.ip_details()
        if _ip_details:
            _str += _ip_details
        _counter_summary = self.counters_summary()
        if _counter_summary:
            _str += _counter_summary
        _str += self.lldp_details()
        return _str

    def counters_summary(self):
        """ print summary of cumulus counters
        Returns:
            table of unicast, broadcast, multicast and error tx/rx counters
            if executed on cumulus VM/non Cumulus but Linux platform,
            this returns nothing
        """
        _counters = self.iface.counters
        if not _counters and not _counters.tx:
            return ''
        _counters_all = _counters.all
        _header = [_('counters'), _('tx'), _('rx')]
        _table = []
        for _countername in ['errors', 'unicast', 'broadcast', 'multicast']:
            _table.append([_(_countername),
                           _counters_all.get('tx').get(_countername),
                           _counters_all.get('rx').get(_countername)])
        # keep return in the right place please!
        return tabulate(_table, _header) + self.new_line()

    def bridgemem_details(self):
        """
        :return: list vlans or bridge names of various stp states MODIFY
        """
        if not self.iface.is_bridgemem():
            return None
        # check if port is in STP
        _str = ''
        _stpstate = self.iface.stp.state
        # get the list of states by grabbing all the keys
        if self.iface.vlan_filtering:
            _vlanlist = self.iface.vlan_list
            _header = [_("all vlans on l2 port")]
            _table = [[', '.join(linux_common.create_range('', _vlanlist))]]
            _str += tabulate(_table, _header, numalign='left') + self.new_line()
            _header = [_("untagged vlans")]
            _table = [[', '.join(self.iface.native_vlan)]]
            _str += tabulate(_table, _header, numalign='left') + self.new_line()
        for _state, _bridgelist in _stpstate.items():
            if _bridgelist:
                _header = [_("vlans in %s state") %
                           (inflection.titleize(_state))]
                # if vlan aware and bridgelist is not empty, then assume
                # all vlans have that stp state
                if self.iface.vlan_filtering:
                    _table = [[', '.join(linux_common.create_range(
                        '', _vlanlist))]]
                else:
                    _table = [self._pretty_vlanlist(_bridgelist)]

                _str += tabulate(_table, _header, numalign='left') + self.new_line()

        return _str
