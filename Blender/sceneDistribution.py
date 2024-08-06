"""
-----------------------------------------------------------------------------
This source file is part of VPET - Virtual Production Editing Tools
http://vpet.research.animationsinstitut.de/
http://github.com/FilmakademieRnd/VPET

Copyright (c) 2021 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Lab

This project has been initiated in the scope of the EU funded project
Dreamspace under grant agreement no 610005 in the years 2014, 2015 and 2016.
http://dreamspaceproject.eu/
Post Dreamspace the project has been further developed on behalf of the
research and development activities of Animationsinstitut.

The VPET component Blender Scene Distribution is intended for research and development
purposes only. Commercial use of any kind is not permitted.

There is no support by Filmakademie. Since the Blender Scene Distribution is available
for free, Filmakademie shall only be liable for intent and gross negligence;
warranty is limited to malice. Scene DistributiorUSD may under no circumstances
be used for racist, sexual or any illegal purposes. In all non-commercial
productions, scientific publications, prototypical non-commercial software tools,
etc. using the Blender Scene Distribution Filmakademie has to be named as follows:
“VPET-Virtual Production Editing Tool by Filmakademie Baden-Württemberg,
Animationsinstitut (http://research.animationsinstitut.de)“.

In case a company or individual would like to use the Blender Scene Distribution in
a commercial surrounding or for commercial purposes, software based on these
components or any part thereof, the company/individual will have to contact
Filmakademie (research<at>filmakademie.de).
-----------------------------------------------------------------------------
"""

import bpy
import math
import mathutils
import bmesh
import struct
import re

from mathutils import Vector, Quaternion
from .AbstractParameter import Parameter
from .SceneObjects.SceneObject import SceneObject
from .SceneObjects.SceneObjectCamera import SceneObjectCamera
from .SceneObjects.SceneObjectLight import SceneObjectLight
from .SceneObjects.SceneObjectSpotLight import SceneObjectSpotLight
from .SceneObjects.SceneCharacterObject import SceneCharacterObject
from .Avatar_HumanDescriptioon_Mixamo import blender_to_unity_bone_mapping


## Creating empty classes to store node data
#  is there a more elegant way?
class sceneObject:
    pass

class sceneLight:
    pass
        
class sceneCamera:
    pass
        
class sceneMesh:
    pass

class sceneSkinnedmesh:
    pass
        
class geoPackage:
    pass

class materialPackage:
    pass

class texturePackage:
    pass

class characterPackage:
    pass

class curvePackage:
    pass

def initialize():
    global vpet, v_prop
    vpet = bpy.context.window_manager.vpet_data
    v_prop = bpy.context.scene.vpet_properties
    
    vpet.objectsToTransfer.clear()
    vpet.nodeList.clear()
    vpet.geoList.clear()
    vpet.materialList.clear()
    vpet.textureList.clear()
    vpet.editableList.clear()
    vpet.characterList.clear()
    vpet.curveList.clear()
    vpet.editable_objects.clear()
    vpet.SceneObjects.clear()
    
    vpet.nodesByteData.clear()
    vpet.geoByteData.clear()
    vpet.texturesByteData.clear()
    vpet.headerByteData.clear()
    vpet.materialsByteData.clear()
    vpet.charactersByteData.clear()
    vpet.curvesByteData.clear()

## General function to gather scene data
#
def gatherSceneData():
    initialize()
     #cID
    vpet.cID = int(str(v_prop.server_ip).split('.')[3])
    print( vpet.cID)
    objectList = getObjectList()

    if len(objectList) > 0:
        vpet.objectsToTransfer = objectList
        

        #iterate over all objects in the scene
        for i, n in enumerate(vpet.objectsToTransfer):
            processSceneObject(n, i)

        for i, n in enumerate(vpet.objectsToTransfer):
            processEditableObjects(n, i)

        getHeaderByteArray()
        getNodesByteArray()
        getGeoBytesArray()
        getMaterialsByteArray()
        getTexturesByteArray()
        getCharacterByteArray()
        getCurvesByteArray()

        #for i, v in enumerate(vpet.nodeList):
        #    if v.editable == 1:
        #        vpet.editableList.append((bytearray(v.name).decode('ascii'), v.vpetType))
        
        return len(vpet.objectsToTransfer)
    
    else:
        return 0
    

def getObjectList():
    parent_object_name = "VPETsceneRoot"
    parent_object = bpy.data.objects.get(parent_object_name)
    #objectList = []
    #recursive_game_object_id_extract(parent_object, objectList)
    
    return parent_object.children_recursive    

# def recursive_game_object_id_extract(location, objectList):
#     # Iterate through each child of the location
#     for child in location.children:
#         # Add the child object to the game_objects list
#         print(child.name)
#         objectList.append(child)
#         # Recursively call the function for the child to explore its children
#         recursive_game_object_id_extract(child, objectList)    
    
