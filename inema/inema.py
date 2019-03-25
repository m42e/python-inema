#!/usr/bin/python

from datetime import datetime
from pytz import timezone
import hashlib
import json
from lxml import etree
from zeep import Client
from pkg_resources import resource_stream, Requirement
import requests, zipfile
import io
import logging

__version__ = "0.6"

_logger = logging.getLogger(__name__)

products_json = resource_stream(__name__, "data/products.json").read().decode()
marke_products = json.loads(products_json)

formats_json = resource_stream(__name__, "data/formats.json").read().decode()
formats = json.loads(formats_json)

def get_product_price_by_id(ext_prod_id):
    price_float_str = marke_products[str(ext_prod_id)]['cost_price']
    return int(round(float(price_float_str) * 100))

# generate a 1C4A SOAP header
def gen_1c4a_hdr(partner_id, key_phase, key):
    # Compute 1C4A request hash accordig to Section 4 of service description
    def compute_1c4a_hash(partner_id, req_ts, key_phase, key):
        # trim leading and trailing spaces of each argument
        partner_id = partner_id.strip()
        req_ts = req_ts.strip()
        key_phase = key_phase.strip()
        key = key.strip()
        # concatenate with "::" separator
        inp = "%s::%s::%s::%s" % (partner_id, req_ts, key_phase, key)
        # compute MD5 hash as 32 hex nibbles
        md5_hex = hashlib.md5(inp.encode('utf8')).hexdigest()
        # return the first 8 characters
        return md5_hex[:8]

    def gen_timestamp():
        de_zone = timezone("Europe/Berlin")
        de_time = datetime.now(de_zone)
        return de_time.strftime("%d%m%Y-%H%M%S")

    nsmap={'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
           'v3':'http://oneclickforpartner.dpag.de'}
    r = etree.Element("{http://schemas.xmlsoap.org/soap/envelope/}Header", nsmap = nsmap)
    p = etree.SubElement(r, "{http://oneclickforpartner.dpag.de}PARTNER_ID")
    p.text = partner_id
    t = etree.SubElement(r, "{http://oneclickforpartner.dpag.de}REQUEST_TIMESTAMP")
    t.text = gen_timestamp()
    k = etree.SubElement(r, "{http://oneclickforpartner.dpag.de}KEY_PHASE")
    k.text = key_phase
    s = etree.SubElement(r, "{http://oneclickforpartner.dpag.de}PARTNER_SIGNATURE")
    s.text = compute_1c4a_hash(partner_id, t.text, key_phase, key)
    return [p, t, k, s]

