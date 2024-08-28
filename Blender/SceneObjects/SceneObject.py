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
from bpy.types import Object
import functools
import math
from mathutils import Vector, Quaternion

from ..AbstractParameter import Parameter
from ..serverAdapter import SendParameterUpdate

class SceneObject:

    s_id = 1
    _parameterList : list[Parameter]
    
    def __init__(self, bl_obj: Object):
        self._id = SceneObject.s_id
        SceneObject.s_id += 1
        self._sceneID = 254
        self._parameterList = []
        self.network_lock = False
        self.editableObject = bl_obj 
        tracer_pos = Parameter(bl_obj.location, bl_obj.name+"-location", self)
        self._parameterList.append(tracer_pos)
        tracer_rot = Parameter(bl_obj.rotation_quaternion, bl_obj.name+"-rotation_euler", self)
        self._parameterList.append(tracer_rot)
        tracer_scl = Parameter(bl_obj.scale, bl_obj.name+"-scale", self)
        self._parameterList.append(tracer_scl)
        # Bind UpdatePosition to the instance using functools.partial
        tracer_pos.hasChanged.append(functools.partial(self.UpdatePosition, tracer_pos))
        tracer_rot.hasChanged.append(functools.partial(self.UpdateRotation, tracer_rot))
        tracer_scl.hasChanged.append(functools.partial(self.UpdateScale,    tracer_scl))


    def UpdatePosition(self, tracer_pos: Parameter, new_value: Vector):
        if self.network_lock:
            self.editableObject.location = new_value
            if tracer_pos.key_list.has_changed:
                for key in tracer_pos.get_key_list():
                    self.editableObject.location = key.value
                    self.editableObject.keyframe_insert("location", key.time)
        else:
            SendParameterUpdate(tracer_pos)

    def UpdateRotation(self, tracer_rot: Parameter, new_value: Quaternion):
        if self.network_lock:
            self.editableObject.rotation_mode = 'QUATERNION'
            self.editableObject.rotation_quaternion = new_value
            self.editableObject.rotation_mode = 'XYZ'

            if self.editableObject.type == 'LIGHT' or self.editableObject.type == 'CAMERA' or self.editableObject.type == 'ARMATURE':
                self.editableObject.rotation_euler.rotate_axis("X", math.radians(90))
        else:
            SendParameterUpdate(tracer_rot)

    def UpdateScale(self, tracer_scl: Parameter, new_value: Vector):
        if self.network_lock:
            self.editableObject.scale = new_value
        else:
            SendParameterUpdate(tracer_scl)

    def LockUnlock(self, value: int):
        if value == 1:
            self.network_lock = True
            self.editableObject.hide_select = True
        else:
            self.network_lock = False
            self.editableObject.hide_select = False
        
    
