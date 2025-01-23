import bpy
import json
import os
from mathutils import Matrix

def serialize_mesh_with_weights_and_triangles_and_bones_and_material(obj):
    if obj.type != 'MESH':
        raise ValueError(f"{obj.name} is not a mesh object")

    mesh = obj.data

    # Extract vertices
    vertices = [{"x": v.co.x, "y": v.co.y, "z": v.co.z} for v in mesh.vertices]
    print(f"Total vertices exported: {len(vertices)}")

    # Extract triangles (ensure only triangular faces)
    triangles = []
    for poly in mesh.polygons:
        if len(poly.vertices) == 3:  # Only triangles
            triangles.extend(poly.vertices)
        else:
            print(f"Warning: Non-triangular face detected in {obj.name}.")

    print(f"Total triangles exported: {len(triangles)}")

    # Extract vertex weights (for bone deformation)
    weights = []
    for vert in mesh.vertices:
        vert_weights = []
        for group in vert.groups:
            group_name = obj.vertex_groups[group.group].name
            vert_weights.append({
                "bone": group_name,
                "weight": group.weight
            })
        if not vert_weights:  # Ensure every vertex has weights
            vert_weights.append({
                "bone": "DefaultBone",  # Replace with a fallback bone name if needed
                "weight": 1.0
            })
        weights.append(vert_weights)

    print(f"Total weights exported: {len(weights)}")

    # Check if vertex count matches weight count
    if len(vertices) != len(weights):
        raise ValueError(f"Mismatch detected: {len(vertices)} vertices but {len(weights)} weights.")

    # Extract bones from the armature and their parent-child relationships
    armature = obj.find_armature()
    if armature:
        bone_names = []
        bone_parent_child = []
        bone_data = []
       
        nodeMatrix = armature.matrix_local.copy()
        rot = nodeMatrix.to_quaternion()
        #rot.invert()

        for bone in armature.pose.bones:
            # Skip bones with empty or null names
            if not bone.name:
                print(f"Warning: Found a bone with an empty or null name. Skipping.")
                continue

            # Add bone name to the list
            bone_names.append(bone.name)

            # Capture parent-child relationships
            if bone.parent:
                bone_parent_child.append({
                    "parentBone": bone.parent.name,
                    "childBone": bone.name
                })
            else:
                # Root bone has no parent
                bone_parent_child.append({
                    "parentBone": None,
                    "childBone": bone.name
                })
                

            # Get the bind pose
            bind_matrix = bone.matrix_local  # Local bone matrix
            bp_matrix = bind_matrix.inverted()  # Bone's bind pose matrix
            bp_matrix_world = armature.matrix_world @ bp_matrix  # Transform to world space

            # Serialize the bone data
            bone_data.append({
                "name": bone.name,
                "position": {"x": nodeMatrix.to_translation().x, "y": nodeMatrix.to_translation().y, "z": nodeMatrix.to_translation().z},
                "scale": {"x": nodeMatrix.to_scale().x, "y": nodeMatrix.to_scale().y, "z": nodeMatrix.to_scale().z},
                "rotation": {
                    "x": rot[1],
                    "y": rot[2],
                    "z": rot[3],
                    "w": rot[0]
                },
                "bindPoseMatrix": [list(row) for row in bp_matrix_world]
            })

        print(f"Total bones exported: {len(bone_names)}")
    else:
        bone_names = []
        bone_parent_child = []
        bone_data = []

    # Extract materials assigned to the mesh (if any)
    materials = []
    if obj.material_slots:
        for mat_slot in obj.material_slots:
            material_data = {
                "name": mat_slot.name,
                "material": mat_slot.material.name if mat_slot.material else None,
                "shader": None,
                "textures": []
            }

            # Check if the material uses nodes (node-based material)
            if mat_slot.material and mat_slot.material.use_nodes:
                material_data["shader"] = mat_slot.material.node_tree.nodes.get("Principled BSDF").name if mat_slot.material.node_tree else None

                # Check if the material has texture nodes
                if mat_slot.material.node_tree:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            material_data["textures"].append(node.image.name)

            # Add material data to the materials list
            materials.append(material_data)

    print(f"Total materials exported: {len(materials)}")

    # Return the serialized data including bone data, parent-child relationships, bind pose, and materials
    return {
        "vertices": vertices,
        "triangles": triangles,
        "weights": weights,
        "bones": bone_names,  # Include bones from the armature
        "boneParentChild": bone_parent_child,  # Include parent-child relationships
        "boneData": bone_data,  # Includes positions, rotations, and bind pose matrices
        "materials": materials  # Include materials
    }

# Select the mesh object
mesh = bpy.data.objects.get('Survivor_Robot_Mesh')  # Replace with your mesh object name

if not mesh:
    raise ValueError("Mesh object 'Survivor_Robot_Mesh' not found. Ensure it exists in your Blender scene.")

# Serialize the mesh along with weights, triangles, bones, parent-child relationships, bind pose, and materials
serialized_mesh = serialize_mesh_with_weights_and_triangles_and_bones_and_material(mesh)

# Combine the data
data = {
    "mesh": serialized_mesh
}

# Save to a JSON file on the Desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_file = os.path.join(desktop_path, "character_data_with_materials_and_bind_pose.json")

# Save the serialized data
with open(output_file, "w") as f:
    json.dump(data, f, indent=4)

print(f"Character data saved to {output_file}")
