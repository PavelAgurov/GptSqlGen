"""
    XML utils
"""

import xml.etree.ElementTree as ET


def get_as_xml(xml_string):
    """
    Get XML as ElementTree
    """
    return ET.fromstring(xml_string)

def get_text_by_xpath(xml, xpath):
    """
    Get text by xpath
    """
    return xml.find(xpath).text

def get_array_by_xpath(xml, xpath):
    """
    Get array by xpath
    """
    return [t.text for t in xml.findall(xpath)]

def xml_to_string(xml):
    """
    Convert XML to string
    """
    return ET.tostring(xml, encoding='unicode').strip()