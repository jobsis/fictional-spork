import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO
import xml.dom.minidom as minidom
import re

# Team name conversion dictionary
TEAM_MAPPING = {
    'HDM H1': 'HDM',
    'Hurley H1': 'HUR',
    'Den Bosch H1': 'DBO',
    'Rotterdam H1': 'ROT',
    'Amsterdam H1': 'AMS',
    'Pinoke H1': 'PIN',
    'Kampong H1': 'KAM',
    'Klein Zwitserland H1': 'KZ',
    'Oranje Rood H1': 'OR',
    'Laren H1': 'LAR',
    'Schaerweijde H1': 'SW',
    'Bloemendaal H1': 'BLO',
    'Nijmegen H1':'NIJ',
    'Ring Pass H1':'RP',
    'Tilburg H1':'TIL',
    'Victoria H1':'VIC',
    'Almere H1':'ALM',
    'SCHC H1':'SCHC',
    'Push H1':'PUSH',
    'Voordaan H1':'VRDN',
    'Berkel-Rodenrijs H1':'HBR',
    'Ede H1':'EDE',
    'Cartouche H1':'CAR',
    'Leiden H1':'LOHC'
}

def convert_filename(original_filename):
    """Convert filename from long format to short format"""
    try:
        # Remove .xml extension
        name_without_ext = original_filename.replace('.xml', '')
        
        # Pattern: YYYYMMDD_R##_Team1-Team2
        # Extract date, remove R##, and get team names
        pattern = r'^(\d{8})_R\d+_(.+)-(.+)$'
        match = re.match(pattern, name_without_ext)
        
        if match:
            date = match.group(1)
            team1_long = match.group(2).strip()
            team2_long = match.group(3).strip()
            
            # Convert team names
            team1_short = TEAM_MAPPING.get(team1_long, team1_long)
            team2_short = TEAM_MAPPING.get(team2_long, team2_long)
            
            # Create new filename
            new_filename = f"{date}_{team1_short}vs{team2_short}.xml"
            return new_filename
        else:
            # If pattern doesn't match, return original filename
            return original_filename
    except:
        return original_filename

def process_xml(xml_content):
    """Process XML content according to specifications"""
    try:
        # Parse the XML
        root = ET.fromstring(xml_content)
        
        # Create new root element
        new_root = ET.Element('file')
        
        # Process ALL_INSTANCES
        all_instances = root.find('ALL_INSTANCES')
        if all_instances is not None:
            new_all_instances = ET.SubElement(new_root, 'ALL_INSTANCES')
            
            # Process each instance
            for i, instance in enumerate(all_instances.findall('instance'), start=1):
                new_instance = ET.SubElement(new_all_instances, 'instance')
                
                # Add ID as number
                id_elem = ET.SubElement(new_instance, 'ID')
                id_elem.text = str(i)
                
                # Copy code, start, end
                for tag in ['code', 'start', 'end']:
                    elem = instance.find(tag)
                    if elem is not None:
                        new_elem = ET.SubElement(new_instance, tag)
                        new_elem.text = elem.text
                
                # Copy all label elements
                for label in instance.findall('label'):
                    new_label = ET.SubElement(new_instance, 'label')
                    text_elem = label.find('text')
                    if text_elem is not None:
                        new_text = ET.SubElement(new_label, 'text')
                        new_text.text = text_elem.text
        
        # Process ROWS
        rows = root.find('ROWS')
        
        # Collect unique codes from instances
        unique_codes = set()
        if all_instances is not None:
            for instance in all_instances.findall('instance'):
                code_elem = instance.find('code')
                if code_elem is not None and code_elem.text:
                    unique_codes.add(code_elem.text)
        
        # Create ROWS section
        new_rows = ET.SubElement(new_root, 'ROWS')
        
        if rows is not None:
            # Process existing rows
            row_dict = {}
            for row in rows.findall('row'):
                code_elem = row.find('code')
                if code_elem is not None and code_elem.text:
                    code = code_elem.text
                    r_elem = row.find('R')
                    g_elem = row.find('G')
                    b_elem = row.find('B')
                    
                    row_dict[code] = {
                        'R': r_elem.text if r_elem is not None else '56156',
                        'G': g_elem.text if g_elem is not None else '56156',
                        'B': b_elem.text if b_elem is not None else '56156'
                    }
            
            # Add any missing codes with default values
            for code in unique_codes:
                if code not in row_dict:
                    row_dict[code] = {'R': '56156', 'G': '56156', 'B': '56156'}
            
            # Sort and add rows
            for code in sorted(row_dict.keys()):
                new_row = ET.SubElement(new_rows, 'row')
                code_elem = ET.SubElement(new_row, 'code')
                code_elem.text = code
                
                for color in ['R', 'G', 'B']:
                    color_elem = ET.SubElement(new_row, color)
                    color_elem.text = row_dict[code][color]
        else:
            # Create rows from unique codes
            for code in sorted(unique_codes):
                new_row = ET.SubElement(new_rows, 'row')
                code_elem = ET.SubElement(new_row, 'code')
                code_elem.text = code
                
                for color in ['R', 'G', 'B']:
                    color_elem = ET.SubElement(new_row, color)
                    color_elem.text = '56156'
        
        # Convert to string with proper formatting
        xml_string = ET.tostring(new_root, encoding='unicode')
        
        # Pretty print
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="", encoding='UTF-8')
        
        # Clean up extra blank lines
        lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
        formatted_xml = '\n'.join(lines)
        
        return formatted_xml, None
    
    except Exception as e:
        return None, str(e)

def main():
    st.set_page_config(page_title="Hudlproof XML conversion", page_icon="📄")
    
    st.title("🔄 Hudlproof XML conversion")
    
    uploaded_files = st.file_uploader(
        "Upload XML files",
        type=['xml'],
        accept_multiple_files=True,
        help="You can upload multiple XML files at once"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        st.write("")  # Add some space
        
        # Process each file
        for idx, uploaded_file in enumerate(uploaded_files):
            # Read and process the file
            xml_content = uploaded_file.read()
            processed_xml, error = process_xml(xml_content)
            
            if error:
                st.error(f"❌ Error processing {uploaded_file.name}: {error}")
            else:
                # Get statistics
                try:
                    root = ET.fromstring(processed_xml)
                    instances_count = len(root.findall('.//instance'))
                    rows_count = len(root.findall('.//row'))
                    stats_text = f" ({instances_count} instances, {rows_count} rows)"
                except:
                    stats_text = ""
                
                # Convert filename
                new_filename = convert_filename(uploaded_file.name)
                
                # Download button with stats and converted filename
                st.download_button(
                    label=f"⬇️ Download {new_filename}{stats_text}",
                    data=processed_xml,
                    file_name=new_filename,
                    mime="application/xml",
                    key=f"download_{idx}_{uploaded_file.name}",
                    use_container_width=True
                )
    
    else:
        st.info("👆 Please upload one or more XML files to get started")

if __name__ == "__main__":
    main()
