# pylint: disable=e0611
# pylint: disable=e1101
"""
Print and Analysis Module for Linux bond interfaces
"""

from netshow.cumulus import print_iface as cumulus_print_iface
import netshow.linux.print_bond as linux_print_bond
from tabulate import tabulate
from netshow.cumulus.common import _


class PrintBondMember(cumulus_print_iface.PrintIface,
                      linux_print_bond.PrintBondMember):
    """
    Print and Analysis Class for Linux bond member interfaces
    """

    def bondmem_details(self):
        """
        :return: string with output shown when netshow interfaces is issued on a \
        bond member
        """
        _header = [_('bond_details'), '']
        _master = self.iface.master
        _printbond = PrintBond(_master)
        _table = []
        _table.append([_('master_bond') + ':', _master.name])
        _table.append([_('state_in_bond') + ':', self.state_in_bond])
        _table.append([_('link_failures') + ':', self.iface.linkfailures])
        _table.append([_('bond_members') + ':', ', '.join(_master.members.keys())])
        _table.append([_('bond_mode') + ':', _printbond.mode])
        _table.append([_('load_balancing') + ':', _printbond.hash_policy])
        _table.append([_('minimum_links') + ':', _master.min_links])
        _lacp_info = self.iface.master.lacp
        if _lacp_info:
            _table.append([_('lacp_sys_priority') + ':', _master.lacp.sys_priority])
            _table.append([_('lacp_rate') + ':', _printbond.lacp_rate()])
            _table.append([_('lacp_bypass') + ':', _printbond.lacp_bypass()])

        return tabulate(_table, _header)

    def cli_output(self):
        """
        cli output of the linux bond member interface.
        Does not print out counters for cumulus VM
        :return: output for 'netshow interface <ifacename>'
        """
        _str = self.cli_header() + self.new_line()
        _str += self.bondmem_details() + self.new_line()
        if self.iface.counters.tx:
            _str += cumulus_print_iface.PrintIface.counters_summary(self) + \
                self.new_line()
        _str += self.lldp_details() + self.new_line()
        return _str


class PrintBond(cumulus_print_iface.PrintIface, linux_print_bond.PrintBond):
    """
    Print and Analysis Class for Linux bond interfaces
    """
    def lacp_bypass(self):
        """
        :return print lacp bypass status
        """
        _lacp = self.iface.lacp
        if _lacp:
            if _lacp.bypass == '1':
                return _('lacp_bypass_active')
            elif _lacp.bypass == '0':
                return _('lacp_bypass_inactive')

        return _('lacp bypass not supported')

    def in_clag(self):
        """
        :return: print clag status
        """
        if self.iface.clag_enable == '0':
            return _('clag inactive')
        elif self.iface.clag_enable == '1':
            return _('clag active')
        else:
            return _('clag not supported')

    def bond_details(self):
        """
        print out table with bond details for netshow interface [ifacename]
        """
        _header = [_('bond_details'), '']
        _table = []
        _table.append([_('bond_mode') + ':', self.mode])
        _table.append([_('load_balancing') + ':', self.hash_policy])
        _table.append([_('minimum_links') + ':', self.iface.min_links])
        if self.in_clag:
            _table.append([_('in_clag') + ':', self.in_clag()])
        _lacp_info = self.iface.lacp
        if _lacp_info:
            _table.append([_('lacp_sys_priority') + ':', self.iface.lacp.sys_priority])
            _table.append([_('lacp_rate') + ':', self.lacp_rate()])
            _table.append([_('lacp_bypass') + ':', self.lacp_bypass()])
        return tabulate(_table, _header) + self.new_line()

    def bondmem_details(self):
        """
        print out table with bond member summary info for netshow interface [ifacename]
        for bond interface
        """
        _header = ['', _('port'), _('speed'),
                   _('tx'), _('rx'), _('err'), _('link_failures')]
        _table = []
        _bondmembers = self.iface.members
        if len(_bondmembers) == 0:
            return _('no_bond_members_found')
        first_member = next(iter(self.iface.members))
        if _bondmembers[first_member].counters.tx:
            _header = ['', _('port'), _('speed'),
                       _('tx'), _('rx'), _('err'), _('link_failures')]

            for _bondmem in _bondmembers.values():
                _printbondmem = PrintBondMember(_bondmem)
                _table.append([_printbondmem.linkstate,
                               "%s(%s)" % (_printbondmem.name,
                                           self.abbrev_bondstate(_bondmem)),
                               _printbondmem.speed,
                               _bondmem.counters.total_tx,
                               _bondmem.counters.total_rx,
                               _bondmem.counters.total_err,
                               _bondmem.linkfailures])
            return tabulate(_table, _header, floatfmt='.0f') + self.new_line()
        else:
            _header = ['', _('port'), _('speed'),
                       _('link_failures')]

            for _bondmem in _bondmembers.values():
                _printbondmem = PrintBondMember(_bondmem)
                _table.append([_printbondmem.linkstate,
                               "%s(%s)" % (_printbondmem.name,
                                           self.abbrev_bondstate(_bondmem)),
                               _printbondmem.speed,
                               _bondmem.linkfailures])
            return tabulate(_table, _header, floatfmt='.0f') + self.new_line()

    def clag_summary(self):
        """
        :return: clag summary details for 'netshow interface' for all ints
        """
        if self.iface.clag_enable == '1':
            return _('in_clag')

        return ''

    @property
    def summary(self):
        """
        :return: summary info for bonds for 'netshow interfaces'
        """
        _arr = []
        _arr.append(self.print_bondmems())
        if self.iface.is_l3():
            _arr.append(', '.join(self.iface.ip_address.allentries))
        elif self.iface.is_trunk():
            _arr += self.trunk_summary()
        elif self.iface.is_access():
            _arr += self.access_summary()
        _in_clag = self.clag_summary()
        if _in_clag:
            _clag_output = "(%s)" % (_in_clag)
            _arr += [_clag_output]
        return _arr

    def cli_output(self):
        """
        point to linux provider PrintBond cli_output function
        """
        return linux_print_bond.PrintBond.cli_output(self)
