# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
from netshowlib.cumulus import asic
import netshowlib.linux.common as linux_common
import mock
import io
from asserts import assert_equals, mock_open_str, mod_args_generator


@mock.patch('netshowlib.cumulus.asic.linux_common.exec_command')
def test_switch_asic(mock_exec_command):
    mock_exec_command.return_value = open(
        'tests/test_netshowlib/lspci_output.txt', 'rb').read()
    instance = asic.switching_asic_discovery()
    assert_equals(isinstance(instance, asic.BroadcomAsic), True)
    # no asic found
    mock_exec_command.side_effect = linux_common.ExecCommandException
    instance = asic.switching_asic_discovery()
    assert_equals(instance, None)


@mock.patch('netshowlib.cumulus.asic.linux_common.exec_command')
def test_cacheinfo(mock_exec):
    mock_exec.return_value = io.open(
        'tests/test_netshowlib/lspci_output.txt', 'rb').read()
    values = {
        ('/var/lib/cumulus/porttab',): io.open('tests/test_netshowlib/xe_porttab'),
        ('/etc/bcm.d/config.bcm',): io.open('tests/test_netshowlib/config_xe.bcm')
    }

    with mock.patch('io.open') as mock_open:
        mock_open.side_effect = mod_args_generator(values)
        _output = asic.cacheinfo()
        assert_equals(_output['kernelports']['swp1']['asicname'], 'xe0')
        assert_equals(_output['kernelports']['swp1']['initial_speed'], '10000')


@mock.patch('netshowlib.cumulus.asic.linux_common.exec_command')
def test_cacheinfo_asic_not_detected(mock_exec):
    mock_exec.side_effect = linux_common.ExecCommandException
    _output = asic.cacheinfo()
    assert_equals(_output,  {'asicports': {}, 'kernelports': {}})


@mock.patch('netshowlib.cumulus.asic.linux_common.exec_command')
def test_cacheinfo_ports_not_initialized(mock_exec):
    mock_exec.return_value = open(
        'tests/test_netshowlib/lspci_output.txt', 'rb').read()

    with mock.patch(mock_open_str()) as mock_open:
        mock_open.side_effect = IOError
        _output = asic.cacheinfo()
        assert_equals(_output,  {'name': 'broadcom', 'asicports': {}, 'kernelports': {}})
