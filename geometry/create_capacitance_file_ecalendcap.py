import xml.etree.ElementTree as ET
import sys
import os
import re

deg_fac = 0.01745  # base units are radians
rad_fac = 1.0

mm_fac = 1.0  # base units are mm
cm_fac = 10.
m_fac = 1000.

def val_with_units(valstr):
    """
    Parse a string of the form value*units and return value in base units

    Args:
       valstr(str): string to be parsed
    """

    splitstr = valstr.split('*')
    if len(splitstr) != 2 :
        print("Error in val_with_units: input not properly formatted.  Should be value*unit")
        return ValueError
    
    inval = float(splitstr[0])
    unit = splitstr[1]

    if unit == "rad":
        return inval*rad_fac
    else:
        if unit == "deg":
            return inval*deg_fac
        else:
            if unit == "mm":
                return inval*mm_fac
            else:
                if unit == "cm":
                    return inval*cm_fac
                else:
                    if unit == "m":
                        return inval*m_fac
                    else:
                        print("Error: unknown unit ", unit)
                        return ValueError

def process_includes(element, base_path):
    """
    Recursively process <include ref="file"/> tags in the element tree.
    
    Args:
        element: The XML element to process
        base_path (str): Base path for resolving relative file paths
    """
    # Find all include tags
    include_elements = element.findall("include")
    
    for include_elem in include_elements:
        ref = include_elem.get("ref")
        
        if ref:
            # Resolve the file path
            include_file = os.path.join(base_path, ref)
            
            try:
                # Parse the included file
                included_tree = ET.parse(include_file)
                included_root = included_tree.getroot()
                
                # Recursively process includes in the included file
                included_base_path = os.path.dirname(os.path.abspath(include_file))
                process_includes(included_root, included_base_path)
                
                # Replace the include element with the included content
                parent = element.find(f".//{include_elem.tag}/..")
                if parent is None:
                    # Find parent manually
                    for parent_candidate in element.iter():
                        if include_elem in list(parent_candidate):
                            parent = parent_candidate
                            break
                
                if parent is not None:
                    index = list(parent).index(include_elem)
                    parent.remove(include_elem)
                    
                    # Insert included children at the same position
                    for i, child in enumerate(included_root):
                        parent.insert(index + i, child)
                else:
                    # If include is at root level, extend root with included children
                    index = list(element).index(include_elem)
                    element.remove(include_elem)
                    for i, child in enumerate(included_root):
                        element.insert(index + i, child)
            
            except FileNotFoundError:
                print(f"Warning: Include file '{include_file}' not found.")
            except ET.ParseError as e:
                print(f"Error parsing include file '{include_file}': {e}")


def is_expression(value):
        """Check if value is an expression (contains operators or variable names)."""
        return any(op in value for op in ['+', '-', '*', '/', '(', ')']) or \
               any(c.isalpha() for c in value)

def evaluate_expression(expr, constants):
        """Safely evaluate an expression with constant substitution."""
        print("IN HERE")
        evaluated_expr = str(expr)
        print("STILL HERE")

        print("a",evaluated_expr,"b")
        print("simple test: ", eval(evaluated_expr, {"__builtins__": {}}, {}))
          
        # Replace constant names with their values
        for const_name in sorted(constants.keys(), key=len, reverse=True):
            pattern = r'\b' + re.escape(const_name) + r'\b'
            replacement = str(constants[const_name])
            evaluated_expr = re.sub(pattern, replacement, evaluated_expr)
            print (evaluated_expr)
            
        print("STILL STILL HERE")
        # Safely evaluate
        print("Here's what I'm trying to return: ", eval(evaluated_expr, {"__builtins__": {}}, {}))
        
        return eval(evaluated_expr, {"__builtins__": {}}, {})    
    
def resolve_expressions(expressions, constants, max_iterations=10):
        """Resolve expressions iteratively."""
        iteration = 0
        
        while expressions and iteration < max_iterations:
            iteration += 1
            resolved = []
            
            for name, expr in list(expressions.items()):
                try:
                    print("Trying to evaluate ", expr, val_with_units(expr))
                    evaluated = evaluate_expression(str(val_with_units(expr)), constants)
                    print(name, evaluated)
                    constants[name] = evaluated
                    resolved.append(name)
                except Exception as e:
                    # Still can't evaluate, try next iteration
                    print("Well that didn't work")
                    pass
            
            for name in resolved:
                print(name)
                del expressions[name]
            
            if not resolved and expressions:
                print(f"Warning: Unresolvable expressions: {list(expressions.keys())}")
                break
            
def read_xml_file(filename):
    """
    Read and parse an XML file, then display its contents.
    
    Args:
        filename (str): Path to the XML file
    """
    try:
        # Parse the XML file
        tree = ET.parse(filename)
        xmlroot = tree.getroot()
        
        process_includes(xmlroot, "../../k4geo/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/")
        
        print(f"Successfully opened: {filename}\n")
        print(f"Xmlroot tag: {xmlroot.tag}\n")
        print("XML Contents:")
        print("-" * 50)

        constants = {}
        expressions = {}
        #find all the constants, and evaluate accordingly
        print("Looking for constants")
        for const_elem in xmlroot.iter():

            print("HEY ", const_elem)
            name = const_elem.get('name')
            value = const_elem.get('value')
                
            if not name or not value:
                print(f"Warning: Constant missing name or value attribute")
                continue
                
            if not is_expression(value):
                try:
                    constants[name] = float(value)
                except ValueError:
                    try:
                        constants[name] = float(val_with_units(value))
                    except ValueError:
                        print(f"Warning: Constant cannot be evaluated")
                        continue
            else:
                expressions[name] = value

            resolve_expressions(expressions, constants)

            print("All Constants:")
             
            for name, value in constants:
                print(f"  {name} = {value}")
                 
        # Loop over all elements
        for element in xmlroot.iter():

            
       
#            print("What's the name ",element.get("name")) 

            if element.get("name") == "BladeAngle1" :
                print("Now the blade angle is ", element.get("value"))
                print("which in radians is", val_with_units(element.get("value")))

            if element.get("name") == "ECalEndcapRmin1":
                print("Wheel 1 inner radius : ", element.get("value"))
                      
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python script.py <xml_file>")
        print("Example: python script.py data.xml")
        sys.exit(1)
    
    xml_filename = sys.argv[1]
    read_xml_file(xml_filename)

if __name__ == "__main__":
    main()
