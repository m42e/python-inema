#!/usr/bin/python

import logging
from inema import Internetmarke

# you have to fill the below with your 1C4A API access details
PARTNER_ID = "XXXXX"
KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
KEY_PHASE = "1"

# you have to fill the below with your login details for the PORTOKASSE
# payment system
USER = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
PASS = "XXXXXXXXXXX"

logging.basicConfig(level=logging.INFO)

im = Internetmarke(PARTNER_ID, KEY, KEY_PHASE)
im.authenticate(USER, PASS)

sysmo_addr = im.build_addr('Alt-Moabit','93','10559','Berlin','DEU')
sysmo_naddr = im.build_comp_addr('sysmocom - s.f.m.c. GmbH', sysmo_addr)

dest_addr = im.build_addr('Glanzstrasse','11','12437','Berlin','DEU')
dest_naddr = im.build_pers_addr('Harald', 'Welte', dest_addr)

position = im.build_position(1017, sysmo_naddr, dest_naddr)
im.add_position(position)

r = im.checkoutPNG()
