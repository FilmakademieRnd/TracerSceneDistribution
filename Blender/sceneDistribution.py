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
import math
import mathutils
import bmesh
import struct
import re
from bpy_extras.io_utils import axis_conversion

from mathutils import Vector, Quaternion, Matrix, Euler
from.settings import TracerData, TracerProperties
from .AbstractParameter import Parameter, NodeTypes
from .SceneObjects.SceneObject import SceneObject
from .SceneObjects.SceneObjectCamera import SceneObjectCamera
from .SceneObjects.SceneObjectLight import SceneObjectLight, LightTypes
from .SceneObjects.SceneObjectSpotLight import SceneObjectSpotLight
from .SceneObjects.SceneCharacterObject import SceneCharacterObject
from .JSONEXP import add_TRS, save_TRS_to_json, add_bind_pose
#from .Avatar_HumanDescription import blender_to_unity_bone_mapping


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

def clear_tracer_data():
    global tracer_data, tracer_props
    tracer_data  = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    
    tracer_data.scene_obj_map.clear()
    tracer_data.objectsToTransfer.clear()
    tracer_data.nodeList.clear()
    tracer_data.geoList.clear()
    tracer_data.materialList.clear()
    tracer_data.textureList.clear()
    tracer_data.editableList.clear()
    tracer_data.characterList.clear()
    tracer_data.curveList.clear()
    tracer_data.editable_objects.clear()
    tracer_data.SceneObjects.clear()
    
    tracer_data.nodesByteData.clear()
    tracer_data.geoByteData.clear()
    tracer_data.texturesByteData.clear()
    tracer_data.headerByteData.clear()
    tracer_data.materialsByteData.clear()
    tracer_data.charactersByteData.clear()
    tracer_data.curvesByteData.clear()

## General function to gather scene data
#
def gather_scene_data():
    clear_tracer_data()
    tracer_data.cID = int(str(tracer_props.server_ip).split('.')[3])
    print(tracer_data.cID)
    object_list = get_object_list()

    if len(object_list) > 0:
        tracer_data.objectsToTransfer = object_list
        #iterate over all objects in the scene
        for i, obj in enumerate(tracer_data.objectsToTransfer):
            process_scene_object(obj, i)

        for i, obj in enumerate(tracer_data.objectsToTransfer):
            process_editable_objects(obj, i)

        get_header_byte_array()
        get_nodes_byte_array()
        get_geo_bytes_array()
        get_materials_byte_array()
        get_textures_byte_array()
        get_character_byte_array()
        #getCurvesByteArray()
        
        save_TRS_to_json()
        return len(tracer_data.objectsToTransfer)
    
    else:
        return 0
    

def get_object_list():
    parent_object_name = "TRACER Scene Root"
    parent_object = bpy.data.objects.get(parent_object_name)
    object_list = [parent_object]
    object_list.extend(parent_object.children_recursive)
    return object_list
    
