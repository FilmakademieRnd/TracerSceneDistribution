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

unity_to_blender_bone_mapping = {
    #//+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-BODY+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
    #//body/body
    "Hips":"mixamorig:Hips",
    "Spine":"mixamorig:Spine",
    "Chest":"mixamorig:Spine1",
    "UpperChest":"mixamorig:Spine2",
     
    # //body/Left Arm
    "LeftShoulder": "mixamorig:LeftShoulder",
    "LeftUpperArm": "mixamorig:LeftArm",
    "LeftLowerArm": "mixamorig:LeftForeArm",
    "LeftHand": "mixamorig:LeftHand",
 
    # //body/Right Arm
    "RightShoulder": "mixamorig:RightShoulder",
    "RightUpperArm": "mixamorig:RightArm",
    "RightLowerArm": "mixamorig:RightForeArm",
    "RightHand": "mixamorig:RightHand",
 
    # //body/Left Leg
    "LeftUpperLeg": "mixamorig:LeftUpLeg",
    "LeftLowerLeg": "mixamorig:LeftLeg",
    "LeftFoot": "mixamorig:LeftFoot",
    "LeftToes": "mixamorig:LeftToeBase",
 
    # //body/Right Leg
    "RightUpperLeg": "mixamorig:RightUpLeg",
    "RightLowerLeg": "mixamorig:RightLeg",
    "RightFoot": "mixamorig:RightFoot",
    "RightToes": "mixamorig:RightToeBase",
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+/BODY+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
 
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-HEAD+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
    # //Head/Head
    "Neck": "mixamorig:Neck",
    "Head": "mixamorig:Head",
    # //{"Left Eye", "mixamorig:something"}
    # //{"Right Eye", "mixamorig:something"}
    # //{"Jaw", "mixamorig:something"}
 
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-/HEAD+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
 
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-LEFT HAND+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
    "LeftThumbProximal": "mixamorig:LeftHandThumb1",
    "LeftThumbIntermediate": "mixamorig:LeftHandThumb2",
    "LeftThumbDistal": "mixamorig:LeftHandThumb3",
    "LeftIndexProximal": "mixamorig:LeftHandIndex1",
    "LeftIndexIntermediate": "mixamorig:LeftHandIndex2",
    "LeftIndexDistal": "mixamorig:LeftHandIndex3",
    "LeftMiddleProximal": "mixamorig:LeftHandMiddle1",
    "LeftMiddleIntermediate": "mixamorig:LeftHandMiddle2",
    "LeftMiddleDistal": "mixamorig:LeftHandMiddle3",
    "LeftRingProximal": "mixamorig:LeftHandRing1",
    "LeftRingIntermediate": "mixamorig:LeftHandRing2",
    "LeftRingDistal": "mixamorig:LeftHandRing3",
    "LeftLittleProximal": "mixamorig:LeftHandPinky1",
    "LeftLittleIntermediate": "mixamorig:LeftHandPinky2",
    "LeftLittleDistal": "mixamorig:LeftHandPinky3",
 
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+/LEFT HAND+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
 
    # //+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-RIGHT HAND+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
    "RightThumbDistal": "mixamorig:RightHandThumb3",
    "RightIndexProximal": "mixamorig:RightHandIndex1",
    "RightIndexIntermediate": "mixamorig:RightHandIndex2",
    "RightIndexDistal": "mixamorig:RightHandIndex3",
    "RightMiddleProximal": "mixamorig:RightHandMiddle1",
    "RightMiddleIntermediate": "mixamorig:RightHandMiddle2",
    "RightMiddleDistal": "mixamorig:RightHandMiddle3",
    "RightRingProximal": "mixamorig:RightHandRing1",
    "RightRingIntermediate": "mixamorig:RightHandRing2",
    "RightRingDistal": "mixamorig:RightHandRing3",
    "RightLittleProximal": "mixamorig:RightHandPinky1",
    "RightLittleIntermediate": "mixamorig:RightHandPinky2",
    "RightLittleDistal": "mixamorig:RightHandPinky3"
}

