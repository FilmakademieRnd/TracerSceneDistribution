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
from mathutils import Vector, Quaternion, Color
from enum import Enum
import math

class TRACERParamType(Enum):
    NONE        = 0
    ACTION      = 1
    BOOL        = 2
    INT         = 3
    FLOAT       = 4
    VECTOR2     = 5
    VECTOR3     = 6
    VECTOR4     = 7
    QUATERNION  = 8
    COLOR       = 9
    STRING      = 10 
    LIST        = 11
    UNKNOWN     = 100

class KeyType(Enum):
    STEP    = 1
    LINEAR  = 2
    BEZIER  = 3

## Abstract Class AbstractParameter (necessary to declare copy method in the AbstractParameter class)
class AbstractParameter:
    pass

class Key:
    ## Class attributes ##
    # frame timestamp of the current key
    time:   float

    tangent_time : float
    # value of the keyframe - type of the value depends on the parameter that is being keyed
    value: any | bool | int | float | Vector | Quaternion | Color | str | list #? type Action?

    tangent_value: any | bool | int | float | Vector | Quaternion | Color | str | list #? type Action?
    # type of keyframe - KeyType (STEP, LINEAR, BEZIER)
    key_type:   KeyType

    def __init__(self, time, value, type = KeyType.LINEAR, tangent_time = None, tangent_value = None):
        self.time = time
        self.value = value
        self.key_type = type
        if self.key_type == KeyType.BEZIER:
            # first component of tangent (for beziér keyframes) - INT/FLOAT
            self.tangent_time = tangent_time if tangent_time != None else time
            # other components of the tangent (for beziér keyframes) - type is same as value
            self.tangent_value = tangent_value if tangent_value != None else value

    def get_data_size(self):
        if isinstance(self.value, bool):
            return struct.calcsize('?') # = 1
        elif isinstance(self.value, int) or isinstance(self.value, float):
            return struct.calcsize('i') # = 4
        elif isinstance(self.value, Vector) and len(self.value) == 2:
            return struct.calcsize('f') * 2 # = 8
        elif isinstance(self.value, Vector) and len(self.value) == 3:
            return struct.calcsize('f') * 3 # = 12
        elif isinstance(self.value, Vector) and len(self.value) == 4 or isinstance(self.value, Quaternion) or isinstance(self.value, Color):
            return struct.calcsize('f') * 4 # = 16
        elif isinstance(self.value, str):
            return struct.calcsize('c') * len(self._value) # len_of_string * size_of_char

    def get_key_size(self):
        # byte (key_type) +           float (time) +           float (tangent_time) + size_of_param (value) + size_of_param (tangentvalue)
        return          1 + self.time.__sizeof__() + self.tangent_time.__sizeof__() +  self.get_data_size() +         self.get_data_size()
    
    def is_equal(self, other):
        return (self.key_type       == other.key_type       and\
                self.time           == other.time           and\
                self.value          == other.value          and\
                self.tangent_time   == other.tangent_time   and\
                self.tangent_value  == other.tangent_value     )
    
class KeyList:
    __data: list[Key]

    def __init__(self) -> None:
        self.__data = []

    def clear(self) -> None:
        self.__data.clear()

    def size(self) -> int:
        return len(self.__data)
    
    def set_key(self, parameter, key: Key, index: int):
        if index > self.size():
            raise IndexError("Setting Key Out Of Bounds for KeyList")
        elif index == self.size() or index == -1:
            self.__data.append(key)
            parameter.emitHasChanged()
        else:
            if not key.is_equal(self.__data[index]):
                self.__data[index] = key
                parameter.emitHasChanged()

    def remove_key(self, key: Key) -> Key:
        flagged_index = -1
        for k, i in enumerate(self.__data):
            # Look for the key to be removed based on its timestamp
            # Stop updating the index at the first found instance 
            if k.time == key.time and flagged_index < 0:
                flagged_index = i

        if flagged_index > 0:
            return self.remove_key_at_index(flagged_index)
        else:
            raise LookupError("Key not found in Parameter Key List")
                

    def remove_key_at_index(self, index: int) -> Key:
        removed_key = self.__data[index]
        self.__data.remove(index)
        return removed_key

    def get_key(self, index: int) -> Key:
        return self.__data[index]
    
    def get_list(self) -> list[Key]:
        return self.__data

