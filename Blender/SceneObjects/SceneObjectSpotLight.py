'''
TRACER Scene Distribution Plugin Blender
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Blender is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Blender development.
 
The TRACER Scene Distribution Plugin Blender is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Blender is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Blender may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Blender Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Blender by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Blender in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
import bpy
import functools
import math
import struct
from ..AbstractParameter import Parameter
from .SceneObjectLight import SceneObjectLight, LightTypes
from ..serverAdapter import send_parameter_update

class SceneObjectSpotLight(SceneObjectLight):
    def __init__(self, obj):
        super().__init__(obj)

        angle_param = Parameter(math.degrees(obj.data.spot_size), "Spot", self)
        angle_param.parameter_handler.append(functools.partial(self.update_spot_angle, angle_param))

    def update_spot_angle(self, parameter, new_value):
        if self.network_lock == True:
            self.blender_object.data.spot_size = new_value
        else:
            send_parameter_update(parameter)

    def serialise(self):
        light_byte_array = super().serialise()

        spot_light_data: bpy.types.SpotLight = self.blender_object.data

        # Light Type
        light_byte_array.extend(struct.pack('i', LightTypes.SPOT.value))
        # Light Intensity
        light_byte_array.extend(struct.pack('f', spot_light_data.energy/100.0))
        # Light Angle
        light_byte_array.extend(struct.pack('f', math.degrees(spot_light_data.spot_size)))
        # Light Range (always 10 because blender does not define it)
        light_byte_array.extend(struct.pack('f', 10))
        # Light Colour
        light_byte_array.extend(struct.pack('3f', spot_light_data.color))

        return light_byte_array