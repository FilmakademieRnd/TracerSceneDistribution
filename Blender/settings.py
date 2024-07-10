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

import bpy

## Class to keep editable parameters
class VpetProperties(bpy.types.PropertyGroup):
    server_ip: bpy.props.StringProperty(name='Server IP', default = '127.0.0.1', description='IP adress of the machine you are running Blender on. \'127.0.0.1\' for tests only on this machine.')
    dist_port: bpy.props.StringProperty(default = '5555')
    sync_port: bpy.props.StringProperty(default = '5556')
    update_sender_port: bpy.props.StringProperty(default = '5557')
    Command_Module_port: bpy.props.StringProperty(default = '5558')
    mixamo_humanoid: bpy.props.BoolProperty(name="Mixamo Unity Humanoid?",description="Check if using mixamo humanoid and you need to send the character to Unity",default=False)
    vpet_collection: bpy.props.StringProperty(name = 'VPET Collection', default = 'VPET_Collection', maxlen=30)
    #edit_collection: bpy.props.StringProperty(name = 'Editable Collection', default = 'VPET_editable', maxlen=30)

## Class to keep data
#
class VpetData():

    sceneObject = {}
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

    SceneObjects = []

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

    nodeTypes = ['GROUP', 'GEO', 'LIGHT', 'CAMERA', 'SKINNEDMESH', 'CHARACTER']
    lightTypes = ['SPOT', 'SUN', 'POINT', 'AREA']

    messageType = ['PARAMETERUPDATE', 'LOCK', \
                'SYNC', 'PING', 'RESENDUPDATE', \
                'UNDOREDOADD', 'RESETOBJECT', \
                'DATAHUB']

    """
    parameterTypes = ['POS', 'ROT', 'SCALE', 'LOCK', 'HIDDENLOCK', 'KINEMATIC', \
                    'FOV', 'ASPECT', 'FOCUSDIST', 'FOCUSSIZE', 'APERTURE', \
                    'COLOR', 'INTENSITY', 'EXPOSURE', 'RANGE', 'ANGLE', \
                    'BONEANIM', \
                    'VERTEXANIM', \
                    'PING', 'RESENDUPDATE', \
                    'CHARACTERTARGET']
    """
    debugCounter = 0