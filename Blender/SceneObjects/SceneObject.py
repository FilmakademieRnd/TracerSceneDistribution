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
import math
from ..AbstractParameter import Parameter;
from ..serverAdapter import SendParameterUpdate;



class SceneObject:

    s_id = 1
    
    def __init__(self, obj):
        self._id = SceneObject.s_id
        SceneObject.s_id += 1
        self._sceneID = 254
        self._parameterList = []
        self._lock = False
        self.editableObject = obj 
        position = Parameter(obj.location, "Position", self)
        self._parameterList.append(position)
        rotation = Parameter(obj.rotation_quaternion, "Rotation", self)
        self._parameterList.append(rotation)
        scale = Parameter(obj.scale, "Scale", self)
        self._parameterList.append(scale)
        # Bind UpdatePosition to the instance using functools.partial
        position.hasChanged.append(functools.partial(self.UpdatePosition, position))
        rotation.hasChanged.append(functools.partial(self.UpdateRotation, rotation))
        scale.hasChanged.append(functools.partial(self.UpdateScale, scale))


    def UpdatePosition(self, parameter, new_value):
        if self._lock == True:
            self.editableObject.location = new_value
        else:
            SendParameterUpdate(parameter)

    def UpdateRotation(self, parameter, new_value):
        if self._lock == True:
            self.editableObject.rotation_mode = 'QUATERNION'
            self.editableObject.rotation_quaternion = new_value
            self.editableObject.rotation_mode = 'XYZ'

            if self.editableObject.type == 'LIGHT' or self.editableObject.type == 'CAMERA' or self.editableObject.type == 'ARMATURE':
                self.editableObject.rotation_euler.rotate_axis("X", math.radians(90))
        else:
            SendParameterUpdate(parameter)

    def UpdateScale(self, parameter, new_value):
        if self._lock == True:
            self.editableObject.scale = new_value
        else:
            SendParameterUpdate(parameter)

    def LockUnlock(self, value):
        if value == 1:
            self._lock = True
            self.editableObject.hide_select = True
        else:
            self._lock = False
            self.editableObject.hide_select = False
        
    
