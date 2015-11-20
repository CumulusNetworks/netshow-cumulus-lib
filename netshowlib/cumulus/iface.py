"""
Iface module for Cumulus Provider
"""
from netshowlib import netshowlib as nn
from netshowlib.linux import common as linux_common
from netshowlib.cumulus import common
from netshowlib.linux import iface as linux_iface
from netshowlib.cumulus import counters
from netshowlib.cumulus import asic as cumulus_asic
import re
import os

def portname_list():
    """
    :return: list of interfaces configured on the switch
    """
    return linux_iface.portname_list()

def iface(name, cache=None):
    """
    calls on checks to determine best interface type match for the named interface

    :return: regular :class:`cumulus.iface <netshowlib.cumulus.iface.Iface>` or \
    :class:`cumulus bond or bond member<netshowlib.cumulus.bond.Bond>`  or  \
    :class:`cumulus bridge or bridge member <netshowlib.cumulus.bridge.Bridge>` \
    interface
    """
    # create test iface.
    test_iface = Iface(name, cache=cache)
    if test_iface.is_bridge():
        bridge = nn.import_module('netshowlib.cumulus.bridge')
        return bridge.Bridge(name, cache=cache)
    elif test_iface.is_bond():
        bond = nn.import_module('netshowlib.cumulus.bond')
        return bond.Bond(name, cache=cache)
    elif test_iface.is_bondmem():
        bondmem = nn.import_module('netshowlib.cumulus.bond')
        return bondmem.BondMember(name, cache=cache)
    elif test_iface.is_bridgemem():
        bridge = nn.import_module('netshowlib.cumulus.bridge')
        return bridge.BridgeMember(name, cache=cache)
    return test_iface


class Iface(linux_iface.Iface):
    """ Cumulus Iface Class
    """

    def __init__(self, name, cache=None):
        linux_iface.Iface.__init__(self, name, cache)
        # import class that collects asic specific info
        # Not this doesn't run things like bcmcmd, just looks at flat files
        self.iface_initializers()
        self.common = common
        self.iface_class = Iface


    def iface_initializers(self):
        self._asic = None
        self._counters = None
        self._initial_speed = 0
        self._connector_type = 0

    def get_bridgemem_port_type(self):
        """
        :return: 0 if port is not a bridge member
        :return: 1 if  port is access port
        :return: 2 if port is a trunk port
        """
        _bridgemem_type = 0
        if self.vlan_filtering:
            if len(self.common.vlan_aware_vlan_list(self.name, 'vlans')) > 1:
                _bridgemem_type = 2
            else:
                _bridgemem_type = 1
        elif os.path.exists(self.sys_path('brport')):
            _bridgemem_type = 1

        if not self.is_subint():
            for subint in self.get_sub_interfaces():
                if os.path.exists(self.sys_path('brport', subint)):
                    _bridgemem_type = 2
                    break
        return _bridgemem_type



    def parent_is_vlan_aware_bridge(self):
        """
        :return: True if  parent of subint is vlan aware bridge.
        :return: False if  not subint or parent is not vlan aware bridge
        """
        if not self.is_subint():
            return False
        parent_ifacename = self.name.split('.')[0]
        parent_iface = self.iface_class(parent_ifacename)
        if self.common.is_vlan_aware_bridge(parent_iface.name):
            return True
        return False


    def is_svi_initial_test(self):
        """
        :return: sets port bitmap entry ``SVI_INT``. This applies to any \
            bridge subinterface in vlan aware mode
        """
        self._port_type = linux_common.clear_bit(self._port_type, linux_iface.SVI_INT)
        if self.parent_is_vlan_aware_bridge():
            self._port_type = linux_common.set_bit(self._port_type, linux_iface.SVI_INT)

    def is_svi(self):
        """
        :return: true if port is a management port
        """
        self.is_svi_initial_test()
        return linux_common.check_bit(self._port_type, linux_iface.SVI_INT)

    def is_mgmt_initial_test(self):
        """
        :return: sets port bitmap entry ``MGMT_INT``. \
            This applies to any ethX and lo interface.
        """
        self._port_type = linux_common.clear_bit(self._port_type, linux_iface.MGMT_INT)
        if re.match(r'eth\d+$', self.name):
            self._port_type = linux_common.set_bit(self._port_type, linux_iface.MGMT_INT)
        elif self.is_loopback():
            self._port_type = linux_common.set_bit(self._port_type, linux_iface.MGMT_INT)

    def is_mgmt(self):
        """
        :return: true if port is a management port
        """
        self.is_mgmt_initial_test()
        return linux_common.check_bit(self._port_type, linux_iface.MGMT_INT)

    def is_phy_initial_test(self):
        """
        :return: sets port bitmap entry ``PHY_INT``
        """
        self._port_type = linux_common.clear_bit(self._port_type, linux_iface.PHY_INT)
        if common.is_phy(self.name):
            self._port_type = linux_common.set_bit(self._port_type, linux_iface.PHY_INT)

    def is_phy(self):
        """
        :return: true if port is a physical port
        """
        self.is_phy_initial_test()
        return linux_common.check_bit(self._port_type, linux_iface.PHY_INT)

    @property
    def asic(self):
        """
        :return: the Switching asic class on the switch. used to get
        initial speed and port names
        """
        if not hasattr(self, '_asic'):
            return None

        if not self._asic:
            asicinstance = cumulus_asic.Asic(self.name, self._cache)
            self._asic = asicinstance.run()
        return self._asic

    @property
    def connector_type(self):
        """ type of connector physical switch has
        Returns:
            int. The return code::
                0 -- Unknown
                1 -- RJ45 (1G/10G)
                2 -- SFP+ (10G)
                3 -- QSFP (40G)
                4 -- QSFP (4x10G)
        """
        if not hasattr(self, '_connector_type'):
            return None

        if self._connector_type:
            return self._connector_type
        if re.match('swp\d+s\d+', self.name):
            return 4
        if self.asic:
            if self.asic.get('asicname').startswith('ge'):
                self._connector_type = 1
            elif self.initial_speed() == 10000:
                self._connector_type = 2
            elif self.initial_speed() == 40000:
                self._connector_type = 3
        return self._connector_type

    def initial_speed(self):
        """
        returns initial speed of the physical port
        """
        # if not a physical port, return none
        if self._initial_speed:
            return self._initial_speed
        if self.asic and self.is_phy():
            self._initial_speed = int(self.asic.get('initial_speed'))
        return self._initial_speed

    @property
    def speed(self):
        """
        :return: port speed in MB
        If the port is down (not admin down) unfortunately speed == 0. \
            Someone fix this pretty please?
        If port is admin down get speed from broadcom initialization files
        """
        if self.linkstate == 0:
            self._speed = self.initial_speed()
        else:
            self._speed = linux_iface.Iface.speed.fget(self)

        return self._speed

    @property
    def counters(self):
        if self.is_bond():
            self._counters = counters.Counters(name=self.name, cache=None)
            for _bondmem in self.members.values():
               for _key in self._counters.tx.keys():
                 self._counters.tx[_key] += _bondmem.counters.tx[_key]
               for _key in self._counters.rx.keys():
                 self._counters.rx[_key] += _bondmem.counters.rx[_key]
            return self._counters 
        if not self.is_phy():
            return None
        if self._counters is None:
            self._counters = counters.Counters(name=self.name,
                                               cache=self._cache)
        # check counters each time this property is called
        self._counters.run()
        return self._counters

    @property
    def vlan_filtering(self):
        """
        :return: Determines if port is vlan aware or not
        """
        if self.read_from_sys('brport/vlans'):
            return True
        return False