## Process and store a scene object
#
# @param obj The scene object to process
# @param index The objects index in the list of all objects
def processSceneObject(obj, index):
    global vpet, v_prop
    node = sceneObject()
    node.vpetType = vpet.nodeTypes.index('GROUP')
    
    # gather light data
    if obj.type == 'LIGHT':
        nodeLight = sceneLight()
        nodeLight.vpetType =vpet.nodeTypes.index('LIGHT')
        nodeLight.lightType = vpet.lightTypes.index(obj.data.type)
        nodeLight.intensity = obj.data.energy/100
        nodeLight.color = (obj.data.color.r, obj.data.color.g, obj.data.color.b)
        nodeLight.type = obj.data.type
        # placeholder value bc Blender does not use exposure
        nodeLight.exposure = 0
        # placeholder value bc Blender has no range
        nodeLight.range = 10
        if obj.data.type == 'SPOT':
            nodeLight.angle = math.degrees(obj.data.spot_size)
        else:
            nodeLight.angle = 45

        node = nodeLight
    
    # gather camera data    
    elif obj.type == 'CAMERA':
        nodeCamera = sceneCamera()
        nodeCamera.vpetType = vpet.nodeTypes.index('CAMERA')
        nodeCamera.fov = math.degrees(obj.data.angle)
        nodeCamera.aspect = obj.data.sensor_width/obj.data.sensor_height
        nodeCamera.near = obj.data.clip_start
        nodeCamera.far = obj.data.clip_end  
        nodeCamera.focalDist = 5
        nodeCamera.aperture = 2    
        node = nodeCamera
    
    # gather mesh data
    elif obj.type == 'MESH':
        if obj.parent != None and obj.parent.type == 'ARMATURE':
            nodeSkinMesh = sceneSkinnedmesh()
            node = processSkinnedMesh(obj, nodeSkinMesh)
        else:
            nodeMesh = sceneMesh()
            node = processMesh(obj, nodeMesh)
                
    elif obj.type == 'ARMATURE':
        node.vpetType = vpet.nodeTypes.index('CHARACTER')
        processCharacter(obj, vpet.objectsToTransfer)
    
    #TODO define scene distribution when encountering a (any) curve
    # elif obj.type == 'CURVE':
    #     processCurve_alt(obj, vpet.objectsToTransfer)

    # When finding an Animation Path to be distributed
    if obj.name == "AnimPath":
        processControlPath_temp(obj.get("Control Points", None), obj.get("Is Cyclic", False))
            
        
    # gather general node data    
    nodeMatrix = obj.matrix_local.copy()

    node.position = (nodeMatrix.to_translation().x, nodeMatrix.to_translation().z, nodeMatrix.to_translation().y)
    node.scale = (nodeMatrix.to_scale().x, nodeMatrix.to_scale().z, nodeMatrix.to_scale().y)
    
    # camera and light rotation offset
    if obj.type == 'CAMERA' or obj.type == 'LIGHT':
        rotFix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')
        nodeMatrix = nodeMatrix @ rotFix
    
    rot = nodeMatrix.to_quaternion()
    rot.invert()
    node.rotation = (rot[1], rot[3], rot[2], rot[0])
    
    node.name = bytearray(64)
    
    for i, n in enumerate(obj.name.encode()):
        node.name[i] = n
    node.childCount = len(obj.children)
    
    
    if obj.name == 'VPETsceneRoot':
        node.childCount = vpet.rootChildCount
        
    node.vpetId = index

    edit_property = "VPET-Editable"
    # check if node is editable
    if edit_property in obj and obj.get(edit_property):
        node.editable = 1
        vpet.editable_objects.append(obj)
    else:
        node.editable = 0

    if obj.name != 'VPETsceneRoot':
        vpet.nodeList.append(node)
    
def processMesh(obj, nodeMesh): 
    nodeMesh.vpetType = vpet.nodeTypes.index('GEO')
    nodeMesh.color = (obj.color[0], obj.color[1], obj.color[2], obj.color[3])
    nodeMesh.roughness = 0.5
    nodeMesh.materialId = -1
               
    # get geo data of mesh
    nodeMesh.geoId = processGeoNew(obj)
                
    # get material of mesh
    nodeMaterial = materialPackage()
    mat = obj.active_material
                
    if mat != None:
        nodeMesh.materialId = processMaterial(obj)
        nodeMaterial = vpet.materialList[nodeMesh.materialId]
                    
        # add material parameters to node
        nodeMesh.color = nodeMaterial.color
        nodeMesh.roughness = nodeMaterial.roughness
        nodeMesh.specular = nodeMaterial.specular
                    
    return(nodeMesh)

def processSkinnedMesh(obj, nodeSkinMesh):
    nodeSkinMesh.vpetType = vpet.nodeTypes.index('SKINNEDMESH')
    nodeSkinMesh.color = (0,0,0,1)
    nodeSkinMesh.roughness = 0.5
    nodeSkinMesh.materialId = -1
    nodeSkinMesh.characterRootID = vpet.objectsToTransfer.index(obj.parent)
    
    nodeSkinMesh.geoID = processGeoNew(obj)
    # get material of mesh
    nodeMaterial = materialPackage()
    mat = obj.active_material
    if mat != None:
        nodeSkinMesh.materialId = processMaterial(obj)
        nodeMaterial = vpet.materialList[nodeSkinMesh.materialId]
        
        # add material parameters to node
        nodeSkinMesh.color = nodeMaterial.color
        nodeSkinMesh.roughness = nodeMaterial.roughness
        nodeSkinMesh.specular = nodeMaterial.specular

        bbox_corners = [obj.parent.matrix_world @ mathutils.Vector(corner) for corner in obj.parent.bound_box]
        bbox_center = sum(bbox_corners, mathutils.Vector((0,0,0))) / 8
        bbox_extents = max(bbox_corners, key=lambda c: (c - bbox_center).length) - bbox_center
        nodeSkinMesh.boundCenter = [bbox_center.x, bbox_center.z, bbox_center.y]
        nodeSkinMesh.boundExtents = [bbox_extents.x, bbox_extents.z, bbox_extents.y]

        armature_obj = obj.parent
        if armature_obj:
            armature_data = armature_obj.data
            bind_poses = []
            for bone in armature_data.bones:
                bind_matrix = armature_obj.matrix_world @ bone.matrix_local
                for row in bind_matrix:
                    bind_poses.extend(row)
            
            desired_length = 1584
            current_length = len(bind_poses)
            if current_length < desired_length:
                # If bind_poses is shorter, extend with zeroes
                bind_poses.extend([0] * (desired_length - current_length))  
            nodeSkinMesh.bindPoses = bind_poses
            nodeSkinMesh.bindPoseLength = int(len(bind_poses) / 16)
            nodeSkinMesh.skinnedMeshBoneIDs = [-1] * 99  # Initialize all to -1
            for i, bone in enumerate(armature_data.bones):
                bone_index = -1
                for idx, obj in enumerate(vpet.objectsToTransfer):
                    if obj.name == bone.name:
                        bone_index = idx
                        break
            #for i, bone in enumerate(armature_data.bones):  
                nodeSkinMesh.skinnedMeshBoneIDs[i] = bone_index
                

        nodeSkinMesh.skinnedMeshBoneIDsSize = len(nodeSkinMesh.skinnedMeshBoneIDs)        

        return(nodeSkinMesh)



