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

import functools
import math
from mathutils import Matrix, Quaternion, Vector, Euler
import copy
import bpy

#from ..settings import TracerProperties
from .SceneObjectMesh import SceneObjectMesh, NodeTypes, SceneDataMesh
from ..Core.ServerAdapter import send_parameter_update

### Subclass of SceneObject adding functionalities specific for Characters
class SceneObjectMeshSkinned(SceneObjectMesh):

    ### INHERITED FROM SceneObjectMesh
    # mesh_geometry_id
    # material_id
    # color
    # roughness
    # specular

    character_root_id: int
    bounding_box_center: Vector
    bounding_box_extents: Vector
    skinned_mesh_bone_ids: list[int] = [-1] * 99    # MAX 99 bones
    bind_poses: list[float] = [0.0] * 1584          # MAX 99 4*4 matrices for the bind poses (one for every bone) => 1584 floats

    ### Class constructor
    #   Initializing TRACER class variable (from line 82)
    #   Adding character-specific Properties to the Blender Object counterpart of the SceneObjectCharacter (from line 66)
    def __init__(self, obj: bpy.types.Object):
        # Initilising the SceneObjectSkinnedMesh as a regular SceneObjectMesh
        # This implies that the current SceneObjectSkinnedMesh (self) is already going to have a valid material_id and mesh_geometry_id
        super().__init__(obj)

        # The SceneDataMesh associated with self.mesh_geometry_id has to be augmented with the indices and weights taken from the armature data
        # self.mesh_geometry_id doesn't change
        self.process_skinned_mesh()

        self.tracer_type = NodeTypes.SKINNEDMESH

        # Initializing non-static class variables
        self.character_root_id = self.tracer_data.scene_objects.index(obj.parent)

        bounding_box_corners = [obj.parent.matrix_world @ Vector(corner) for corner in obj.parent.bound_box]    # List of Vectors represeting the corners of the bounding box of a character in world space
        self.bounding_box_center = Vector(sum(bounding_box_corners, Vector(0,0,0)) / 8).xzy                     # Average the coordinates of the corners to find the centre of the bounding box
        self.bounding_box_extents = Vector(abs(bounding_box_corners[0] - self.bounding_box_center)).xzy         # Calculate the extents: the (absolute value of the) distance between any corner and the centre of the bounding box
        
        armature_data: bpy.types.Armature = obj.parent.data
        for i, bone in enumerate(armature_data.bones):
            
            # Getting the current global transforms of all the bones in the armature and place the matrices values in the bind_poses array
            bind_matrix = obj.parent.matrix_world @ bone.matrix_local
            for row in bind_matrix:
                self.bind_poses[i*4: 4] = row
            
            # Getting the index of the TRACER SceneObject representing the cruuent bone and pplacing it the the list of bone IDs for this Skinned Mesh
            for j, scene_obj in enumerate(self.tracer_data.scene_objects):
                if scene_obj.name == bone.name:
                    self.skinned_mesh_bone_ids[i] = j       # The i-th bone in the skinned mesh corresponds to the j-th Scene Object in the TRacer Scene representation
                    break
    
    ### Process the Character-specific Mesh data 
    def process_skinned_mesh(self):
        mesh_data: SceneDataMesh = self.tracer_data.geometry_list[self.mesh_geometry_id]

        # Process bone vertices and indices
        vertex_bone_weights = {}
        vertex_bone_indices = {}

        mesh_vertices: bpy.types.MeshVertices = self.blender_object.data.vertices
        for vert in mesh_vertices:
            # Initialise (index-weight) pairs for every vertex in the mesh (capping the maximum number of elements to 4)
            simple_groups = [(-1, 0.0) * 4]

            # Retrieve the vertex groups and their weights for this vertex
            complete_groups = [(g.group, g.weight) for g in vert.groups]

            # Selecting the 4 most relevant weights
            complete_groups.sort(key=lambda x: x[1], reverse=True)
            complete_groups = complete_groups[:4]
            for n in range(0, 4):
                if len(complete_groups < n):
                    simple_groups = complete_groups[n]

            # Output the bone indices and weights for this vertex
            vertex_bone_indices[vert.index] = [g[0] for g in simple_groups]
            vertex_bone_weights[vert.index] = [g[1] for g in simple_groups]

        for og_idx in mesh_data.original_indices:
            mesh_data.bone_indices = vertex_bone_indices.get(og_idx, [-1] * 4)
            mesh_data.bone_weights = vertex_bone_weights.get(og_idx, [0.0] * 4)
        