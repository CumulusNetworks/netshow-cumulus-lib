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

from asserts import assert_equals
import netshow.cumulus.show as show
import mock
import sys


@mock.patch('netshow.cumulus.show.ShowInterfaces')
def test_run_show_interfaces(mock_showint):
    # netshow interfaces
    sys.argv = ['netshow', 'trunks']
    show.run()
    assert_equals(mock_showint.call_count, 1)


@mock.patch('netshow.cumulus.show.ShowSystem')
def test_run_show_system(mock_showsys):
    # netshow system
    sys.argv = ['netshow', 'system']
    show.run()
    assert_equals(mock_showsys.call_count, 1)


@mock.patch('netshow.cumulus.show.ShowNeighbors')
def test_run_lldp(mock_shownei):
    # netshow lldp
    sys.argv = ['netshow', 'lldp']
    show.run()
    assert_equals(mock_shownei.call_count, 1)


@mock.patch('netshow.cumulus.show.ShowCounters')
def test_run_show_counters(mock_showcounters):
    # netshow system
    sys.argv = ['netshow', 'counters']
    show.run()
    assert_equals(mock_showcounters.call_count, 1)