def processCharacter(armature_obj, object_list):
    chr_pack = characterPackage()
    chr_pack.bonePosition = []
    chr_pack.boneRotation = []
    chr_pack.boneScale = []
    chr_pack.boneMapping = []
    chr_pack.skeletonMapping = []
        

    if armature_obj.type == 'ARMATURE':
        bones = armature_obj.data.bones
        chr_pack.characterRootID = vpet.objectsToTransfer.index(armature_obj)

        if(v_prop.mixamo_humanoid):
            for key, value in blender_to_unity_bone_mapping.items():
                bone_index = -1
                for idx, obj in enumerate(object_list):
                    if key == obj.name:
                        bone_index = idx
                        break
                chr_pack.boneMapping.append(bone_index)

        else:
            for i, bone in enumerate(bones):
                bone_index = -1
                for idx, obj in enumerate(vpet.objectsToTransfer):
                    if obj.name == bone.name:
                        bone_index = idx
                        break

                chr_pack.boneMapping.append(bone_index)
        
        chr_pack.bMSize = len(chr_pack.boneMapping)
        
        for idx, obj in enumerate(object_list):
                if obj.name == armature_obj.name:
                    bone_index = idx
        chr_pack.skeletonMapping.append(bone_index)

        nodeMatrix = armature_obj.matrix_local.copy()

        chr_pack.bonePosition.extend([nodeMatrix.to_translation().x, nodeMatrix.to_translation().z, nodeMatrix.to_translation().y])
        chr_pack.boneScale.extend([nodeMatrix.to_scale().x, nodeMatrix.to_scale().z, nodeMatrix.to_scale().y])
        rot = nodeMatrix.to_quaternion()
        rot.invert()
        chr_pack.boneRotation.extend([rot[1], rot[3], rot[2], rot[0]])

        for mesh in armature_obj.children:
            if mesh.type == 'MESH':
                for idx, obj in enumerate(object_list):
                    if obj.name == mesh.name:
                        bone_index = idx
                chr_pack.skeletonMapping.append(bone_index)

                nodeMatrix = mesh.matrix_local.copy()

                chr_pack.bonePosition.extend([nodeMatrix.to_translation().x, nodeMatrix.to_translation().z, nodeMatrix.to_translation().y])
                chr_pack.boneScale.extend([nodeMatrix.to_scale().x, nodeMatrix.to_scale().z, nodeMatrix.to_scale().y])
                rot = nodeMatrix.to_quaternion()
                rot.invert()
                chr_pack.boneRotation.extend([rot[1], rot[3], rot[2], rot[0]])


        for bone in armature_obj.pose.bones:
            bone_index = -1
            for idx, obj in enumerate(object_list):
                if obj.name == bone.name:
                    bone_index = idx
                    break

            chr_pack.skeletonMapping.append(bone_index)

            
            bone_matrix = armature_obj.matrix_world @ bone.matrix 
            position = bone_matrix.to_translation()
            rotation = bone_matrix.to_quaternion()
            rotation.invert()
            
            
            scale =bone.scale
            chr_pack.bonePosition.extend([position.x, position.z, position.y])
            chr_pack.boneRotation.extend([rotation[1], rotation[3], rotation[2], rotation[0]])
            chr_pack.boneScale.extend(scale)

        chr_pack.sMSize = len(chr_pack.skeletonMapping)
    vpet.characterList.append(chr_pack)
    return chr_pack

##TODO Process and store a Control Path for sending it to TRACER
# def processControlPath(control_point_list):
#     control_path_package = [] #??? This should be an Animation Parameter
    
#     #Initialise AnimationParameter for the Character Object 
#     for cp in control_point_list:
#         # Unpack positions (Vector3 - bezier with two handles) with tangents and frame
#         #??? What about timing Ease-In/Ease-Out values (Vector2???) ?
#         # Unpack timings Ease-In/Ease-Out (Vector2 - stepped) with frame
#         # Unpack rotations (Vector3 - linear) with frame
#         # Unpack styles (Int/String - stepped) with frame
#
#    return control_path_package #??? This should be an Animation Parameter