## Process and store a scene object
#
# @param obj The scene object to process
# @param index The objects index in the list of all objects
def process_scene_object(obj: bpy.types.Object, index):
    global tracer_data, tracer_props
    node = sceneObject()
    node.tracer_type = NodeTypes.GROUP
    
    # gather light data
    if obj.type == 'LIGHT':
        nodeLight = sceneLight()
        nodeLight.tracer_type = NodeTypes.LIGHT
        nodeLight.light_type = LightTypes[obj.data.type]
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
        nodeCamera.tracer_type = NodeTypes.CAMERA
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
            node = process_skinned_mesh(obj, nodeSkinMesh)
        else:
            nodeMesh = sceneMesh()
            node = process_mesh(obj, nodeMesh)
                
    elif obj.type == 'ARMATURE':
        node.tracer_type = NodeTypes.CHARACTER
        process_character(obj, tracer_data.objectsToTransfer)
    
    # When finding an Animation Path to be distributed
    #if obj.name == "AnimPath":
    #    process_control_path(obj)
    blender_to_unity = Matrix([
                [1,  0,  0,  0],
                [0,  0,  1,  0],
                [0,  1,  0,  0],
                [0,  0,  0,  1]
            ])
    
    if obj.name == "TRACER Scene Root": 
        nodeMatrix =  blender_to_unity @  obj.matrix_local.copy()
    else:
        nodeMatrix = obj.matrix_local.copy()

    node.position = nodeMatrix.to_translation()
    node.scale = nodeMatrix.to_scale()

    # camera and light rotation offset
    if obj.type == 'CAMERA' or obj.type == 'LIGHT':
        rotFix = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')
        nodeMatrix = nodeMatrix @ rotFix

   
    #rotFix = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')
    rot = (nodeMatrix).to_quaternion()
    #rot.invert()
    node.rotation = (rot[1], rot[2], rot[3], rot[0])
    
    add_TRS(nodeMatrix, obj.name)

    node.name = bytearray(64)
    
    for i, n in enumerate(obj.name.encode()):
        node.name[i] = n
    node.childCount = len(obj.children)
    
    # Assign the child count of the root object
    #if obj.name == 'TRACER Scene Root':
        #node.childCount = tracer_data.rootChildCount
    
    node.tracer_id = index

    node.editable = int(obj.get("TRACER-Editable", False))
    tracer_data.editable_objects.append(obj)

    #if obj.name != 'TRACER Scene Root':
    tracer_data.nodeList.append(node)
    
def process_mesh(obj, nodeMesh): 
    nodeMesh.tracer_type = NodeTypes.GEO
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
        nodeMaterial = tracer_data.materialList[nodeMesh.materialId]
                    
        # add material parameters to node
        nodeMesh.color = nodeMaterial.color
        nodeMesh.roughness = nodeMaterial.roughness
        nodeMesh.specular = nodeMaterial.specular
                    
    return(nodeMesh)

def process_skinned_mesh(obj, nodeSkinMesh):
    nodeSkinMesh.tracer_type = NodeTypes.SKINNEDMESH
    nodeSkinMesh.color = (0,0,0,1)
    nodeSkinMesh.roughness = 0.5
    nodeSkinMesh.materialId = -1
    nodeSkinMesh.characterRootID = tracer_data.objectsToTransfer.index(obj.parent)
    
    nodeSkinMesh.geoID = processGeoNew(obj)
    # get material of mesh
    nodeMaterial = materialPackage()
    mat = obj.active_material
    if mat != None:
        nodeSkinMesh.materialId = processMaterial(obj)
        nodeMaterial = tracer_data.materialList[nodeSkinMesh.materialId]
        
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
            armature_data = armature_obj.data  # Accessing the armature data for static bone information
            bind_poses = []
            root_transform = armature_obj.matrix_world
            
            
            blender_to_unity = Matrix([
                [1,  0,  0,  0],
                [0,  0,  1,  0],
                [0,  1,  0,  0],
                [0,  0,  0,  1]
            ])

            for bone in armature_data.bones:


                bone_local_transform = bone.matrix_local.copy()
                bone_local_transform = bone_local_transform.inverted()
                #bone_local_transform = bone_local_transform @ root_transform
                #bone_local_transform = blender_to_unity @ bone_local_transform
                #(old_local_pose, old_local_rot, old_local_scl) = bone_local_transform.decompose()
                #old_local_pose = old_local_pose.xzy
                #old_local_rot = Quaternion((old_local_rot.x, old_local_rot.z, old_local_rot.y, old_local_rot.w))
                #old_local_rot.rotate(Euler((math.radians(-90), 0 ,0), 'XZY'))
                #old_local_scl = old_local_scl.xzy
                #bone_local_transform = Matrix.LocRotScale(old_local_pose, old_local_rot, old_local_scl)

                add_bind_pose(bone_local_transform, bone.name)# FOR JSON EXPORT

                # Flatten and append each row of the matrix
                for row in bone_local_transform:
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
                for idx, obj in enumerate(tracer_data.objectsToTransfer):
                    if obj.name == bone.name:
                        bone_index = idx
                        break
            #for i, bone in enumerate(armature_data.bones):  
                nodeSkinMesh.skinnedMeshBoneIDs[i] = bone_index
                print("POSE "+str(nodeSkinMesh.skinnedMeshBoneIDs[i]) +" " + bone.name)
                

        nodeSkinMesh.skinnedMeshBoneIDsSize = len(nodeSkinMesh.skinnedMeshBoneIDs)        

        return(nodeSkinMesh)


