#
# Blender OSC Camera Sync
#
# Sends camera parameters via OSC to ossia score or other OSC receivers
#

bl_info = {
    "name": "OSC Camera Sync",
    "author": "Based on blender-addon-shmdata",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Properties > Camera Data > OSC Camera Sync",
    "description": "Send camera parameters via OSC (for ossia score)",
    "category": "Import-Export",
}

import bpy

# Check for python-osc
OSC_AVAILABLE = False
OSC_ERROR = ""

try:
    from pythonosc import udp_client
    OSC_AVAILABLE = True
except ImportError as e:
    OSC_ERROR = str(e)


def register():
    from . import properties
    from . import operators
    
    properties.register()
    operators.register()


def unregister():
    from . import operators
    from . import properties
    
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