## Given a Control Path in the scene, it evaluates it, it fills a new Curve Package object with the sampled data, and adds it to the list of curves to be shared with the other TRACER clients
# @param control_point_list List of Control Points defining the Control Path
# @param is_cyclic          Whether the Control Path is cyclic or not (acyclic by default)
# @returns  None            It doesn't return anything, but appends the evaluated curve (@see curvePackage()) to vpet_data.curveList (@see VpetData())
def processControlPath_temp(control_point_list: list[bpy.types.Object], is_cyclic=False):
    vpet = bpy.context.window_manager.vpet_data
    curve_package = curvePackage()
    curve_package.points  = [] # list of floats [pos0.x, pos0.y, pos0.z, pos1.x, pos1.y, pos1.z, ..., posN.x, posN.y, posN.z]
    curve_package.look_at = [] # list of floats [rot0.x, rot0.y, rot0.z, rot1.x, rot1.y, rot1.z, ..., rotN.x, rotN.y, rotN.z]
    value_error_msg = "The frame value of any point MUST be greater than the previous one!"

    for i, point in enumerate(control_point_list):
        # Read the attribute of the first point of the segment
        coords_point_one    = point.location
        r_handle_point_one  = Vector(point.get("Right Handle").to_list())
        frame_point_one     = point.get("Frame")
        ease_out_point_one  = point.get("Ease Out")

        if is_cyclic:
            if i == 0:
                # If cyclic, we assume that the frame of the first point is 0 at the beginning of the path and point.get("Frame") at the end 
                frame_point_one = 0

            if i == len(control_point_list)-1:
                # If the path is cyclic and we are at the end of the path,
                # Evaluate segment between last and fist point of the path
                next_point = control_point_list[0]
                value_error_msg = "When cyclic, the frame value of the first point MUST be greater than the last one!"
        else:
            if i < len(control_point_list)-1:
                next_point = control_point_list[i+1]
            else:
                next_point = None
        
        if next_point != None:
            # Read the attribute of the second point of the segment
            coords_point_two    = next_point.location
            l_handle_point_two  = Vector(next_point.get("Left Handle").to_list())        
            frame_point_two     = next_point.get("Frame")        
            ease_in_point_two   = point.get("Ease In")

            segment_frames = frame_point_two - frame_point_one      # Compute number of samples in the segment 

            if segment_frames > 0:
                curve_package.points.extend(adaptive_sample_bezier(coords_point_one, r_handle_point_one, l_handle_point_two, coords_point_two,\
                                                                   segment_frames, ease_out_point_one, ease_in_point_two))
                curve_package.look_at.extend(quaternion_slerp(point.rotation_quaternion, next_point.rotation_quaternion, segment_frames))
            else:
                raise ValueError(value_error_msg)
    
    curve_package.pointsLen = int(len(curve_package.points) / 3)
    vpet.curveList.append(curve_package)

# def processCurve(obj, objList):
#     vpet = bpy.context.window_manager.vpet_data
#     curve_Pack = curvePackage()
#     curve_Pack.points = []

#     for frame in range(0, bpy.context.scene.frame_end + 1):
#         points = evaluate_curve(obj, frame)
#         vpet.points_for_frames[frame] = points

#     for frame, points_list in vpet.points_for_frames.items():
#         for point in points_list:
#             curve_Pack.points.extend([point.x, point.z, point.y])
#             print(point.x)

#     curve_Pack.pointsLen = len(curve_Pack.points) # len is also equal to the nr of frames 

#     vpet.curveList.append(curve_Pack)

# #! This function appears to work only for two-points curves, interpolating linearly between them
# def evaluate_curve(curve_object, frame):
#     # Set the current frame
#     bpy.context.scene.frame_set(frame)
    
#     evaluated_points = []
    
#     # Ensure the object is a curve and is using Bezier type
#     if curve_object.data.splines.active.type == 'BEZIER':
#         spline = curve_object.data.splines.active
        
#         # Evaluate the curve at current frame
#         evaluated_point = spline.bezier_points[0].co.lerp(spline.bezier_points[1].co, frame / bpy.context.scene.frame_end)
#         evaluated_points.append(evaluated_point)
    
#     return evaluated_points

##  Function that takes a curve object in the scene and samples it, filling the TRACER Curve Package with the obtained data 
#   IMPORTANT: The points sampled on the curve are added to the Curve Package in the format XZY (instead of XYZ) in order to
#   convert between the blender Z-up coord. space and the more conventional Y-up space
#   @param      curve       An object (of type \'CURVE\' in the scene)
#   @returns    void        It appends a new Curve Package to the Curve List of the VPET environment (temporary solution)
def processCurve_alt(curve, objList):
    vpet = bpy.context.window_manager.vpet_data
    curve_Pack = curvePackage()
    curve_Pack.points = []
    curve_Pack.tangents = []

    evaluated_bezier, bezier_tangents = evaluate_bezier_multi_seg(curve)

    print("Size of evaluated_bezier " + str(len(evaluated_bezier)))
    for i in range(0,len(evaluated_bezier)):
        
        point = evaluated_bezier[i]
        curve_Pack.points.extend([point.x, point.y, point.z])
        print(point)

        tangent = bezier_tangents[i]
        curve_Pack.tangents.extend([tangent.x, tangent.y, tangent.z]) #! TO BE TESTED!!!
        print(tangent)

    curve_Pack.pointsLen = int(len(curve_Pack.points) / 3) # len is also equal to the nr of frames 

    vpet.curveList.append(curve_Pack)

