"""
    Utilities for creating a KML (Google Maps) file
"""
import xml.etree.ElementTree as ET

ET.register_namespace("kml", "http://www.opengis.net/kml/2.2")

def CDATA(text=None):
    element = ET.Element('![CDATA[')
    element.text = text
    return element

# http://stackoverflow.com/questions/174890/how-to-output-cdata-using-elementtree
ET._original_serialize_xml = ET._serialize_xml
def _serialize_xml(write, elem, qnames, namespaces, coding):
    if elem.tag == '![CDATA[':
        write("\n<%s%s]]>\n" % (
                elem.tag, elem.text))
        return
    return ET._original_serialize_xml(
        write, elem, qnames, namespaces, coding)
ET._serialize_xml = ET._serialize['xml'] = _serialize_xml


class KmlCreator(object):
    """ Simple object to create a KML file for Google Earth """
    def __init__(self):
        self.root = ET.Element("{http://www.opengis.net/kml/2.2}kml")
        self.document = ET.SubElement(self.root, "Document")

        open_el = ET.SubElement(self.document, "open")
        open_el.text = "1"

    def write_name(self, name):
        name_el = ET.SubElement(self.document, "name")
        name_el.text = name

    def write_placemark(self, name, description, lat, lon, altitude=0):
        placemark_el = ET.SubElement(
            self.document, "Placemark")

        name_el = ET.SubElement(placemark_el, "name")
        name_el.text = name

        if description:
            description_el = ET.SubElement(
                placemark_el, "description")
            description_el.append(CDATA(description.replace('\n', '<br/>')))

        point_el = ET.SubElement(placemark_el, "Point")
        coords_el = ET.SubElement(
            point_el, "coordinates")
        coords_el.text = "{lon},{lat},{alt}".format(
            lon=lon, lat=lat, alt=altitude)

    def write(self, f):
        tree = ET.ElementTree(self.root)
        tree.write(
            f,
            encoding='utf-8',
            xml_declaration=True,
            method="xml")