class AbstractParameter:

    ## Class attributes ##
    # Type of the Parameter according to Tracer' definition
    __type: TRACERParamType = None
    # Parameter value - type of the value depends on the parameter that is being keyed
    value: any | bool | int | float | Vector | Quaternion | Color | str | list #? type Action?
    # Parameter name
    name: str
    # Parametrized blender Object
    parent: bpy.types.Object
    # Flag that determines whether a Parameter is going to be distributed
    distribute: bool
    # Flag that determines whether a Parameter is locked from the network connection
    network_lock: bool = False
    # Flag that determines whether a Parameter is a RPC parameter
    is_RPC: bool = False
    # Flag that determines whether a Parameter is animated
    is_animated: bool = False

    def __init__ (self, value, name, parent = None, distribute = True, network_lock = False, is_RPC = False, is_animated = False):
        self.value = value
        self.__type = self.get_tracer_type()
        self.name = name
        self.parent = parent
        self.distribute = distribute
        self.network_lock = network_lock
        self.is_RPC = is_RPC
        self.is_animated = is_animated
        self.initial_value = value
        self.dataSize = self.getDataSize()
        self.hasChanged = []

        if(parent):
            self._id = len(parent._parameterList)
            print(str(self._id))

    def get_tracer_type(self):
        if isinstance(self.value, bool):
            return TRACERParamType.BOOL
        elif isinstance(self.value, int):
            return TRACERParamType.INT
        elif isinstance(self.value, float):
            return TRACERParamType.FLOAT
        elif isinstance(self.value, Vector) and len(self.value) == 2:
            return TRACERParamType.VECTOR2
        elif isinstance(self.value, Vector) and len(self.value) == 3:    
            return TRACERParamType.VECTOR3
        elif isinstance(self.value, Vector) and len(self.value) == 4:
            return TRACERParamType.VECTOR4
        elif isinstance(self.value, Quaternion):
            return TRACERParamType.QUATERNION
        elif isinstance(self.value, Color):
            return TRACERParamType.COLOR
        elif isinstance(self.value, str):
            return TRACERParamType.STRING
        else:
            return TRACERParamType.UNKNOWN
    
    def get_data_size(self) -> int:
        if self.__type == TRACERParamType.BOOL:
            return struct.calcsize('?') # = 1
        elif self.__type == TRACERParamType.INT or self.__type == TRACERParamType.FLOAT:
            return struct.calcsize('i') # = 4
        elif self.__type == TRACERParamType.VECTOR2:
            return struct.calcsize('f') * 2 # = 8
        elif self.__type == TRACERParamType.VECTOR3:
            return struct.calcsize('f') * 3 # = 12
        elif self.__type == TRACERParamType.VECTOR4 or self.__type == TRACERParamType.QUATERNION or self.__type == TRACERParamType.COLOR:
            return struct.calcsize('f') * 4 # = 16
        elif self.__type == TRACERParamType.STRING:
            return struct.calcsize('c') * len(self._value) # len_of_string * size_of_char
        
    def python_type(self):
        return type(self._value)

    