##  Function that evaluates a bezier spline with multiple knots (control points) - only 2D curves supported
#   It selects the first spline element in a curve object, evaluates the various subsegments and returns the complete list of evaluated positions
#   The number of returned points is determined by the PATH DURATION value of the curve object
#   @param  curve_object    A specific curve object in the scene
#   @returns                A list of points (of size equal to the path_duration of the curve) sampled along the spline contained in the curve
def evaluate_bezier_multi_seg(curve_object):
    bezier_points = curve_object.data.splines[0].bezier_points  # List of control points in the (first) bezier spline in the curve object - only one spline per curve supported at the moment
    is_cyclic = curve_object.data.splines[0].use_cyclic_u       # Whether the curve is a closed loop or not
    num_frames = curve_object.data.path_duration                     # Number of total frames to generate in the curve

    #? curve_object.data.splines[0].sample_uniform_index_factors() # developer.blender.org/docs/features/objects/curve/

    if len(bezier_points) == 0:
        return [], []

    if len(bezier_points) == 1:
        knot = bezier_points[0]
        coord = knot.co.copy()
        tang  = knot.handle_left.copy()
        return [coord], tang

    evaluated_bezier = []
    tangent_bezier = []
    if is_cyclic:
        num_segments = len(bezier_points)   # Number of segments to be evaluated (if the spline is cyclic the number of segments is equal to the number of points)
        # Subdivide the total number of frames that have to be generated between the various bezier subsegments
        segment_frames = math.floor(num_frames / num_segments)
        # Accumulating possible approximation error in the first segment's frames
        first_segment_frames = num_frames - (segment_frames * (num_segments - 1))

        # Evaluate spline segments (excl. the cyclic part)
        for segment in range (0, num_segments - 1):
            evaluated_segment = []
            
            knot1 = bezier_points[segment].co
            handle1 = bezier_points[segment].handle_right
            knot2 = bezier_points[segment + 1].co
            handle2 = bezier_points[segment + 1].handle_left
            
            if segment == 0:
                evaluated_segment = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, first_segment_frames)
                #TODO use custom sample_bezier function
            else:
                evaluated_segment = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, segment_frames + 1) # Accounting for the removal of the first frame of every segment (it's redundant)
                #TODO use custom sample_bezier function
                evaluated_segment.pop(0)
            
            evaluated_bezier.extend(evaluated_segment)
        
        # Evaluate cyclic segment (between last and first knot in the list)
        evaluated_segment = []
            
        knot1 = bezier_points[-1].co
        handle1 = bezier_points[-1].handle_right
        knot2 = bezier_points[0].co
        handle2 = bezier_points[0].handle_left

        evaluated_segment = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, segment_frames)
        #TODO use custom sample_bezier function
        evaluated_bezier.extend(evaluated_segment)

        # Extract tangents at every evaluated point
        tangent_bezier.append(bezier_points[0].handle_right.normalized()) # first tangent can be extracted from the first handle
        for frame in range (1, num_frames - 1):
            dir1 = evaluated_bezier[frame] - evaluated_bezier[frame - 1] # Direction from point-1 to point 
            dir2 = evaluated_bezier[frame + 1] - evaluated_bezier[frame] # Direction from point to point+1
            tang = dir1.normalize() + dir2.normalize() # Average direction 
            tangent_bezier.append(tang.normalized())
        tangent_bezier.append(bezier_points[0].handle_left.normalized()) # last tangent can be extracted from the last handle

    else:
        num_segments = len(bezier_points) - 1   # Number of segments to be evaluated
        # Subdivide the total number of frames that have to be generated between the various bezier subsegments
        segment_frames = math.floor(num_frames / num_segments)
        # Accumulating possible approximation error in the first segment's frames
        first_segment_frames = num_frames - (segment_frames * (num_segments - 1)) 
        
        # Evaluate spline segments
        for segment in range (0, num_segments):
            evaluated_segment = []

            knot1 = bezier_points[segment].co
            handle1 = bezier_points[segment].handle_right
            knot2 = bezier_points[segment + 1].co
            handle2 = bezier_points[segment + 1].handle_left
            
            if segment == 0:
                evaluated_segment = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, first_segment_frames)
            else:
                evaluated_segment = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, segment_frames + 1) # Accounting for the removal of the first frame of every segment (it's redundant)
                evaluated_segment.pop(0)
            
            evaluated_bezier.extend(evaluated_segment)

        # Extract tangents at every evaluated point
        tangent_bezier.append(bezier_points[0].handle_right.normalized()) # first tangent can be extracted from the first handle
        for frame in range (1, num_frames - 1):
            dir1 = evaluated_bezier[frame] - evaluated_bezier[frame -1] # Direction from point-1 to point 
            dir2 = evaluated_bezier[frame+1] - evaluated_bezier[frame] # Direction from point to point+1
            tang = dir1.normalized() + dir2.normalized() # Average direction 
            tangent_bezier.append(tang.normalized())
        tangent_bezier.append(bezier_points[-1].handle_left.normalized()) # last tangent can be extracted from the last handle
    
    return evaluated_bezier, tangent_bezier

##  Function that ADAPTIVELY samples a cubic Beziér between two points - only 2D curves supported
#   It uses the timing information provided by the artist through the UI (frames, ease-in, ease-out) to sample a given segment of the control path
#   @param  b0          The coordinates of first point of the beziér segment
#   @param  b1          The right handle of the first point of the beziér segment
#   @param  b2          The left handle of the second point of the beziér segment
#   @param  b3          The coordinates of second point of the beziér segment
#   @param  resolution  How many points should be sampled on the segment, aka the frame delta betwen first and second point
#   @param  influence1  Speed rate for easing out of the first point, aka the ease-out value of the first point of the beziér segment
#   @param  influence2  Speed rate for easing into the second point, aka the ease-in value of the second point of the beziér segment
#   @returns            A list of points (of size equal to resolution) sampled along the beziér segment between b0 and b3 (with handles defined by b1 and b2)
def adaptive_sample_bezier(b0: Vector, b1: Vector, b2: Vector, b3: Vector, resolution: int, influence1: int , influence2: int) -> list[float]:
    sample: Vector
    sampled_segment = []
    # Sampling a cubic bezier spline between (0,0) and (1,1) given handles parallel to X and as strong as the passed influence values
    # This gives us a list of percentages for sampling the Control Path between two Control Points, with the given resolution and timings
    timings = mathutils.geometry.interpolate_bezier([0, 0], [influence1/100, 0], [1 - influence2/100, 1], [1, 1], resolution)
    
    # Sample the bezier segment between b0 and b3 given the sapmling rate in timings 
    for i, timing in enumerate(timings):
        t = timing.y
        sample = (                      math.pow((1-t), 3)) * b0 +\
                 (3 *          t      * math.pow((1-t), 2)) * b1 +\
                 (3 * math.pow(t, 2)  *          (1-t)    ) * b2 +\
                 (    math.pow(t, 3)                      ) * b3
        sampled_segment.extend([sample.x, sample.y, sample.z])
     
    return sampled_segment

## Implementation of a single slerp function, to limit dependencies from external librabries
# @param quat_1     value of the first Quaternion
# @param quat_2     value of the second Quaternion
# @param n_samples  number of samples to take on the range of the interpolation
# @returns          list spherical-linearly interpolated Quaternions 
def quaternion_slerp(quat_1: Quaternion, quat_2: Quaternion, n_samples: int) -> list[Quaternion]:
    t = 0
    step = 1 / n_samples
    angle = quat_1.dot(quat_2)
    samples = []

    for i in range(n_samples):
        sample = (math.sin(angle * (1-t)) / math.sin(angle)) * quat_1 +\
                 (math.sin(angle *    t ) / math.sin(angle)) * quat_2
        euler_sample = sample.to_euler()
        samples.extend([euler_sample.x, euler_sample.y, euler_sample.z])
        t += step
    
    return samples

