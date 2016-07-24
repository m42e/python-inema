This is a python module for interfacing the "Internetmarke" API provided
by the German postal company "Deutsche Post".  It implements V3 of this
API.

The Internetmarke API allwos you to buy online franking for national and
international postal products like post cardsd and letters of all weight
classes and service classes (normal, registered, ...).

In order to use this module, you will need to be registered with
Deutsche Post for accessing the "1C4A Webservice".  You can request
related details from pcf-1click@deutschepost.de.  Upon registration,
you will recevie your individual parameters PARTNER_ID, KEY and
KEY_PHASE.

Furthermore, for actual payment of purchases made via this API, you will
need the user name (email address) and password to a "Portokasse"
acount.

This module makes use of the farily new "zeep" module for SOAP/WSDL.