class Internetmarke(object):
    wsdl_url = 'https://internetmarke.deutschepost.de/OneClickForAppV3/OneClickForAppServiceV3?wsdl'

    def __init__(self, partner_id, key, key_phase="1"):
        self.client = Client(self.wsdl_url)
        self.partner_id = partner_id
        self.key_phase = key_phase
        self.key = key
        self.soapheader = gen_1c4a_hdr(self.partner_id, self.key_phase, self.key)
        self.positions = []

    def authenticate(self, username, password):
        s = self.client.service
        r = s.authenticateUser(_soapheaders= self.soapheader, username=username, password=password)
        self.user_token = r.userToken
        self.wallet_balance = r.walletBalance

    def retrievePNGs(self, link):
        _logger.info("Retrieving PNGs from %s", link)
        r = requests.get(link, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        return [ z.read(f.filename) for f in z.infolist() ]

    def retrieve_manifest(self, link):
        _logger.info("Retrieving Manifest from %s", link)
        r = requests.get(link, stream=True)
        return r.content

    def retrievePreviewPNG(self, prod_code, layout = "AddressZone"):
        s = self.client.service
        r = s.retrievePreviewVoucherPNG(_soapheaders = self.soapheader,
                                        productCode = prod_code,
                                        voucherLayout = layout)
        _logger.info("retrievePreviewPNG result: %s", r)
        return r

    def retrievePreviewPDF(self, prod_code, page_format,
        layout = "AddressZone"):
        s = self.client.service
        r = s.retrievePreviewVoucherPDF(_soapheaders = self.soapheader,
                                        productCode = prod_code,
                                        pageFormatId = page_format,
                                        voucherLayout = layout)
        _logger.info("retrievePreviewPPDF result: %s", r)
        return r

    def retrievePageFormats(self):
        s = self.client.service
        r = s.retrievePageFormats(_soapheaders = self.soapheader)
        _logger.info("retrievePageFormats result: %s", r)
        return r


    def add_position(self, position):
        _logger.info("Adding position to basket: %s", position)
        self.positions.append(position)

    def clear_positions(self):
        _logger.info("Clearing positions from basket")
        self.positions = []

    def compute_total(self):
        total = 0
        for p in self.positions:
            total += get_product_price_by_id(p.productCode)
        return total

    def checkoutPDF(self, page_format):
        s = self.client.service
        # FIXME: convert ShoppingCartPosition to ShoppingCartPDFPosition
        _logger.info("Submitting basket with %u positions, total=%f", len(self.positions), self.compute_total())
        r = s.checkoutShoppingCartPDF(_soapheaders = self.soapheader,
                                  userToken = self.user_token,
                                  pageFormatId = page_format,
                                  positions = self.positions,
                                  total = self.compute_total(),
                                  createManifest = True,
                                  createShippingList = 2)
        _logger.info("PDF checkout result: %s", r)
        if r.link:
            pdf = requests.get(r.link, stream=True)
            r.pdf_bin = pdf.content
        if r.manifestLink:
            r.manifest_pdf_bin = self.retrieve_manifest(r.manifestLink)
        return r

    def checkoutPNG(self):
        s = self.client.service
        _logger.info("Submitting basket with %u positions, total=%f", len(self.positions), self.compute_total())
        r = s.checkoutShoppingCartPNG(_soapheaders = self.soapheader,
                                  userToken = self.user_token,
                                  positions = self.positions,
                                  total = self.compute_total(),
                                  createManifest = True,
                                  createShippingList = 2)
        _logger.info("PNG checkout result: %s", r)
        if r.link:
            # retrieve PNG images and store them in result object
            pngs = self.retrievePNGs(r.link)
            for i in range(0, len(pngs)):
                r.shoppingCart.voucherList.voucher[i].png_bin = pngs[i]
        if r.manifestLink:
            # retrieve manifest PDF and store in result object
            r.manifest_pdf_bin = self.retrieve_manifest(r.manifestLink)
        return r


    def build_addr(self, street, house, zipcode, city, country, additional = None):
        zclient = self.client
        atype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}Address')
        return atype(additional = additional, street = street,
                     houseNo = house, zip = zipcode, city = city,
                     country= country)

    def build_pers_name(self, first, last, salutation=None, title=None):
        zclient = self.client
        pntype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}PersonName')
        pn = pntype(firstname = first, lastname = last,
                    salutation = salutation, title = title)
        return pn

    def build_comp_addr(self, company, address, person = None):
        zclient = self.client
        cntype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}CompanyName')
        cn = cntype(company = company, personName = person)
        ntype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}Name')
        name = ntype(companyName = cn)
        atype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}NamedAddress')
        return atype(name = name, address = address)

    def build_pers_addr(self, first, last, address, salutation = None, title = None):
        zclient = self.client
        pn = self.build_pers_name(first, last, salutation, title)
        ntype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}Name')
        name = ntype(personName = pn)
        atype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}NamedAddress')
        return atype(name = name, address = address)

    def build_position(self, product, sender=None, receiver=None, layout="AddressZone", pdf=False, x=1, y=1, page=1):
        zclient = self.client
        abtype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}AddressBinding')
        postype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}VoucherPosition')
        if pdf:
            pos = 'ShoppingCartPDFPosition'
            args = { 'position': postype(labelX=x, labelY=y, page=page) }
        else:
            pos = 'ShoppingCartPosition'
            args = {}
        ptype = zclient.get_type('{http://oneclickforapp.dpag.de/V3}' + pos)
        ab = abtype(sender = sender, receiver = receiver) if sender and receiver else None
        return ptype(productCode = product, address = ab,
                voucherLayout = layout, **args)
