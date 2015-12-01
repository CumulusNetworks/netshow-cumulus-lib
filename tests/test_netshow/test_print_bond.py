# http://pylint-messages.wikidot.com/all-codes
# attribute defined outside init
# pylint: disable=W0201
# pylint: disable=R0913
# disable unused argument
# pylint: disable=W0613
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# disable invalid name
# pylint: disable=C0103
# pylint: disable=F0401
# pylint: disable=E0611
# pylint: disable=W0611

import netshow.cumulus.print_bond as print_bond
import netshowlib.cumulus.bond as cumulus_bond
import mock
from asserts import assert_equals, mod_args_generator
import io


class TestPrintBondMember(object):
    def setup(self):
        iface = cumulus_bond.BondMember('swp22')
        self.piface = print_bond.PrintBondMember(iface)

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_speed(self, mock_read_sys):
        values = {('speed', ): '1000',
                  ('carrier',): '1',
                  ('operstate',): 'up'}
        self.piface.iface._asic = {'asicname': 'xe2', 'initial_speed': '10000'}
        mock_read_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.speed, '1G(sfp)')


class TestPrintBond(object):
    def setup(self):
        iface = cumulus_bond.Bond('bond0')
        self.piface = print_bond.PrintBond(iface)

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    @mock.patch('netshowlib.linux.iface.Iface.is_access')
    @mock.patch('netshowlib.linux.iface.Iface.is_trunk')
    @mock.patch('netshowlib.linux.iface.Iface.is_l3')
    def test_summary_in_clag(self, mock_is_l3, mock_is_trunk,
                             mock_is_access, mock_from_sys):
        values = {('carrier',): '1',
                  ('operstate',): 'up',
                  ('speed',): '1000',
                  ('bonding/mode',): '802.3ad 4',
                  ('bonding/slaves',): 'swp2 swp3',
                  ('bonding/xmit_hash_policy',): 'layer3+4 1',
                  ('bonding/min_links',): '2',
                  ('bonding/clag_enable',): '1'}

        mock_from_sys.side_effect = mod_args_generator(values)
        mock_is_l3.return_value = False
        mock_is_access.return_value = False
        mock_is_trunk.return_value = False
        _output = self.piface.summary
        assert_equals(_output[1], '(in_clag)')

    # GORY mess of a test..but very helpful
    @mock.patch('netshowlib.cumulus.asic.linux_common.exec_command')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    @mock.patch('netshowlib.linux.iface.Iface.read_symlink')
    def test_bondmem_details(self, mock_symlink, mock_read_from_sys, mock_file_oneline,
                             mock_exec):
        values3 = {
            ('/sbin/ethtool -S swp2',): io.open('tests/test_netshowlib/ethtool_swp.txt').read(),
            ('/sbin/ethtool -S swp3',): io.open('tests/test_netshowlib/ethtool_swp.txt').read(),
            ('lspci -nn',): io.open('tests/test_netshowlib/lspci_output.txt', 'rb').read()
        }

        mock_exec.side_effect = mod_args_generator(values3)
        values10 = {
            ('.pdbrc',): io.open('tests/test_netshow/test_pdbrc'),
            ('/proc/net/bonding/bond0',): io.open('tests/test_netshow/proc_net_bonding.txt'),
            ('/var/lib/cumulus/porttab',): io.open('tests/test_netshowlib/xe_porttab'),
            ('/etc/bcm.d/config.bcm',): io.open('tests/test_netshowlib/config_xe.bcm')
        }

        values1 = {('carrier',): '1',
                   ('operstate',): 'up',
                   ('speed',): '1000',
                   ('bonding/mode',): '802.3ad 4',
                   ('bonding/slaves',): 'swp2 swp3',
                   ('bonding/xmit_hash_policy',): 'layer3+4 1',
                   ('bonding/min_links',): '2',
                   ('ifalias',): None}
        values2 = {'/sys/class/net/bond0/bonding/ad_sys_priority': '65535',
                   '/sys/class/net/bond0/bonding/lacp_rate': 'slow 0'}
        values5 = {('master',): 'bond0'}
        mock_symlink.side_effect = mod_args_generator(values5)
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        with mock.patch('io.open') as mock_open2:
            mock_open2.side_effect = mod_args_generator(values10)
#            from nose.tools import set_trace; set_trace()
            _output = self.piface.bondmem_details()
            outputtable = _output.split('\n')
            assert_equals(outputtable[0].split(),
                          ['port', 'speed', 'tx', 'rx', 'err',
                           'link_failures'])
            assert_equals(outputtable[2].split(),
                          ['up', 'swp2(P)', '1G(sfp)', '1500',
                           '600', '30', '11'])
            assert_equals(outputtable[3].split(),
                          ['up', 'swp3(N)', '1G', '1500', '600', '30', '0'])
