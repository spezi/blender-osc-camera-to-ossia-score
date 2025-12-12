#
# Properties and UI Panels for OSC Camera Sync
#

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty, FloatProperty


class OscCameraSettings(bpy.types.PropertyGroup):
    """Settings for camera OSC sync"""
    
    active: BoolProperty(
        name="Sync Active",
        description="True if camera parameters are being sent via OSC",
        default=False,
        options={'SKIP_SAVE'}
    )
    
    host: StringProperty(
        name="Host",
        description="OSC target host/IP address",
        default="127.0.0.1",
        maxlen=256
    )
    
    port: IntProperty(
        name="Port",
        description="OSC target port",
        default=9000,
        min=1,
        max=65535
    )
    
    address_prefix: StringProperty(
        name="Address Prefix",
        description="OSC address prefix (e.g. /camera results in /camera/position, /camera/fov, etc.)",
        default="/camera",
        maxlen=256
    )
    
    look_distance: FloatProperty(
        name="Look Distance",
        description="Distance to calculate the look-at center point",
        default=1.0,
        min=0.1,
        max=10000.0
    )
    
    send_bundled: BoolProperty(
        name="Send as Bundle",
        description="Send all parameters as a single OSC bundle (atomic update)",
        default=True
    )


class OSC_PT_camera_panel(bpy.types.Panel):
    """Panel for OSC camera sync settings"""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "OSC Camera Sync"
    bl_idname = "OSC_PT_camera_panel"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        camera = context.camera
        settings = camera.osc_camera
        
        # Import status
        from . import OSC_AVAILABLE, OSC_ERROR
        if not OSC_AVAILABLE:
            box = layout.box()
            box.alert = True
            box.label(text="python-osc not found!", icon='ERROR')
            box.label(text="Install: pip install python-osc")
            return
        
        # Main controls
        row = layout.row(align=True)
        if settings.active:
            row.operator("osc.camera_sync", text="Stop Sync", icon='PAUSE')
            row.alert = True
        else:
            row.operator("osc.camera_sync", text="Start Sync", icon='PLAY')
        
        # Connection settings
        box = layout.box()
        box.label(text="OSC Connection:", icon='URL')
        col = box.column(align=True)
        col.prop(settings, "host")
        col.prop(settings, "port")
        
        # OSC settings
        box = layout.box()
        box.label(text="OSC Settings:", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(settings, "address_prefix")
        col.prop(settings, "send_bundled")
        
        # Camera settings
        box = layout.box()
        box.label(text="Camera:", icon='CAMERA_DATA')
        col = box.column(align=True)
        col.prop(settings, "look_distance")
        
        # Info - show OSC addresses
        if settings.active:
            box = layout.box()
            box.label(text="Sending to:", icon='CHECKMARK')
            prefix = settings.address_prefix
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text=f"{prefix}/position  [x, y, z]")
            col.label(text=f"{prefix}/center    [x, y, z]")
            col.label(text=f"{prefix}/fov       [degrees]")
            col.label(text=f"{prefix}/near      [float]")
            col.label(text=f"{prefix}/far       [float]")
            col.separator()
            col.label(text="Coordinates: Y-up (ossia/OpenGL)")


# Registration
classes = [
    OscCameraSettings,
    OSC_PT_camera_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Camera.osc_camera = bpy.props.PointerProperty(type=OscCameraSettings)


def unregister():
    del bpy.types.Camera.osc_camera
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
