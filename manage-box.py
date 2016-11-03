#!/usr/bin/env python3
# Auto set-up DMZ ip for SFR and Numericable
# Made by Neavend [nsimon.fr] - Free to use

import time
import re
import socket
import fcntl
import struct
import binascii

from bs4 import BeautifulSoup
from robobrowser import RoboBrowser

# Change with yours
settings = {
	'credentials': {
		'login': 'admin',
		'password': 'password'
	},
	'interface': 'eth0',
	'backup_interface': 'wlan0',
	'server': 'http://nsimon.fr' # Server to check if online or offline
}

class ManageBox:
	credentials = settings['credentials']
	browser = RoboBrowser(history=True, parser="lxml")

	def __init__(self, force):		
		if not force:
			try:
				self.browser.open(settings['server'], timeout=3)
				print("Server seems to be working, no DMZ change needed")
				return
			except: pass

		self.login()
		self.hostname = socket.gethostname()
		#self.ip = socket.gethostbyname(socket.gethostname()) # Not working 100% TODO
		interface = settings['interface']
		self.mac = self.getHwAddr(interface)
		self.ip = self.get_local_ip(self.mac)
		if (self.ip is None):
			interface = settings['backup_interface']
			self.mac = self.getHwAddr(interface)
			self.ip = self.get_local_ip(self.mac)
			if (self.ip is None):
				raise Exception("Unable to find the IP for your {} interface [MAC: {}]".format(interface, self.mac))
		print("Your local IP is {}, setting DMZ to this adress...".format(self.ip))
		self.set_dmz(self.ip)
		print("Done.")

	def login(self):
		self.browser.open('http://192.168.0.1/config.html')
		form = self.browser.get_form(action='/goform/login')
		if (form is None):
			if ("YOUR GATEWAY" in str(self.browser.select)):
				return print('Already authentified as ' + self.credentials['login'])
			raise Exception("Authentication failed")
		form['loginUsername'] = self.credentials['login']
		form['loginPassword'] = self.credentials['password']
		self.browser.submit_form(form)
		#form = self.browser.get_form(action='/goform/login')
		#if form is not None:
		#	raise Exception("Authentication failed, please enter valid credentials")
		print('Authentified as ' + self.credentials['login'])

	def getHwAddr(self, ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		struc = struct.pack('256s', ifname[:15].encode('utf-8'))
		info = fcntl.ioctl(s.fileno(), 0x8927, struc)
		int_mac = str(binascii.hexlify(info)[36:48], 'utf-8')
		return ":".join([int_mac[i:i+2] for i in range(0, len(int_mac), 2)])

	def get_local_ip(self, mac):
		self.browser.open('http://192.168.0.1/reseau-pb6-moniteur.html')
		soup = BeautifulSoup(str(self.browser.select), "lxml")
		divs = soup.findAll("div", {"id": lambda L: L and L.startswith('apDiv') and 'mac'in L})
		for div in divs:
			addrs = div.getText().split('\n')
			if (addrs[1] == mac):
				return addrs[2]

	def set_dmz(self, ip):
		self.browser.open('http://192.168.0.1/reseau-pa7-DMZ.html')
		form = self.browser.get_form(action='/goform/WebUiRgDmz')
		if (form is None):
			raise Exception("Unable to get DMZ form")
		form['RgDmzAddr03'] = ip[-2:]
		self.browser.submit_form(form)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='An auto DMZ set-up using the SFR/Numericable web interface')
	parser.add_argument('--force', '-f', action="store_true", help="Forces update (Disables the server check)")
	ManageBox(parser.parse_args().force)
