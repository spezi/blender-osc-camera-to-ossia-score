#
# Operators for OSC Camera Sync
#

import bpy
import math
from bpy.types import Operator
from mathutils import Vector
from typing import Dict, Optional

# OSC Import
try:
    from pythonosc import udp_client
    from pythonosc import osc_bundle_builder
    from pythonosc import osc_message_builder
    OSC_OK = True
except ImportError:
    udp_client = None
    osc_bundle_builder = None
    osc_message_builder = None
    OSC_OK = False


# ============================================================================
# Coordinate Conversion
# ============================================================================

def blender_to_ossia_coords(vec):
    """Transform Blender Z-up to ossia Y-up: (x, y, z) -> (x, z, -y)"""
    x, y, z = vec
    return (x, z, -y)


# ============================================================================
# Camera OSC Sync
# ============================================================================

class CameraOscTarget:
    """Represents an active OSC camera sync"""
    
    def __init__(self, object_name: str, client, address_prefix: str, 
                 look_distance: float, send_bundled: bool):
        self.object_name = object_name
        self.client = client
        self.address_prefix = address_prefix.rstrip('/')  # Remove trailing slash
        self.look_distance = look_distance
        self.send_bundled = send_bundled
        self.last_data = None  # Cache to avoid sending duplicates


class CameraOscSyncer:
    """Manages camera OSC sync"""
    
    targets: Dict[str, CameraOscTarget] = {}
    _handler_registered = False
    
    @classmethod
    def add_target(cls, target: CameraOscTarget):
        cls.targets[target.object_name] = target
        cls._ensure_handler()
        # Send initial data
        cls._send_camera_data(target)
    
    @classmethod
    def remove_target(cls, object_name: str):
        if object_name in cls.targets:
            del cls.targets[object_name]
        
        if not cls.targets:
            cls._remove_handler()
    
    @classmethod
    def _ensure_handler(cls):
        if not cls._handler_registered:
            bpy.app.handlers.depsgraph_update_post.append(cls._depsgraph_callback)
            cls._handler_registered = True
    
    @classmethod
    def _remove_handler(cls):
        if cls._handler_registered:
            try:
                bpy.app.handlers.depsgraph_update_post.remove(cls._depsgraph_callback)
            except:
                pass
            cls._handler_registered = False
    
    @classmethod
    def _depsgraph_callback(cls, scene, depsgraph):
        """Called when scene updates - check if camera changed"""
        if not cls.targets:
            return
        
        for update in depsgraph.updates:
            obj_name = None
            
            # Check for Object or Camera data updates
            if isinstance(update.id, bpy.types.Object):
                if update.id.type == 'CAMERA':
                    obj_name = update.id.name
            elif isinstance(update.id, bpy.types.Camera):
                # Find the object using this camera data
                for obj in bpy.data.objects:
                    if obj.type == 'CAMERA' and obj.data == update.id:
                        obj_name = obj.name
                        break
            
            if obj_name and obj_name in cls.targets:
                target = cls.targets[obj_name]
                cls._send_camera_data(target)
    
    @classmethod
    def _send_camera_data(cls, target: CameraOscTarget):
        """Send camera parameters via OSC"""
        try:
            obj = bpy.data.objects.get(target.object_name)
            if obj is None or obj.type != 'CAMERA':
                return
            
            cam_data = obj.data
            
            # Position (direkt aus location, wie im funktionierenden Script)
            blender_pos = tuple(obj.location)
            ossia_pos = blender_to_ossia_coords(blender_pos)
            
            # Center berechnen (Kamera schaut in -Z Richtung lokal)
            forward = obj.matrix_world.to_quaternion() @ Vector((0, 0, -1))
            blender_center = tuple(obj.location + forward * target.look_distance)
            ossia_center = blender_to_ossia_coords(blender_center)
            
            # FOV (in Grad, ossia verwendet vertikales FOV)
            fov = math.degrees(cam_data.angle)
            
            # Clipping
            near = cam_data.clip_start
            far = cam_data.clip_end
            
            # Create data tuple for comparison
            current_data = (ossia_pos, ossia_center, fov, near, far)
            
            # Skip if data hasn't changed (avoid OSC spam)
            if target.last_data == current_data:
                return
            target.last_data = current_data
            
            prefix = target.address_prefix
            
            if target.send_bundled:
                # Send as OSC bundle (atomic)
                bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
                
                # Position
                msg = osc_message_builder.OscMessageBuilder(address=f"{prefix}/position")
                msg.add_arg(float(ossia_pos[0]))
                msg.add_arg(float(ossia_pos[1]))
                msg.add_arg(float(ossia_pos[2]))
                bundle.add_content(msg.build())
                
                # Center
                msg = osc_message_builder.OscMessageBuilder(address=f"{prefix}/center")
                msg.add_arg(float(ossia_center[0]))
                msg.add_arg(float(ossia_center[1]))
                msg.add_arg(float(ossia_center[2]))
                bundle.add_content(msg.build())
                
                # FOV
                msg = osc_message_builder.OscMessageBuilder(address=f"{prefix}/fov")
                msg.add_arg(float(fov))
                bundle.add_content(msg.build())
                
                # Near
                msg = osc_message_builder.OscMessageBuilder(address=f"{prefix}/near")
                msg.add_arg(float(near))
                bundle.add_content(msg.build())
                
                # Far
                msg = osc_message_builder.OscMessageBuilder(address=f"{prefix}/far")
                msg.add_arg(float(far))
                bundle.add_content(msg.build())
                
                target.client.send(bundle.build())
            else:
                # Send as individual messages
                target.client.send_message(f"{prefix}/position", list(ossia_pos))
                target.client.send_message(f"{prefix}/center", list(ossia_center))
                target.client.send_message(f"{prefix}/fov", fov)
                target.client.send_message(f"{prefix}/near", near)
                target.client.send_message(f"{prefix}/far", far)
                
        except Exception as e:
            print(f"[OSC Camera] Error sending data: {e}")


