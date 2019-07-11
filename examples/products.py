#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from inema import ProductInformation
import json

# you have to fill the below with your login details for the ProdWS Service
USER = "xxx"
PASS = "yyyyyy"
MANDANTID = "zzzzz"

#logging.basicConfig(level=logging.INFO)

im = ProductInformation(USER, PASS, MANDANTID)
data = im.getProductList()
# print data

if data['success']:
    products = {}

    for ele in data['Response']['salesProductList']['SalesProduct']:
        international = True if ele['extendedIdentifier']['destination'] == 'international' else False
        id = ele['extendedIdentifier']['externIdentifier'][0]['id']
        name = ele['extendedIdentifier']['externIdentifier'][0]['name']
        cost_price = ele['priceDefinition']['price']['commercialGrossPrice']['value']
        weight = ele['weight']
        if weight:
            products[id] = {
                'international': international,
                'cost_price': unicode(cost_price),
                'name': name,
                'max_weight': unicode(weight['maxValue'])
            }

    print json.dumps(products)

else:
    print 'ERROR: %s' % data['Exception']