blender_to_unity_bone_mapping = {

    "mixamorig:Hips": "Hips",
    "mixamorig:LeftUpLeg": "LeftUpperLeg",
    "mixamorig:RightUpLeg": "RightUpperLeg",
    "mixamorig:LeftLeg": "LeftLowerLeg",
    "mixamorig:RightLeg": "RightLowerLeg",
    "mixamorig:LeftFoot": "LeftFoot",
    "mixamorig:RightFoot": "RightFoot",
    "mixamorig:Spine": "Spine",
    "mixamorig:Spine1": "Chest",
    
    "mixamorig:Neck": "Neck",
    "mixamorig:Head": "Head",
    "mixamorig:LeftShoulder": "LeftShoulder",
    "mixamorig:RightShoulder": "RightShoulder",
    "mixamorig:LeftArm": "LeftUpperArm",
    "mixamorig:RightArm": "RightUpperArm",
    "mixamorig:LeftForeArm": "LeftLowerArm",
    "mixamorig:RightForeArm": "RightLowerArm",
    "mixamorig:LeftHand": "LeftHand",
    "mixamorig:RightHand": "RightHand",
    "mixamorig:LeftToeBase": "LeftToes",
    "mixamorig:RightToeBase": "RightToes",
    "mixamorig:LeftEye": "LeftEye",
    "mixamorig:RightEye": "RightEye",
    "mixamorig:Jaw": "Jaw",
    "mixamorig:LeftHandThumb1": "LeftThumbProximal",
    "mixamorig:LeftHandThumb2": "LeftThumbIntermediate",
    "mixamorig:LeftHandThumb3": "LeftThumbDistal",
    "mixamorig:LeftHandIndex1": "LeftIndexProximal",
    "mixamorig:LeftHandIndex2": "LeftIndexIntermediate",
    "mixamorig:LeftHandIndex3": "LeftIndexDistal",
    "mixamorig:LeftHandMiddle1": "LeftMiddleProximal",
    "mixamorig:LeftHandMiddle2": "LeftMiddleIntermediate",
    "mixamorig:LeftHandMiddle3": "LeftMiddleDistal",
    "mixamorig:LeftHandRing1": "LeftRingProximal",
    "mixamorig:LeftHandRing2": "LeftRingIntermediate",
    "mixamorig:LeftHandRing3": "LeftRingDistal",
    "mixamorig:LeftHandPinky1": "LeftLittleProximal",
    "mixamorig:LeftHandPinky2": "LeftLittleIntermediate",
    "mixamorig:LeftHandPinky3": "LeftLittleDistal",
    "mixamorig:RightHandThumb1": "RightThumbProximal",
    "mixamorig:RightHandThumb2": "RightThumbIntermediate",
    "mixamorig:RightHandThumb3": "RightThumbDistal",
    "mixamorig:RightHandIndex1": "RightIndexProximal",
    "mixamorig:RightHandIndex2": "RightIndexIntermediate",
    "mixamorig:RightHandIndex3": "RightIndexDistal",
    "mixamorig:RightHandMiddle1": "RightMiddleProximal",
    "mixamorig:RightHandMiddle2": "RightMiddleIntermediate",
    "mixamorig:RightHandMiddle3": "RightMiddleDistal",
    "mixamorig:RightHandRing1": "RightRingProximal",
    "mixamorig:RightHandRing2": "RightRingIntermediate",
    "mixamorig:RightHandRing3": "RightRingDistal",
    "mixamorig:RightHandPinky1": "RightLittleProximal",
    "mixamorig:RightHandPinky2": "RightLittleIntermediate",
    "mixamorig:RightHandPinky3": "RightLittleDistal",
    "mixamorig:Spine2": "UpperChest",
    "LastBone": "LastBone"
}
