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

import struct
import bpy
from mathutils import Vector, Quaternion, Euler, Color, Matrix
from enum import Enum
import math

class AbstractParameter:

    def __init__ (self, value, name, parent=None, distribute=True):
        self._type = self.to_tracer_type(type(value))
        self._value = value
        self._name = name
        self._parent = parent
        self._distribute = distribute
        self._initial_value = value
        self._dataSize = self.getDataSize()
        self.hasChanged = []

        if(parent):
            self._id = len(parent._parameterList)
            print(str(self._id))

    
    def to_tracer_type(self, t):
        if t == bool:
            return 2  # BOOL
        elif t == int:
            return 3  # INT
        elif t == float:
            return 4  # FLOAT
        elif t in [Vector, Vector]:
            if len(t()) == 2:
                return 5  # Vector2
            elif len(t()) == 3:
                return 6  # Vector3
            elif len(t()) == 4:
                return 7  # Vector4
        elif t == Quaternion:
            return 8  # Quaternion
        elif t == Color:
            return 9  # Color
        elif t == str:
            return 10  # STRING
        else:
            return 100  # UNKNOWN
        
         
    def getDataSize(self):
        if self._type == 2:
            return 1
        if self._type == 3 or self._type == 4:
            return 4
        if self._type == 5:
            return 8
        if self._type == 6:
            return 12
        if self._type == 7 or self._type == 8 or self._type == 9:
            return 16
    
class Parameter(AbstractParameter):
    def __init__(self, value, name, parent=None, distribute=True):
        super().__init__(value, name, parent, distribute)

    def set_value(self, new_value):
        #if new_value != self._value:
        self._value = new_value
        self.emitHasChanged()
    
    def emitHasChanged(self):
        for handler in self.hasChanged:
            handler(self._value)

    def decodeMsg(self, param_data):
        type = self._type
        if type == 2 :
            floatVal = unpack('?', param_data, 0)
            self.set_value(floatVal)

        if type == 4 :
            floatVal = unpack('f', param_data, 0)
            self.set_value(floatVal)

        if type == 6 :
            newVector3 = Vector((   unpack('f', param_data, 0),\
                                    unpack('f', param_data, 4),\
                                    unpack('f', param_data, 8)
                                    ))
             
            unityToBlenderVector3 = Vector((newVector3[0], newVector3[2], newVector3[1]))

            self.set_value(unityToBlenderVector3)

        elif type == 8 :
            XYZW_quat = Quaternion((    unpack('f', param_data, 0 ),\
                                        unpack('f', param_data, 4 ),\
                                        unpack('f', param_data, 8 ),\
                                        unpack('f', param_data, 12)
                                        ))

            WXYZ_quat = Quaternion((    XYZW_quat[3],\
                                        XYZW_quat[0],\
                                        XYZW_quat[1],\
                                        XYZW_quat[2]
                                        ))

            self.set_value(WXYZ_quat)

        elif type == 9:
             newColor = (unpack('f', param_data, 0), unpack('f', param_data, 4), unpack('f', param_data, 8))

             self.set_value(newColor)


    def SerializeParameter(self):
        type = self._type
        val = self._value
        if type == 3:
            return struct.pack('i', val)
        elif type == 4:
            return struct.pack('f', val)
        elif type == 6:
            unity_vec3 = Vector((val[0], val[2], val[1]))
            return struct.pack('3f', *unity_vec3)
        elif type == 8:
            self._parent.editableObject.rotation_mode = 'QUATERNION'
            unity_quat = Quaternion((    val[1],\
                                         val[3],\
                                         val[2],\
                                        -val[0]
                                        ))
            self._parent.editableObject.rotation_mode = 'XYZ'
            #print(str(unity_quat))
            return struct.pack('4f', *unity_quat)

def unpack(type, array, offset):
    return struct.unpack_from(type, array, offset)[0]

   
class AnimationParameter(Parameter):

    def __init__(self, value, name, parent=None, distribute=True):
        super().__init__(value, name, parent, distribute)
        self.keys = []

    def is_animated(self) -> bool:
        return len(self.keys) > 0

class Keys():

    KeyType = Enum('KeyType', ['STEP', 'LINEAR', 'BEZIER'])

    def __init__(self, time, value, type = KeyType.LINEAR, tangent_time = None, tangent_value = None):
        self.time = time                            # frame - INT
        self.value = value                          # value of the keyframe - type of the value depends on the parameter that is being keyed 
        self.type = type                            # type of keyframe - KeyType (STEP, LINEAR, BEZIER)
        if self.type == 'BEZIER':
            self.tangent_time = tangent_time        # first component of tangent (for beziér keyframes) - INT
            self.tangent_value = tangent_value      # other components of the tangent (for beziér keyframes) - type is same as value