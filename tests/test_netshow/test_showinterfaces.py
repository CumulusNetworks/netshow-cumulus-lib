# http://pylint-messages.wikidot.com/all-codes
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

from asserts import assert_equals, mod_args_generator
from netshow.cumulus.show_interfaces import ShowInterfaces
import mock

class TestCumulusShowInterfaces(object):
    def setup(self):
        self.showint = ShowInterfaces()

    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.common.read_file')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.common.exec_command')
    @mock.patch('netshowlib.linux.common.read_symlink')
    @mock.patch('netshowlib.linux.iface.Iface.is_bridgemem')
    @mock.patch('netshowlib.cumulus.iface.Iface.stp_state')
    def todo_single_iface_json(self,
                               mock_stp_state,
                               mock_is_bridgemem,
                               mock_symlink,
                               mock_exec,
                               mock_listdir,
                               mock_file,
                               mock_read_oneline,
                               mock_os_path_exists):

        values10 = {('/sys/class/net/swp3/brif',): False,
                    ('/sys/class/net/swp3',): True,
                    ('/sys/class/net/swp3/bonding',): False,
                    ('/sys/class/net/swp3/master/bonding',): False,
                    ('sys/class/net/swp3/brport/vlans',): True,
                    ('/sys/class/net/swp3/carrier',): True,
                    ('/sys/class/net/swp3.1/brport',): True,
                    }
        mock_os_path_exists.side_effect = mod_args_generator(values10)
        values4 = {('/sys/class/net',): ['swp3', 'swp3.1', 'swp3.2'],
                   ('/sys/class/net/br0/brif',): ['swp3'],
                   ('/sys/class/net/br1/brif',): ['swp3.1'],
                   ('/sys/class/net/br2/brif',): ['swp3.2']
                   }
        mock_is_bridgemem.return_value = True
        mock_stp_state.return_value = '2'
        mock_listdir.side_effect = mod_args_generator(values4)
        values3 = {('lspci -nn',): '',
                   ('/sbin/ethtool -S swp3', ): '',
                   ('/sbin/mstpctl showall',): open(
                       'tests/test_netshowlib/mstpctl_showall').read(),
                   ('/usr/sbin/lldpctl -f xml',): '<xml></xml>'}
        mock_exec.side_effect = mod_args_generator(values3)
        values = {('bridge/stp_state',): '2',
                  ('brport/vlans',): None,
                  ('/sys/class/net/swp3/carrier',): '1',
                  ('/sys/class/net/swp3/speed',): '1000',
                  ('/sys/class/net/swp3/brport/vlans',): None}
        mock_read_oneline.side_effect = mod_args_generator(values)
        values5 = {
            ('/sys/class/net/swp3/brport/bridge',): 'br0',
            ('/sys/class/net/swp3.1/brport/bridge',): 'br1',
            ('/sys/class/net/swp3.2/brport/bridge',): 'br2'
        }
        mock_symlink.side_effect = mod_args_generator(values5)
        self.showint.single_iface = 'swp3'
        self.showint.use_json = True
        _output = self.showint.print_single_iface()
        assert_equals(_output, '')