##Create SceneObject for each object that will be sent iver network
#
#@param obj the acual object from the scene
def processEditableObjects(obj, index):
    is_editable = obj.get("VPET-Editable", False)
    print(obj.name + " VPET-Editable: " + str(is_editable))
    if is_editable:
        if obj.type == 'CAMERA':
            vpet.SceneObjects.append(SceneObjectCamera(obj))
        elif obj.type == 'LIGHT':
            if obj.data.type == 'SPOT':
                vpet.SceneObjects.append(SceneObjectSpotLight(obj))
            else:
                vpet.SceneObjects.append(SceneObjectLight(obj))
        elif obj.type == 'ARMATURE':
            vpet.SceneObjects.append(SceneCharacterObject(obj))
        else:
            vpet.SceneObjects.append(SceneObject(obj))
    

## Process a meshes material
#
# @param mesh The geo data to process
#
#  this breaks easily if the material has a complex setup
#  todo:
#  - should find a more stable way to traverse the shader node graph
#  - should maybe skip the whole object if it has a volume shader
def processMaterial(mesh):
    matPack = materialPackage()
    
    mat = mesh.active_material
    
    # get material data
    name = mesh.active_material.name
    matPack.type = 1
    src = "Standard" 
    matPack.textureId = -1
    
    # need to check if the material was already processed
    for i, n in enumerate(vpet.materialList):
        if n.name == name:
            return i
        

    matPack.name = bytearray(64)
    matPack.src = bytearray(64)
    
    for i, n in enumerate(mesh.active_material.name.encode()):
        matPack.name[i] = n
 

    for i, n in enumerate(src.encode()):
        matPack.src[i] = n    
    
    # getting the material data
    matPack.color = mesh.active_material.diffuse_color
    matPack.roughness = mesh.active_material.roughness
    matPack.specular = mesh.active_material.specular_intensity
    
    ## get into the node tree
    # find output of node tree
    out = None
    for n in (x for x in mat.node_tree.nodes if x.type == 'OUTPUT_MATERIAL'):
        out = n
        break

    # the node connected to the first input of the OUT should always be a shader
    shader = out.inputs[0].links[0].from_node
    
    if shader != None:
        tmpColor = shader.inputs[0].default_value
        matPack.color = (tmpColor[0], tmpColor[1], tmpColor[2], tmpColor[3])
        
        if shader.type == 'BSDF_PRINCIPLED':
            matPack.roughness = shader.inputs[7].default_value
            matPack.specular = shader.inputs[5].default_value
        
    # check if texture is plugged in
    matPack.tex = None
    links = shader.inputs[0].links
    if len(links) > 0:
        if links[0].from_node.type == 'TEX_IMAGE':
            matPack.tex = links[0].from_node.image
            

    if matPack.tex != None:
        matPack.textureId = processTexture(matPack.tex)
    
            
    matPack.diffuseTexture = matPack.tex
    matPack.materialID = len(vpet.materialList)
    vpet.materialList.append(matPack)
    return (len(vpet.materialList)-1)
    
## Process Texture
#
# @param tex Texture to process
def processTexture(tex):
    # check if texture is already processed
    for i, t in enumerate(vpet.textureList):
        if t.texture == tex.name_full:
            return i

    try:
        texFile = open(tex.filepath_from_user(), 'rb')
    except FileNotFoundError:
        print(f"Error: Texture file not found at {tex.filepath_from_user()}")
        return -1
    
    texBytes = texFile.read()
    
    texPack = texturePackage()
    texPack.colorMapData = texBytes
    texPack.colorMapDataSize = len(texBytes)
    texPack.width = tex.size[0]
    texPack.height = tex.size[1]
    texPack.format = 0
    
    texPack.texture = tex.name_full
    
    texFile.close()

    texBinary = bytearray([])
        
    #texBinary.extend(struct.pack('i', 0)) #type
    texBinary.extend(struct.pack('i', texPack.width))
    texBinary.extend(struct.pack('i', texPack.height))
    texBinary.extend(struct.pack('i', texPack.format))
    texBinary.extend(struct.pack('i', texPack.colorMapDataSize))
    texBinary.extend(texPack.colorMapData)
    
    vpet.textureList.append(texPack)
    
    # return index of texture in texture list
    return (len(vpet.textureList)-1)

def get_vertex_bone_weights_and_indices(vert):
    #for vert_idx, vert in enumerate(obj.data.vertices):
        # Retrieve the vertex groups and their weights for this vertex
        groups = [(g.group, g.weight) for g in vert.groups]
        
        # Sort the groups by weight in descending order
        groups.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to at most 4 bone influences
        groups = groups[:4]
        while len(groups) < 4:
            groups.append((0, 0.0))
        
        # Output the bone indices and weights for this vertex
        bone_indices = [g[0] for g in groups]
        bone_weights = [g[1] for g in groups]
        
        return bone_weights, bone_indices