# ============================================================================
# Operator
# ============================================================================

class OSC_OT_camera_sync(Operator):
    """Sync camera parameters via OSC"""
    bl_idname = "osc.camera_sync"
    bl_label = "Sync Camera via OSC"
    
    def execute(self, context):
        if not OSC_OK:
            self.report({'ERROR'}, "python-osc library not available")
            return {'CANCELLED'}
        
        obj = context.active_object
        if obj is None or obj.type != 'CAMERA':
            self.report({'ERROR'}, "Select a camera")
            return {'CANCELLED'}
        
        camera = obj.data
        settings = camera.osc_camera
        
        if settings.active:
            # Stop sync
            settings.active = False
            CameraOscSyncer.remove_target(obj.name)
            self.report({'INFO'}, f"Stopped OSC sync for {obj.name}")
        else:
            # Start sync
            try:
                # Create OSC client
                client = udp_client.SimpleUDPClient(settings.host, settings.port)
                
                target = CameraOscTarget(
                    object_name=obj.name,
                    client=client,
                    address_prefix=settings.address_prefix,
                    look_distance=settings.look_distance,
                    send_bundled=settings.send_bundled
                )
                
                CameraOscSyncer.add_target(target)
                settings.active = True
                
                self.report({'INFO'}, f"OSC sync started: {settings.host}:{settings.port}{settings.address_prefix}")
                
            except Exception as e:
                self.report({'ERROR'}, f"Failed to start OSC sync: {e}")
                return {'CANCELLED'}
        
        return {'FINISHED'}


# Registration
classes = [
    OSC_OT_camera_sync,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Stop all active syncs
    for name in list(CameraOscSyncer.targets.keys()):
        CameraOscSyncer.remove_target(name)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