#! The part that processes a "Humanoid Rig" character is probably no longer valid
def process_character(armature_obj, object_list):
    chr_pack = characterPackage()
    chr_pack.bonePosition = []
    chr_pack.boneRotation = []
    chr_pack.boneScale = []
    chr_pack.boneMapping = []
    chr_pack.skeletonMapping = []
        

    if armature_obj.type == 'ARMATURE':
        bones = armature_obj.data.bones
        chr_pack.characterRootID = tracer_data.objectsToTransfer.index(armature_obj)

        if(tracer_props.humanoid_rig):
            raise RuntimeError("Update Humanoid Rig implementation")
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
                for idx, obj in enumerate(tracer_data.objectsToTransfer):
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
    tracer_data.characterList.append(chr_pack)
    return chr_pack

## Given a Control Path in the scene, it evaluates it, it fills a new Curve Package object with the sampled data, and adds it to the list of curves to be shared with the other TRACER clients
# @param control_point_list List of Control Points defining the Control Path
# @param is_cyclic          Whether the Control Path is cyclic or not (acyclic by default)
# @returns  None            It doesn't return anything, but appends the evaluated curve (@see curvePackage()) to tracer_data.curveList (@see TracerData())
def process_control_path(anim_path: bpy.types.Object) -> curvePackage:
    tracer_data = bpy.context.window_manager.tracer_data
    curve_package = curvePackage()
    curve_package.points  = [] # list of floats [pos0.x, pos0.y, pos0.z, pos1.x, pos1.y, pos1.z, ..., posN.x, posN.y, posN.z]
    curve_package.look_at = [] # list of floats [rot0.x, rot0.y, rot0.z, rot1.x, rot1.y, rot1.z, ..., rotN.x, rotN.y, rotN.z]
    value_error_msg = "The frame value of any point MUST be greater than the previous one!"

    control_points = anim_path["Control Points"]
    bezier_points  = anim_path.children[0].data.splines[0].bezier_points

    for i, point in enumerate(control_points):
        # Read the attribute of the first point of the segment
        coords_point_one    = bezier_points[i].co
        r_handle_point_one  = bezier_points[i].handle_right
        frame_point_one     = point.get("Frame")
        ease_out_point_one  = point.get("Ease Out")

        if anim_path.get("Is Cyclic", False):
            if i == 0:
                # If cyclic, we assume that the frame of the first point is 0 at the beginning of the path and point.get("Frame") at the end 
                frame_point_one = 0

            if i == len(control_points)-1:
                # If the path is cyclic and we are at the end of the path,
                # Evaluate segment between last and fist point of the path
                next_point = control_points[0]
                value_error_msg = "When cyclic, the frame value of the first point MUST be greater than the last one!"
        else:
            if i < len(control_points)-1:
                next_point = control_points[i+1]
            else:
                next_point = None
        
        if next_point != None:
            # Read the attribute of the second point of the segment
            coords_point_two    = bezier_points[i+1].co
            l_handle_point_two  = bezier_points[i+1].handle_left
            frame_point_two     = next_point.get("Frame")        
            ease_in_point_two   = next_point.get("Ease In")

            segment_frames = frame_point_two - frame_point_one + 1      # Compute number of samples in the segment 

            if segment_frames > 0:
                # Sampling a cubic bezier spline between (0,0) and (1,1) given handles parallel to X and as strong as the passed influence values
                # This gives us a list of percentages for sampling the Control Path between two Control Points, with the given resolution and timings
                timings = adaptive_timings_resampling(ease_out_point_one/100, ease_in_point_two/100, segment_frames)
                
                evaluated_positions = adaptive_sample_bezier(coords_point_one, r_handle_point_one, l_handle_point_two, coords_point_two, timings)
                # Probably it is necessary to check whether Eulers or Quaternions are used by the user to define pointer rotations (more often than not Eulers are used though)
                evaluated_rotations = rotation_interpolation(point.rotation_euler.to_quaternion(), next_point.rotation_euler.to_quaternion(), timings)
                
                # Removing the 3 elements (points coordinates and euler angle respectively) from the two lists for all the segments but not the last (to avoid duplicates)
                if i < len(control_points)-2:
                    evaluated_positions = evaluated_positions[: len(evaluated_positions) - 3]
                    evaluated_rotations = evaluated_rotations[: len(evaluated_rotations) - 3]

                curve_package.points.extend(evaluated_positions)
                curve_package.look_at.extend(evaluated_rotations) 
            else:
                bpy.context.window_manager.report({"ERROR"}, value_error_msg)
    
    curve_package.pointsLen = int(len(curve_package.points) / 3)
    tracer_data.curveList =  [curve_package]
    return curve_package

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
def adaptive_sample_bezier(knot1: Vector, handle1: Vector, handle2: Vector, knot2: Vector, timings: list[float]) -> list[float]:
    sample: Vector
    sampled_segment = []

    # Sample the bezier segment between b0 and b3 given the sapmling rate in timings 
    for t in timings:
        sample = sample_bezier(knot1, handle1, handle2, knot2, t)
        sampled_segment.extend([sample.x, sample.y, sample.z])
    
    return sampled_segment