def processGeoNew(mesh):
    geoPack = sceneMesh()
    mesh_identifier = generate_mesh_identifier(mesh)
    geoPack.identifier = mesh_identifier
    vertex_bone_weights = {}
    vertex_bone_indices = {}
    isParentArmature = False

    for existing_geo in vpet.geoList:
        if existing_geo.identifier == mesh_identifier:
            return vpet.geoList.index(existing_geo)

    if mesh.parent != None:
        if mesh.parent.type == 'ARMATURE':
            isParentArmature = True
            armature = mesh.parent
            bone_names = {bone.name: idx for idx, bone in enumerate(armature.data.bones)}
            

            for vert in mesh.data.vertices:
                weights, indices = get_vertex_bone_weights_and_indices(vert)
                vertex_bone_weights[vert.index] = weights
                vertex_bone_indices[vert.index] = indices

    #mesh.data.calc_normals_split()
    bm = bmesh.new()
    bm.from_mesh(mesh.data)

    # flipping faces because the following axis swap inverts them
    for f in bm.faces:
        bmesh.utils.face_flip(f)
    bm.normal_update()

    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    loop_triangles = bm.calc_loop_triangles()

    split_verts = {} # vertex data : some unique counted index using hash map for quick lookup
    index_buffer = []
    split_index_cur = 0 # index of vert after which the hash_map can later be sorted into a list again
    num_shared_verts = 0 # just for debugging purposes
    for tri in loop_triangles:
        for loop in tri:
            original_index = loop.vert.index
            co = loop.vert.co.copy().freeze()
            uv = loop[uv_layer].uv.copy().freeze()

            if mesh.data.polygons[0].use_smooth:
                normal = loop.vert.normal.copy().freeze() if loop.edge.smooth else loop.face.normal.copy().freeze()
            else:
                normal = loop.face.normal.copy().freeze()
            
            bone_weights = [0.0] * 4
            bone_indices = [-1] * 4
            if mesh.parent != None:
                if mesh.parent.type == 'ARMATURE':
                    bone_weights = vertex_bone_weights.get(original_index, [0.0] * 4)
                    bone_indices = vertex_bone_indices.get(original_index, [-1] * 4)

            #normal = loop.vert.normal.copy().freeze() if loop.edge.smooth else loop.face.normal.copy().freeze()
            new_split_vert = (co, normal, uv, tuple(bone_weights), tuple(bone_indices))
            split_vert_idx = split_verts.get(new_split_vert)
            if split_vert_idx == None: # no matching vert found, push new one with index and increment for next time
                split_vert_idx = split_index_cur
                split_verts[new_split_vert] = split_vert_idx
                split_index_cur += 1
            else:
                num_shared_verts += 1
            index_buffer.append(split_vert_idx)

    split_vert_items = list(split_verts.items())
    split_vert_items.sort(key=lambda x: x[1]) #sort by index
    interleaved_buffer = [item[0] for item in split_vert_items] # strip off index
    co_buffer, normal_buffer, uv_buffer, bone_weights_buffer, bone_indices_buffer = zip(*interleaved_buffer)


    # should unify the list sizes
    geoPack.vSize = len(co_buffer)
    geoPack.iSize = len(index_buffer)
    geoPack.nSize = len(normal_buffer)
    geoPack.uvSize = len(uv_buffer)
    geoPack.bWSize = 0
    geoPack.vertices = []
    geoPack.indices = []
    geoPack.normals = []
    geoPack.uvs = []
    geoPack.boneWeights = []
    geoPack.boneIndices = []

    if isParentArmature:
        for vert_data in interleaved_buffer:
            _, _, _, vert_bone_weights, vert_bone_indices = vert_data
            geoPack.boneWeights.extend(vert_bone_weights)
            geoPack.boneIndices.extend(vert_bone_indices)

        geoPack.bWSize = len(co_buffer)

    for i, vert in enumerate(interleaved_buffer):
        geoPack.vertices.append(vert[0][0])
        geoPack.vertices.append(vert[0][2])
        geoPack.vertices.append(vert[0][1])

        geoPack.normals.append(-vert[1][0])
        geoPack.normals.append(-vert[1][2])
        geoPack.normals.append(-vert[1][1])
        
        geoPack.uvs.append(vert[2][0])
        geoPack.uvs.append(vert[2][1])
    bm.free()

    
    geoPack.indices = index_buffer
    geoPack.mesh = mesh
    
    
    vpet.geoList.append(geoPack)
    return (len(vpet.geoList)-1)

def generate_mesh_identifier(obj):
    if obj.type == 'MESH':
        return f"Mesh_{obj.name}_{len(obj.data.vertices)}"
    elif obj.type == 'ARMATURE':
        return f"Armature_{obj.name}_{len(obj.data.bones)}"
    else:
        return f"{obj.type}_{obj.name}"

## generate Byte Arrays out of collected node data
def getHeaderByteArray():
    global headerByteData
    headerBin = bytearray([])
    
    lightIntensityFactor = 1.0
    senderID = int(vpet.cID)

    headerBin.extend(struct.pack('f', lightIntensityFactor))
    headerBin.extend(struct.pack('i', senderID))
    headerBin.extend(struct.pack('i', 60))# frame rate that should be modified later

    vpet.headerByteData.extend(headerBin)

def getNodesByteArray():
    for node in vpet.nodeList:
        nodeBinary = bytearray([])
        
        nodeBinary.extend(struct.pack('i', node.vpetType))
        nodeBinary.extend(struct.pack('i', node.editable)) #editable ?
        nodeBinary.extend(struct.pack('i', node.childCount))
        nodeBinary.extend(struct.pack('3f', *node.position))
        nodeBinary.extend(struct.pack('3f', *node.scale))
        nodeBinary.extend(struct.pack('4f', *node.rotation))
        nodeBinary.extend(node.name)
          
        if (node.vpetType == vpet.nodeTypes.index('GEO')):
            nodeBinary.extend(struct.pack('i', node.geoId))
            nodeBinary.extend(struct.pack('i', node.materialId))
            nodeBinary.extend(struct.pack('4f', *node.color))
            
        if (node.vpetType == vpet.nodeTypes.index('LIGHT')):
            nodeBinary.extend(struct.pack('i', node.lightType))
            nodeBinary.extend(struct.pack('f', node.intensity))
            nodeBinary.extend(struct.pack('f', node.angle))
            nodeBinary.extend(struct.pack('f', node.range))
            nodeBinary.extend(struct.pack('3f', *node.color))
            
        if (node.vpetType == vpet.nodeTypes.index('CAMERA')):
            nodeBinary.extend(struct.pack('f', node.fov))
            nodeBinary.extend(struct.pack('f', node.aspect))
            nodeBinary.extend(struct.pack('f', node.near))
            nodeBinary.extend(struct.pack('f', node.far))
            nodeBinary.extend(struct.pack('f', node.focalDist))
            nodeBinary.extend(struct.pack('f', node.aperture))
        
        if (node.vpetType == vpet.nodeTypes.index('SKINNEDMESH')):
            nodeBinary.extend(struct.pack('i', node.geoID))
            nodeBinary.extend(struct.pack('i', node.materialId))
            nodeBinary.extend(struct.pack('4f', *node.color))
            nodeBinary.extend(struct.pack('i', node.bindPoseLength))
            nodeBinary.extend(struct.pack('i', node.characterRootID))
            nodeBinary.extend(struct.pack('3f', *node.boundExtents))
            nodeBinary.extend(struct.pack('3f', *node.boundCenter))
            nodeBinary.extend(struct.pack('%sf'% node.bindPoseLength * 16, *node.bindPoses))
            nodeBinary.extend(struct.pack('%si'% node.skinnedMeshBoneIDsSize, *node.skinnedMeshBoneIDs))
        
                    
        vpet.nodesByteData.extend(nodeBinary)

