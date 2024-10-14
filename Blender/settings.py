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
import logging
from .SceneObjects.SceneObject import SceneObject

## Class to keep editable parameters
class TracerProperties(bpy.types.PropertyGroup):
    server_ip: bpy.props.StringProperty(name='Server IP', default = '127.0.0.1', description='IP adress of the machine you are running Blender on. \'127.0.0.1\' for tests only on this machine.')
    dist_port: bpy.props.StringProperty(default = '5555')
    sync_port: bpy.props.StringProperty(default = '5556')
    update_sender_port: bpy.props.StringProperty(default = '5557')
    Command_Module_port: bpy.props.StringProperty(default = '5558')
    humanoid_rig: bpy.props.BoolProperty(name="Humanoid Rig for Unity",description="Check if using humanoid rig and you need to send the character to Unity",default=False)
    tracer_collection: bpy.props.StringProperty(name = 'TRACER Collection', default = 'TRACER_Collection', maxlen=30)
    overwrite_animation: bpy.props.BoolProperty(name="Overwrite Animation", description="When true, baking an animation received from AnimHost will overwrite the previous one; otherwhise, it writes it on a new layer", default=False)

## Class to keep data
#
class TracerData():

    
    scene_obj_map: dict[int, SceneObject] = {}
    sceneLight = {}
    sceneCamera = {}
    sceneMesh = {}

    geoPackage = {}
    materialPackage = {}
    texturePackage = {}
    characterPackage = {}

    points_for_frames = {}

    objectsToTransfer = []
    nodeList = []
    geoList = []
    materialList = []
    textureList = []
    editableList = []
    characterList = []
    curveList = []
    editable_objects = []

    SceneObjects: list[SceneObject] = []

    rootChildCount = 0
    
    socket_d = None
    socket_s = None
    socket_c = None
    socket_u = None
    poller = None
    ctx = None
    cID = None
    time = 0
    pingStartTime = 0

    nodesByteData = bytearray([])
    geoByteData = bytearray([])
    texturesByteData = bytearray([])
    headerByteData = bytearray([])
    materialsByteData = bytearray([])
    charactersByteData = bytearray([])
    curvesByteData = bytearray([])
    pingByteMSG = bytearray([])
    ParameterUpdateMSG = bytearray([])

    debugCounter = 0

    def clear_tracer_data(self):
    
        self.scene_obj_map.clear()
        self.objectsToTransfer.clear()
        self.nodeList.clear()
        self.geoList.clear()
        self.materialList.clear()
        self.textureList.clear()
        self.editableList.clear()
        self.characterList.clear()
        self.curveList.clear()
        self.editable_objects.clear()
        self.SceneObjects.clear()
        self.nodesByteData.clear()
        self.geoByteData.clear()
        self.texturesByteData.clear()
        self.headerByteData.clear()
        self.materialsByteData.clear()
        self.charactersByteData.clear()
        self.curvesByteData.clear()

    