def adaptive_timings_resampling(ease_from: float, ease_to: float, resolution: int) -> list [float]:
    timings = []
    # Good results with oversampling by a factor of 10 but no interpolation or with interpolation but no oversampling 
    pre_sampling = mathutils.geometry.interpolate_bezier(Vector((0,0)), Vector((ease_from,0)), Vector((1-ease_to,1)), Vector((1,1)), 10*resolution)

    for i in range(resolution):
        t = i / resolution
        j = 0

        while pre_sampling[j].x <= t:
            j += 1

        t1 = (t - pre_sampling[j-1].x) / (pre_sampling[j].x - pre_sampling[j-1].x)
        eased_t = t1 * pre_sampling[j].y + (1-t1) * pre_sampling[j-1].y
        #eased_t = pre_sampling[j].y
        
        timings.append(eased_t)
		
    return timings

def sample_bezier(knot1: Vector, handle1: Vector, handle2: Vector, knot2: Vector, t: float) -> Vector:
    sample = (                      math.pow((1-t), 3)) * knot1   +\
             (3 *          t      * math.pow((1-t), 2)) * handle1 +\
             (3 * math.pow(t, 2)  *          (1-t)    ) * handle2 +\
             (    math.pow(t, 3)                      ) * knot2
    return sample


## Implementation of a single slerp function, to limit dependencies from external librabries
# @param quat_1     value of the first Quaternion
# @param quat_2     value of the second Quaternion
# @param n_samples  number of samples to take on the range of the interpolation
# @returns          list of directional vectors derived from the spherical-linearly interpolated Quaternions 
def rotation_interpolation(quat_1: Quaternion, quat_2: Quaternion, timings: list[float]) -> list[Vector]:
    samples = []

    for t in timings:
        # quat_slerp = (math.sin(angle * (1-t)) / math.sin(angle)) * quat_1 +\
        #              (math.sin(angle *    t ) / math.sin(angle)) * quat_2
        quat_slerp = quat_1.slerp(quat_2, t)
        fwd_vector = Vector((0, -1, 0))
        fwd_vector.rotate(quat_slerp)
        samples.extend([fwd_vector.x, fwd_vector.y, fwd_vector.z])
    
    return samples