class Parameter(AbstractParameter):

    ## Class Attributes ##
    key_list: KeyList

    def __init__(self, value, name, parent=None, distribute=True, network_lock = False, is_RPC = False, is_animated = False):
        super().__init__(value, name, parent, distribute, network_lock, is_RPC, is_animated)
        self.key_list = KeyList()

    # resets value to initial value, why do we want to do that?
    def reset(self):
        pass

    def init_animation(self):
        #???
        self.is_animated = True
        key_zero = Key()
        self.key_list.set_key(self, key_zero, 0)

    def clear_animation(self):
        self.is_animated = False
        self.key_list.clear()

    def get_size(self) -> int:
        data_size = self.get_data_size()
        if self.is_animated:
            # When animated, the size of the parameter increases. After the first payload, there will be the number of keys that the animated parameter will have and then the list of those keys. 
            #         size_of_param +  size_of_short (nr_keys) +             nr_keys *                      size_of_key (= 2* size_of_param (value + tangent_value) + 2 * size_of_float (time + tangent_time) + byte (key_type))
            return        data_size +                        2 + len(self.key_list) * self.key_list[0].get_key_size()
        else:
            return data_size

    def set_value(self, new_value):
        self.network_lock = True
        if new_value != self.value:
            self.value = new_value
            self.emitHasChanged()
        self.network_lock = False
    
    def emitHasChanged(self):
        for handler in self.hasChanged:
            handler(self.value)

    def copy_value(self, other): # other: Parameter (returns Parameter)
        self.network_lock = True
        has_changed = False
        if self.value != other.value:
            self.value = other.value
            has_changed = True
        if self.is_animated != other.is_animated:
            self.is_animated = other.is_animated
            if self.is_animated:
                self.init_animation()
                self.key_list = other.key_list
            else:
                self.clear_animation()
            has_changed = True
        self.network_lock = False


    #####################
    ### Serialization ###
    #####################

    def serialize(self) -> bytearray:
        payload = bytearray()
        payload.extend(self.serialize_data())
        if self.is_animated:
            for key in self.key_list:
                payload = bytearray(key.get_key_size())
                payload.extend(struct.pack('<B', key.key_type))         # '<B' represents the format of an unsigned char (1 byte) encoded as little endian
                payload.extend(struct.pack('<f', key.time))             # '<f' represents the format of a signed float (4 bytes) encoded as little endian
                payload.extend(struct.pack('<f', key.tangent_time))
                payload.extend(self.serialize_data(key.value))
                payload.extend(self.serialize_data(key.tangent_value))
        return payload

    def serialize_data(self, value = None) -> bytearray:
        
        # If the attribute value is not initialised, the internal self.value instance attribute is going to be serialised
        # Vectors are swizzled (Y-Z swap) in order to comply with the different handidness between blender and unity
        # Quanternion rotation is taken from the object's rotation and swizzled (from XYZW to WXYZ) 
        if value == None:
            if self.__type == TRACERParamType.VECTOR3:
                value = self.value.xzy
            elif self.__type == TRACERParamType.VECTOR4:
                value = self.value.xzyw
            elif self.__type == TRACERParamType.QUATERNION:
                self.parent.editableObject.rotation_mode = 'QUATERNION'
                value = self.value.wxyz
                self.parent.editableObject.rotation_mode = 'XYZ'
            else:
                value = self.value

        if self.__type == TRACERParamType.BOOL:
            return struct.pack('?', value)
        elif self.__type == TRACERParamType.INT:
            return struct.pack('<i', value)
        elif self.__type == TRACERParamType.FLOAT:
            return struct.pack('<f', value)
        elif self.__type == TRACERParamType.VECTOR2:
            return struct.pack('<2f', value)
        elif self.__type == TRACERParamType.VECTOR3:
            unity_vec3 = value.xzy
            return struct.pack('<3f', unity_vec3)
        elif self.__type == TRACERParamType.VECTOR4:
            unity_vec4 = value.xzyw
            return struct.pack('<4f', unity_vec4)
        elif self.__type == TRACERParamType.QUATERNION:
            return struct.pack('<4f', value)
        elif self.__type == TRACERParamType.COLOR:
            return struct.pack('<4f', value)
        elif self.__type == TRACERParamType.STRING:
            string_length = str(len(value))
            format_string = string_length + "s"
            return struct.pack(format_string, value)
        
    #####################
    ## Deserialization ##
    #####################

    def deserialize(self, msg: bytearray) -> None:
        data_size = self.get_data_size()
        msg_payload = msg[0:data_size]
        self.set_value(self.deserialize_data(msg_payload))

        if self.is_animated:
            byte_count = data_size
            key_count = 0
            while byte_count < len(msg):
                key_type        = struct.unpack('<B', msg[byte_count:byte_count+1])[0],           byte_count = byte_count + 1           # Read Key Type
                time            = struct.unpack('<f', msg[byte_count:byte_count+4])[0],           byte_count = byte_count + 4           # Read time
                #! Tangent time and Tangent value are due a refactoring
                tangent_time    = struct.unpack('<f', msg[byte_count:byte_count+4])[0],           byte_count = byte_count + 4           # Read tangent time
                value           = self.deserialize_data(msg[byte_count:byte_count+data_size]),    byte_count = byte_count + data_size   # Read value
                tangent_value   = self.deserialize_data(msg[byte_count:byte_count+data_size]),    byte_count = byte_count + data_size   # Read tangent value
                deserialized_key = Key(time, value, key_type, tangent_time, tangent_value)
                self.key_list.set_key(self, deserialized_key, key_count)
                key_count = key_count + 1


    def deserialize_data(self, msg_payload: bytearray):
        if self.__type == TRACERParamType.BOOL:
            bool_val = struct.unpack('?', msg_payload)[0]
            return bool_val

        elif self.__type == TRACERParamType.INT:
            #? Signed or unsigned Integer?
            int_val = struct.unpack('<i', msg_payload)[0]
            return int_val

        elif self.__type == TRACERParamType.FLOAT:
            float_val = struct.unpack('<f', msg_payload)[0]
            return float_val

        elif self.__type == TRACERParamType.VECTOR2:
            vec2_val = Vector((struct.unpack('<2f', msg_payload)))
            return vec2_val

        elif self.__type == TRACERParamType.VECTOR3:
            vec3_val = Vector((struct.unpack('<3f', msg_payload)))
            # Swap Y and Z axis to adapt to blender's handidness
            return vec3_val.xzy

        elif self.__type == TRACERParamType.VECTOR4:
            vec3_val = Vector((struct.unpack('<4f', msg_payload)))
            # Swap Y and Z axis to adapt to blender's handidness
            return vec3_val.xzyw

        elif self.__type == TRACERParamType.QUATERNION:
            # The quaternion is passed in the order XYZW
            quat_val = Quaternion((struct.unpack('<4f', msg_payload)))
            return Quaternion((quat_val.w, quat_val.x, quat_val.y, quat_val.z))

        elif self.__type == TRACERParamType.COLOR:
            color_val = Color((struct.unpack('<4f', msg_payload)))
            return color_val

        elif self.__type == TRACERParamType.STRING:
            # https://docs.python.org/3/library/stdtypes.html#bytearray.decode
            string_val = msg_payload.decode(encoding='ascii', errors='strict')
            return string_val

        else:
            print("Unknown type")
