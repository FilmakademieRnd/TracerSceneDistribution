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

import functools
from ..AbstractParameter import Parameter
from .SceneObject import SceneObject
from ..serverAdapter import send_parameter_update;

class SceneObjectLight(SceneObject):
    def __init__(self, obj):
        super().__init__(obj)
        color = Parameter(obj.data.color, "Color", self)
        self.parameter_list.append(color)
        intensity = Parameter(obj.data.energy, "Intensity", self)
        self.parameter_list.append(intensity)
        color.parameter_handler.append(functools.partial(self.update_color, color))
        intensity.parameter_handler.append(functools.partial(self.update_intensity, intensity))

    def update_color(self, parameter, new_value):
        if self.network_lock == True:
            self.editable_object.data.color = new_value
        else:
            send_parameter_update(parameter)

    def update_intensity(self, parameter, new_value):
        if self.network_lock == True:
            self.editable_object.data.energy = new_value
        else:
            send_parameter_update(parameter)