## Create SceneObject for each object that will be sent over network
#
#@param obj the acual object from the scene
def process_editable_objects(obj, index):
    is_editable = obj.get("TRACER-Editable", False)
    print(obj.name + " TRACER-Editable: " + str(is_editable))
    if is_editable:
        if obj.type == 'CAMERA':
            tracer_data.SceneObjects.append(SceneObjectCamera(obj))
        elif obj.type == 'LIGHT':
            if obj.data.type == 'SPOT':
                tracer_data.SceneObjects.append(SceneObjectSpotLight(obj))
            else:
                tracer_data.SceneObjects.append(SceneObjectLight(obj))
        elif obj.type == 'ARMATURE':
            tracer_data.SceneObjects.append(SceneCharacterObject(obj))
        else:
            tracer_data.SceneObjects.append(SceneObject(obj))

        obj.tracer_id = len(tracer_data.SceneObjects) -1
    

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
    for i, n in enumerate(tracer_data.materialList):
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
    matPack.materialID = len(tracer_data.materialList)
    tracer_data.materialList.append(matPack)
    return (len(tracer_data.materialList)-1)
    
## Process Texture
#
# @param tex Texture to process
def processTexture(tex):
    # check if texture is already processed
    for i, t in enumerate(tracer_data.textureList):
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
    
    tracer_data.textureList.append(texPack)
    
    # return index of texture in texture list
    return (len(tracer_data.textureList)-1)

def get_vertex_bone_weights_and_indices(vert, mesh_obj, armature):
    #for vert_idx, vert in enumerate(obj.data.vertices):
        # Retrieve the vertex groups and their weights for this vertex
        groups = [(g.group, g.weight) for g in vert.groups]
        
        # Sort the groups by weight in descending order
        groups.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to at most 4 bone influences
        groups = groups[:4]
        # Ensure there are 4 weights and indices
        while len(groups) < 4:
            groups.append((-1, 0.0))
        
        # Output the bone indices and weights for this vertex
        bone_indices = []
        bone_weights = [g[1] for g in groups]

        for g in groups:
            group_index = g[0]
            # Access the vertex group by index from the vertex's mesh object data
            bone_name = mesh_obj.vertex_groups[group_index].name  # Get the group name
            for idx, obj in enumerate(armature.data.bones):
                if obj.name == bone_name:
                    bone_index = idx
                    bone_indices.append(bone_index)
                    
        
        return bone_weights, bone_indices

def processGeoNew(mesh):
    geoPack = sceneMesh()
    mesh_identifier = generate_mesh_identifier(mesh)
    geoPack.identifier = mesh_identifier
    vertex_bone_weights = {}
    vertex_bone_indices = {}
    isParentArmature = False

    for existing_geo in tracer_data.geoList:
        if existing_geo.identifier == mesh_identifier:
            return tracer_data.geoList.index(existing_geo)

    if mesh.parent != None:
        if mesh.parent.type == 'ARMATURE':
            isParentArmature = True
            armature = mesh.parent
            bone_names = {bone.name: idx for idx, bone in enumerate(armature.data.bones)}
            

            for vert in mesh.data.vertices:
                weights, indices = get_vertex_bone_weights_and_indices(vert, mesh, armature)
                vertex_bone_weights[vert.index] = weights
                vertex_bone_indices[vert.index] = indices

    #mesh.data.calc_normals_split()
    bm = bmesh.new()

    bm.from_mesh(mesh.data)

    #bm.transform(Matrix(((1,0,0,0), (0,0,1,0), (0,1,0,0), (0,0,0,1))))
    # flipping faces because the following axis swap inverts them????
    #for f in bm.faces:
    #    bmesh.utils.face_flip(f)
    #bm.normal_update()

    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    loop_triangles: list[tuple[bmesh.types.BMLoop]] = bm.calc_loop_triangles()

    split_verts = {} # vertex data : some unique counted index using hash map for quick lookup
    index_buffer = []
    split_index_cur = 0 # index of vert after which the hash_map can later be sorted into a list again
    num_shared_verts = 0 # just for debugging purposes
    for tri in loop_triangles:
        for loop in tri:
            original_index = loop.vert.index
            co = loop.vert.co.copy().freeze()
            uv = loop[uv_layer].uv.copy().freeze()

            if mesh.data.polygons[0].use_smooth and loop.edge.smooth:
                normal = loop.vert.normal.copy().freeze()
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
            #print(vert_bone_indices)
            #print(vert_bone_weights)

        geoPack.bWSize = len(co_buffer)

    for i, vert in enumerate(interleaved_buffer):
        geoPack.vertices.append(vert[0][0])
        geoPack.vertices.append(vert[0][1])
        geoPack.vertices.append(vert[0][2])

        geoPack.normals.append(vert[1][0])
        geoPack.normals.append(vert[1][1])
        geoPack.normals.append(vert[1][2])
        
        geoPack.uvs.append(vert[2][0])
        geoPack.uvs.append(vert[2][1])
    bm.free()


    # Reverse triangle winding order to fix flipped faces
    #fixed_indices = []
    #for i in range(0, len(index_buffer), 3):  
    #    fixed_indices.append(index_buffer[i])      # First vertex remains the same
    #    fixed_indices.append(index_buffer[i + 2])  # Swap last and second
    #    fixed_indices.append(index_buffer[i + 1])  
    
    geoPack.indices = index_buffer
    geoPack.mesh = mesh
    
    
    tracer_data.geoList.append(geoPack)
    return (len(tracer_data.geoList)-1)

