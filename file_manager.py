"""
File operations for basket data and spot price management
"""

import os
import json
import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path

class FileManager:
    """Handles file operations for basket data and spot price"""
    
    def __init__(self, config):
        self.config = config
        self.basket_dir = config['basket_dir']
        self.xml_schema = config['xml_schema']
        
        # Create directories
        Path(self.basket_dir).mkdir(exist_ok=True)
    

    
    def save_basket_json(self, basket_data):
        """Save basket data as JSON file"""
        basket_file = os.path.join(self.basket_dir, f"{basket_data['id']}.json")
        with open(basket_file, 'w') as f:
            json.dump(basket_data, f, indent=2)
        return basket_file
    
    def save_basket_xml(self, basket_data):
        """Save basket data as XML file"""
        xml_content = self._generate_xml(basket_data)
        xml_file = os.path.join(self.basket_dir, f"{basket_data['id']}.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)
        return xml_file
    
    def validate_xml(self, xml_file):
        """Validate XML against XSD schema"""
        try:
            if not os.path.exists(self.xml_schema):
                print("Warning: XSD schema not found, skipping validation")
                return True
                
            with open(self.xml_schema, 'r') as f:
                schema_root = etree.XML(f.read().encode())
            schema = etree.XMLSchema(schema_root)
            
            with open(xml_file, 'r') as f:
                xml_doc = etree.parse(f)
            
            return schema.validate(xml_doc)
        except Exception as e:
            print(f"XML validation error: {e}")
            return False
    
    def _generate_xml(self, basket_data):
        """Generate XML content with strict execution order"""
        root = ET.Element('basket')
        
        # Metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'id').text = basket_data['id']
        ET.SubElement(metadata, 'timestamp').text = basket_data['timestamp']
        ET.SubElement(metadata, 'type').text = basket_data['type']
        ET.SubElement(metadata, 'spotValue').text = str(basket_data['spotValue'])
        ET.SubElement(metadata, 'reference').text = str(
            basket_data.get('newReference', basket_data.get('reference'))
        )
        
        # Orders in strict execution sequence
        orders = ET.SubElement(root, 'orders')
        
        # Sort orders by execution_order if available, otherwise maintain original order
        sorted_orders = sorted(
            basket_data['orders'], 
            key=lambda x: x.get('execution_order', 999)
        )
        
        for order in sorted_orders:
            order_elem = ET.SubElement(orders, 'order')
            # Add execution order attribute for XML tracking
            if 'execution_order' in order:
                order_elem.set('execution_order', str(order['execution_order']))
            
            ET.SubElement(order_elem, 'action').text = order['action']
            ET.SubElement(order_elem, 'strike').text = str(order['strike'])
            ET.SubElement(order_elem, 'type').text = order['type']
            ET.SubElement(order_elem, 'quantity').text = str(order['qty'])
            ET.SubElement(order_elem, 'index').text = order['index']
            if 'price' in order:
                ET.SubElement(order_elem, 'price').text = str(order['price'])
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        return ET.tostring(root, encoding='unicode', xml_declaration=True)