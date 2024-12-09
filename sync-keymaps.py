"""
This module provides functionality to synchronize keyboard shortcuts between
Windows and Mac keymap XML files. It includes functions to load, save, and 
convert shortcuts, as well as to synchronize the keymaps between the two platforms.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import copy

def load_keymap(file_path):
    """
    Load an XML keymap file and return its root element.

    Args:
        file_path (str): The path to the keymap XML file.

    Returns:
        Element: The root element of the XML tree.
    """
    tree = ET.parse(file_path)
    return tree.getroot()

def save_keymap(root, file_path):
    """
    Save the XML tree to a file with pretty formatting, sorted by action ID,
    and without the XML declaration.

    Args:
        root (Element): The root element of the XML tree.
        file_path (str): The path where the XML file will be saved.
    """
    # Sort actions by their 'id' attribute
    actions = sorted(root.findall('action'), key=lambda a: a.get('id'))
    
    # Clear existing children and re-add sorted actions
    for child in list(root):
        root.remove(child)
    for action in actions:
        root.append(action)
    
    # Convert to string with pretty formatting
    xml_str = ET.tostring(root, encoding='unicode')
    
    # Parse and format with minidom for pretty printing
    import xml.dom.minidom
    dom = xml.dom.minidom.parseString(xml_str)
    
    # Remove extra whitespace between tags while keeping indentation
    pretty_xml = '\n'.join([line for line in dom.toprettyxml(indent='  ').split('\n') if line.strip()])
    
    # Remove the XML declaration if present
    if pretty_xml.startswith('<?xml'):
        pretty_xml = '\n'.join(pretty_xml.split('\n')[1:])
    
    # Write to file without XML declaration
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

def convert_shortcut(shortcut, to_mac=False):
    """
    Convert keyboard shortcuts between Windows and Mac formats.

    Args:
        shortcut (str): The shortcut string to convert.
        to_mac (bool): If True, convert from Windows to Mac format. 
                       If False, convert from Mac to Windows format.

    Returns:
        str: The converted shortcut string.
    """
    if to_mac:
        return shortcut.replace('ctrl', 'meta')
    return shortcut.replace('meta', 'ctrl')

def sync_keymaps(windows_file, mac_file):
    """
    Synchronize keyboard shortcuts between Windows and Mac keymap files,
    ensuring each keymap contains the union of shortcuts from both platforms.

    Args:
        windows_file (str): The path to the Windows keymap XML file.
        mac_file (str): The path to the Mac keymap XML file.
    """
    # Load both keymaps
    windows_root = load_keymap(windows_file)
    mac_root = load_keymap(mac_file)
    
    # Create dictionaries of actions for easier lookup
    windows_actions = {action.get('id'): action for action in windows_root.findall('action')}
    mac_actions = {action.get('id'): action for action in mac_root.findall('action')}
    
    # Function to add shortcuts to an action
    def add_shortcuts(action, shortcuts):
        existing_shortcuts = {s.get('first-keystroke') for s in action.findall('keyboard-shortcut')}
        for keystroke in shortcuts:
            if keystroke not in existing_shortcuts:
                new_shortcut = ET.SubElement(action, 'keyboard-shortcut')
                new_shortcut.set('first-keystroke', keystroke)
    
    # Collect all unique shortcuts for each action
    all_action_ids = set(windows_actions.keys()).union(mac_actions.keys())
    
    for action_id in all_action_ids:
        # Get or create actions
        windows_action = windows_actions.get(action_id)
        mac_action = mac_actions.get(action_id)
        
        if windows_action is None:
            windows_action = ET.SubElement(windows_root, 'action', {'id': action_id})
        
        if mac_action is None:
            mac_action = ET.SubElement(mac_root, 'action', {'id': action_id})
        
        # Collect shortcuts
        windows_shortcuts = {s.get('first-keystroke') for s in windows_action.findall('keyboard-shortcut')}
        mac_shortcuts = {s.get('first-keystroke') for s in mac_action.findall('keyboard-shortcut')}
        
        # Convert and union shortcuts
        mac_converted = {convert_shortcut(s, to_mac=False) for s in mac_shortcuts}
        windows_converted = {convert_shortcut(s, to_mac=True) for s in windows_shortcuts}
        
        # Union of all shortcuts
        all_windows_shortcuts = windows_shortcuts.union(mac_converted)
        all_mac_shortcuts = mac_shortcuts.union(windows_converted)
        
        # Add shortcuts to actions
        add_shortcuts(windows_action, all_windows_shortcuts)
        add_shortcuts(mac_action, all_mac_shortcuts)
    
    # Save the updated keymaps
    save_keymap(windows_root, windows_file)
    save_keymap(mac_root, mac_file)

if __name__ == '__main__':
    windows_keymap = 'Windows - Fraser.xml'
    mac_keymap = 'macOS - Fraser.xml'
    
    sync_keymaps(windows_keymap, mac_keymap)
    print("Keymap synchronization complete!")