def generate_mesh_identifier(obj):
    if obj.type == 'MESH':
        return f"Mesh_{obj.name}_{len(obj.data.vertices)}"
    elif obj.type == 'ARMATURE':
        return f"Armature_{obj.name}_{len(obj.data.bones)}"
    else:
        return f"{obj.type}_{obj.name}"

### Generate Byte Arrays out of collected node data
def get_header_byte_array():
    global headerByteData
    headerBin = bytearray([])
    
    lightIntensityFactor = 1.0
    senderID = int(tracer_data.cID)

    headerBin.extend(struct.pack('f', lightIntensityFactor))
    headerBin.extend(struct.pack('i', senderID))
    headerBin.extend(struct.pack('i', 60))# frame rate that should be modified later

    tracer_data.headerByteData.extend(headerBin)

### Generate Byte Arrays out of generic Node Data
def get_nodes_byte_array():
    for node in tracer_data.nodeList:
        nodeBinary = bytearray([])
        
        nodeBinary.extend(struct.pack('i', node.tracer_type.value))
        nodeBinary.extend(struct.pack('i', node.editable)) #editable ?
        nodeBinary.extend(struct.pack('i', node.childCount))
        nodeBinary.extend(struct.pack('3f', *node.position))
        nodeBinary.extend(struct.pack('3f', *node.scale))
        nodeBinary.extend(struct.pack('4f', *node.rotation))
        nodeBinary.extend(node.name)
          
        if (node.tracer_type == NodeTypes.GEO):
            nodeBinary.extend(struct.pack('i', node.geoId))
            nodeBinary.extend(struct.pack('i', node.materialId))
            nodeBinary.extend(struct.pack('4f', *node.color))
            
        if (node.tracer_type == NodeTypes.LIGHT):
            nodeBinary.extend(struct.pack('i', node.light_type.value))
            nodeBinary.extend(struct.pack('f', node.intensity))
            nodeBinary.extend(struct.pack('f', node.angle))
            nodeBinary.extend(struct.pack('f', node.range))
            nodeBinary.extend(struct.pack('3f', *node.color))
            
        if (node.tracer_type == NodeTypes.CAMERA):
            nodeBinary.extend(struct.pack('f', node.fov))
            nodeBinary.extend(struct.pack('f', node.aspect))
            nodeBinary.extend(struct.pack('f', node.near))
            nodeBinary.extend(struct.pack('f', node.far))
            nodeBinary.extend(struct.pack('f', node.focalDist))
            nodeBinary.extend(struct.pack('f', node.aperture))
        
        if (node.tracer_type == NodeTypes.SKINNEDMESH):
            nodeBinary.extend(struct.pack('i', node.geoID))
            nodeBinary.extend(struct.pack('i', node.materialId))
            nodeBinary.extend(struct.pack('4f', *node.color))
            nodeBinary.extend(struct.pack('i', node.bindPoseLength))
            nodeBinary.extend(struct.pack('i', node.characterRootID))
            nodeBinary.extend(struct.pack('3f', *node.boundExtents))
            nodeBinary.extend(struct.pack('3f', *node.boundCenter))
            nodeBinary.extend(struct.pack('%sf'% node.bindPoseLength * 16, *node.bindPoses))
            nodeBinary.extend(struct.pack('%si'% node.skinnedMeshBoneIDsSize, *node.skinnedMeshBoneIDs))
        
                    
        tracer_data.nodesByteData.extend(nodeBinary)

