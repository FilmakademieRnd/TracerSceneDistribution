"""
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
"""

import functools
from ..AbstractParameter import Parameter
from .SceneObject import SceneObject
from ..serverAdapter import SendParameterUpdate;


class SceneObjectCamera(SceneObject):
    def __init__(self, obj):
        super().__init__(obj)
        fov = Parameter(obj.data.angle, "Fov", self)
        self._parameterList.append(fov)
        aspect = Parameter(obj.data.sensor_width/obj.data.sensor_height, "Aspect", self)
        self._parameterList.append(aspect)
        near = Parameter(obj.data.clip_start, "Near", self)
        self._parameterList.append(near)
        far = Parameter(obj.data.clip_end, "Far", self)
        self._parameterList.append(far)

        fov.hasChanged.append(functools.partial(self.UpdateFov, fov))
        near.hasChanged.append(functools.partial(self.UpdateNear, near))
        far.hasChanged.append(functools.partial(self.UpdateFar, far))




    def UpdateFov(self, parameter, new_value):
         if self._lock == True:
            self.editableObject.data.angle = new_value
         else:
            SendParameterUpdate(parameter)

    def UpdateNear(self, parameter, new_value):
         if self._lock == True:
            self.editableObject.data.clip_start = new_value
         else:
            SendParameterUpdate(parameter)

    def UpdateFar(self, parameter, new_value):
         if self._lock == True:
            self.editableObject.data.clip_end = new_value
         else:
            SendParameterUpdate(parameter)