## pack geo data into byte array
def getGeoBytesArray():        
    for geo in vpet.geoList:
        geoBinary = bytearray([])
        
        geoBinary.extend(struct.pack('i', geo.vSize))
        geoBinary.extend(struct.pack('%sf' % geo.vSize*3, *geo.vertices))
        geoBinary.extend(struct.pack('i', geo.iSize))
        geoBinary.extend(struct.pack('%si' % geo.iSize, *geo.indices))
        geoBinary.extend(struct.pack('i', geo.nSize))
        geoBinary.extend(struct.pack('%sf' % geo.nSize*3, *geo.normals))
        geoBinary.extend(struct.pack('i', geo.uvSize))
        geoBinary.extend(struct.pack('%sf' % geo.uvSize*2, *geo.uvs))
        geoBinary.extend(struct.pack('i', geo.bWSize))
        if(geo.bWSize > 0):
            geoBinary.extend(struct.pack('%sf' % geo.bWSize*4, *geo.boneWeights))
            geoBinary.extend(struct.pack('%si' % geo.bWSize*4, *geo.boneIndices))

        
        vpet.geoByteData.extend(geoBinary)

## pack texture data into byte array        
def getTexturesByteArray():
    if len(vpet.textureList) > 0:
        for tex in vpet.textureList:
            texBinary = bytearray([])
    
            texBinary.extend(struct.pack('i', tex.width))
            texBinary.extend(struct.pack('i', tex.height))
            texBinary.extend(struct.pack('i', tex.format))
            texBinary.extend(struct.pack('i', tex.colorMapDataSize))
            texBinary.extend(tex.colorMapData)
            
            vpet.texturesByteData.extend(texBinary)

## pack Material data into byte array        
def getMaterialsByteArray():
    if len(vpet.materialList) > 0:
        for mat in vpet.materialList:
            matBinary = bytearray([])
            matBinary.extend(struct.pack('i', mat.type)) #type
            matBinary.extend(struct.pack('i', 64))# name.size
            matBinary.extend(mat.name) # mat name
            matBinary.extend(struct.pack('i', 64)) # src.size
            matBinary.extend(mat.src) # src
            matBinary.extend(struct.pack('i', mat.materialID)) # mat id
            matBinary.extend(struct.pack('i', len(vpet.textureList)))# tex id size
            if(mat.textureId != -1):
                matBinary.extend(struct.pack('i', mat.textureId))# tex id
                matBinary.extend(struct.pack('f', 0)) # tex offsets
                matBinary.extend(struct.pack('f', 0)) # tex offsets
                matBinary.extend(struct.pack('f', 1)) # tex scales
                matBinary.extend(struct.pack('f', 1)) # tex scales

            vpet.materialsByteData.extend(matBinary) 

def getCharacterByteArray():
    if len(vpet.characterList):
        for chr in vpet.characterList:
            charBinary = bytearray([]) 
            
            charBinary.extend(struct.pack('i', chr.bMSize))
            charBinary.extend(struct.pack('i', chr.sMSize)) 
            charBinary.extend(struct.pack('i', chr.characterRootID))
            
            formatBoneMapping = f'{len(chr.boneMapping)}i'
            formatSkeletonMapping = f'{len(chr.skeletonMapping)}i'
            charBinary.extend(struct.pack(formatBoneMapping, *chr.boneMapping))
            charBinary.extend(struct.pack(formatSkeletonMapping, *chr.skeletonMapping))
            
            charBinary.extend(struct.pack('%sf' % chr.sMSize*3, *chr.bonePosition))
            charBinary.extend(struct.pack('%sf' % chr.sMSize*4, *chr.boneRotation))
            charBinary.extend(struct.pack('%sf' % chr.sMSize*3, *chr.boneScale))

            vpet.charactersByteData.extend(charBinary) 

           
def getCurvesByteArray():
    vpet = bpy.context.window_manager.vpet_data
    vpet.curvesByteData.clear()
    for curve in vpet.curveList:
        curveBinary = bytearray([])
        curveBinary.extend(struct.pack('i', curve.pointsLen))
        curveBinary.extend(struct.pack('%sf' % len(curve.points), *curve.points))
        curveBinary.extend(struct.pack('%sf' % len(curve.look_at), *curve.look_at))

        vpet.curvesByteData.extend(curveBinary)

def resendCurve():
    vpet = bpy.context.window_manager.vpet_data
    if bpy.context.selected_objects[0].type == 'CURVE' :
        vpet.curvesByteData = bytearray([])
        vpet.curveList = []
        processCurve_alt(bpy.context.selected_objects[0], vpet.objectsToTransfer)
        getCurvesByteArray()

        # TODO MAKE IT NICER AFTER FMX!!!!!

    