### Pack geometric data into byte array
def get_geo_bytes_array():        
    for geo in tracer_data.geoList:
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

        
        tracer_data.geoByteData.extend(geoBinary)

### Pack texture data into byte array        
def get_textures_byte_array():
    if len(tracer_data.textureList) > 0:
        for tex in tracer_data.textureList:
            texBinary = bytearray([])
    
            texBinary.extend(struct.pack('i', tex.width))
            texBinary.extend(struct.pack('i', tex.height))
            texBinary.extend(struct.pack('i', tex.format))
            texBinary.extend(struct.pack('i', tex.colorMapDataSize))
            texBinary.extend(tex.colorMapData)
            
            tracer_data.texturesByteData.extend(texBinary)

### Pack Material data into byte array        
def get_materials_byte_array():
    if len(tracer_data.materialList) > 0:
        for mat in tracer_data.materialList:
            matBinary = bytearray([])
            matBinary.extend(struct.pack('i', mat.type)) #type
            matBinary.extend(struct.pack('i', 64))# name.size
            matBinary.extend(mat.name) # mat name
            matBinary.extend(struct.pack('i', 64)) # src.size
            matBinary.extend(mat.src) # src
            matBinary.extend(struct.pack('i', mat.materialID)) # mat id
            matBinary.extend(struct.pack('i', len(tracer_data.textureList)))# tex id size
            if(mat.textureId != -1):
                matBinary.extend(struct.pack('i', mat.textureId))# tex id
                matBinary.extend(struct.pack('f', 0)) # tex offsets
                matBinary.extend(struct.pack('f', 0)) # tex offsets
                matBinary.extend(struct.pack('f', 1)) # tex scales
                matBinary.extend(struct.pack('f', 1)) # tex scales

            tracer_data.materialsByteData.extend(matBinary) 

### Pack Character data into singular byte array
def get_character_byte_array():
    if len(tracer_data.characterList):
        for chr in tracer_data.characterList:
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

            tracer_data.charactersByteData.extend(charBinary) 

#! DEPRECATED           
# def getCurvesByteArray():
#     tracer_data = bpy.context.window_manager.tracer_data
#     tracer_data.curvesByteData.clear()
#     for curve in tracer_data.curveList:
#         curveBinary = bytearray([])
#         curveBinary.extend(struct.pack('i', curve.pointsLen))
#         curveBinary.extend(struct.pack('%sf' % len(curve.points), *curve.points))
#         curveBinary.extend(struct.pack('%sf' % len(curve.look_at), *curve.look_at))
#    
#         tracer_data.curvesByteData.extend(curveBinary)

# def resendCurve():
#     tracer_data = bpy.context.window_manager.tracer_data
#     if bpy.context.active_object.type == 'ARMATURE' and bpy.context.active_object.get("Control Path") != None:
#         control_path_obj: bpy.types.Object = bpy.context.active_object.get("Control Path")
#         tracer_data.curvesByteData = bytearray([])
#         tracer_data.curveList = []
#         processControlPath(control_path_obj)
#         getCurvesByteArray()
    