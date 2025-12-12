Here is the English translation:

---

# Blender OSC Camera Sync

Blender add-on for sending camera parameters via OSC (Open Sound Control).

Ideal for integration with ossia score, Resolume, TouchDesigner, and other OSC-capable applications.

## Features

* **Real-time sync**: Sends camera parameters whenever they change
* **Coordinate conversion**: Automatically converts Blender’s Z-up to ossia/OpenGL Y-up
* **OSC bundle support**: Atomic updates of all parameters
* **Configurable**: Adjustable host, port, and OSC addresses

## Sent Parameters

| OSC Address        | Data        | Description              |
| ------------------ | ----------- | ------------------------ |
| `/camera/position` | `[x, y, z]` | Camera position (Y-up)   |
| `/camera/center`   | `[x, y, z]` | Look-at point (Y-up)     |
| `/camera/fov`      | `float`     | Field of view in degrees |
| `/camera/near`     | `float`     | Near clipping plane      |
| `/camera/far`      | `float`     | Far clipping plane       |

The address prefix (`/camera`) is configurable.

## Installation

### 1. Install python-osc in Blender’s Python

```bash
# Find Blender's Python
/path/to/blender/4.5/python/bin/python3 -m pip install python-osc
```

### 2. Install the add-on

1. Edit → Preferences → Add-ons → Install
2. Select `blender-osc-camera.zip`
3. Activate "OSC Camera Sync"

## Usage

1. Select a camera
2. Properties Panel → Camera Data → **OSC Camera Sync**
3. Configure host and port (default: `127.0.0.1:9000`)
4. Adjust the OSC address prefix (default: `/camera`)
5. Click “Start Sync”

## ossia score Configuration

In ossia score:

1. Add device → OSC
2. Set the port to the same as in the add-on (e.g. 9000)
3. The parameters will appear automatically under the configured prefix

## Coordinate Systems

The add-on automatically converts:

* **Blender**: Z-up (X=right, Y=back, Z=up)
* **ossia/OpenGL**: Y-up (X=right, Y=up, Z=toward viewer)

Transformation: `(x, y, z)_blender → (x, z, -y)_ossia`

## Options

* **Send as Bundle**: When enabled, all parameters are sent as an OSC bundle (atomic update). Recommended for synchronized processing.
* **Look Distance**: Distance for calculating the look-at point from the camera direction.

## License

GPL v3

---
