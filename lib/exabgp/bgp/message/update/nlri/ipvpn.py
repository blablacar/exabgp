# encoding: utf-8
"""
bgp.py

Created by Thomas Mangin on 2012-07-08.
Copyright (c) 2009-2015 Exa Networks. All rights reserved.
"""

from exabgp.protocol.family import AFI
from exabgp.protocol.family import SAFI

from exabgp.bgp.message import OUT

from exabgp.bgp.message.update.nlri.nlri import NLRI
from exabgp.bgp.message.update.nlri.cidr import CIDR
from exabgp.bgp.message.update.nlri.labelled import Labelled
from exabgp.bgp.message.update.nlri.qualifier import RouteDistinguisher
from exabgp.bgp.message.update.nlri.qualifier import PathInfo

from exabgp.protocol.ip import IP
from exabgp.protocol.ip import NoNextHop


# ====================================================== IPVPN
# RFC 4364

@NLRI.register(AFI.ipv4,SAFI.mpls_vpn)
@NLRI.register(AFI.ipv6,SAFI.mpls_vpn)
class IPVPN (Labelled):
	__slots__ = ['rd']

	def __init__ (self, afi, safi, action=OUT.UNSET):
		Labelled.__init__(self, afi, safi, action)
		self.rd = RouteDistinguisher.NORD

	@classmethod
	def new (cls, afi, safi, packed, mask, labels, rd, nexthop=None, action=OUT.UNSET):
		instance = cls(afi,safi,action)
		instance.cidr = CIDR(packed, mask)
		instance.labels = labels
		instance.rd = rd
		instance.nexthop = IP.create(nexthop) if nexthop else NoNextHop
		instance.action = action
		return instance

	def extensive (self):
		return "%s%s%s%s%s" % (self.prefix(),str(self.labels),str(self.rd),str(self.path_info),str(self.rd))

	def __len__ (self):
		return Labelled.__len__(self) + len(self.rd)

	def __repr__ (self):
		nexthop = ' next-hop %s' % self.nexthop if self.nexthop else ''
		return "%s%s" % (self.extensive(),nexthop)

	def __eq__ (self, other):
		return \
			Labelled.__eq__(self, other) and \
			self.rd == other.rd

	@classmethod
	def has_rd (cls):
		return True

	def pack (self, negotiated=None):
		addpath = self.path_info.pack() if negotiated and negotiated.addpath.send(self.afi,self.safi) else ''
		mask = chr(len(self.labels)*8 + len(self.rd)*8 + self.cidr.mask)
		return addpath + mask + self.labels.pack() + self.rd.pack() + self.cidr.pack_ip()

	def index (self, negotiated=None):
		addpath = 'no-pi' if self.path_info is PathInfo.NOPATH else self.path_info.pack()
		mask = chr(len(self.labels)*8 + len(self.rd)*8 + self.cidr.mask)
		return addpath + mask + self.labels.pack() + self.rd.pack() + self.cidr.pack_ip()

	def _internal (self, announced=True):
		r = Labelled._internal(self,announced)
		if announced and self.rd:
			r.append(self.rd.json())
		return r

	# @classmethod
	# def _rd (cls, data, mask):
	# 	mask -= 8*8  # the 8 bytes of the route distinguisher
	# 	rd = data[:8]
	# 	data = data[8:]
	#
	# 	if mask < 0:
	# 		raise Notify(3,10,'invalid length in NLRI prefix')
	#
	# 	if not data and mask:
	# 		raise Notify(3,10,'not enough data for the mask provided to decode the NLRI')
	#
	# 	return RouteDistinguisher(rd), mask, data
	#
	# @classmethod
	# def unpack_mpls (cls, afi, safi, data, action, addpath):
	# 	pathinfo, data = cls._pathinfo(data,addpath)
	# 	mask, labels, data = cls._labels(data,action)
	# 	rd, mask, data = cls._rd(data,mask)
	# 	nlri, data = cls.unpack_cidr(afi,safi,mask,data,action)
	# 	nlri.path_info = pathinfo
	# 	nlri.labels = labels
	# 	nlri.rd = rd
	# 	return nlri,data
	#
	# @classmethod
	# def unpack_nlri (cls, afi, safi, data, addpath):
	# 	return cls.unpack_mpls(afi,safi,data,addpath)
