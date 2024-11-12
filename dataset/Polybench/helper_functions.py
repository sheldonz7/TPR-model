import xml.etree.ElementTree as ET
import sys
import re

def parse_bambu_simulation(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        cycle_element = root.find('.//CYCLES')

        if cycle_element is not None:
            cycles_value = cycle_element.get('value')
            if cycles_value is not None:
                return int(float(cycles_value))

        print("Error: CYCLES element not found in the XML file")
        return None

    except Exception as e:
        print("Fail to parse the XML file: ", e)



def remove_vivado_script_optimization_steps(vivado_tcl_path, vivado_noop_tcl_path):
    lines = list()
    with open(vivado_tcl_path, "r") as f:
        lines = f.readlines()
    
    counter = 0
    with open(vivado_noop_tcl_path, "w+") as f:
        for line in lines:
            if (counter > 0):
                counter -= 1
                continue
            if line.find("# Optionally run optimization if there are timing violations after placement") != -1:
                counter = 4
                continue
            elif line.find("# Optionally run optimization if there are timing violations after routing") != -1:
                counter = 6
                continue
            else:
                f.write(line)


def extract_vitis_cycle(csynth_rpt_path):
    """ Parse HLS synthesis report to extract min and max latency cycles.
    
    Args: file_content (str): Content of the HLS synthesis report Returns: tuple: (min_latency, max_latency) in cycles, or (None, None) if not found """ 
    with open(csynth_rpt_path, "r") as f:
        file_content = f.read()
        # Look for the latency summary section
        
        latency_pattern = r'\|\s*Latency \(cycles\)\s*\|.*?\|\s*(\d+)\s*\|\s*(\d+)\s*\|' 
        
        
        # Search for the pattern in the file content
        match = re.search(latency_pattern, file_content, re.MULTILINE | re.DOTALL) 
        if match: 
            min_latency = int(match.group(1))
            max_latency = int(match.group(2))
            return min_latency, max_latency
        else:
            return None, None 


