/*
TRACER Scene Distribution Plugin Unreal Engine
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Unreal Engine is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Unreal Engine development.
 
The TRACER Scene Distribution Plugin Unreal Engine is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Unreal Engine is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Unreal Engine may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Unreal Engine Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Unreal Engine by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Unreal Engine in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
#pragma once

#include <vector>


namespace VPET
{
	enum LodMode { ALL, TAG }; // is needed?
	enum NodeType { GROUP, GEO, LIGHT, CAMERA, SKINNEDMESH };
	enum LightType { SPOT, DIRECTIONAL, POINT, AREA, RECTANGLE, DISC, NONE };

	struct Node
	{
		bool editable = false;
		int childCount = 0;
		float position[3] = { 1, 2, 3 };
		float scale[3] = { 1, 2, 3 };
		float rotation[4] = { 1, 2, 3, 4 };
		char name[64] = { ' ' };
	};

	struct NodeGeo : Node
	{
		int geoId = -1;
		int materialId = -1;
		//float roughness = 0.166f;
		float color[4] = { 1,1,1,1 };
	};

	struct NodeLight : Node
	{
		int type = SPOT;
		float intensity = 1.0;
		float angle = 60.0;
		float range = 500.0;
		float color[3] = { 1.0,1.0,1.0 };
	};

	struct NodeCam : Node
	{
		float fov = 70;
		float aspect = 2;
		float nearPlane = 1.0f;
		float farPlane = 1000;
		float focalDist = 5;
		float aperture = 2;
	};

	struct ObjectPackage
	{
		ObjectPackage() :
			dagpath(""),
			instanceId("")
		{}
		std::string dagpath;
		std::string instanceId;
		std::vector<float> vertices;
		std::vector<int> indices;
		std::vector<float> normals;
		std::vector<float> uvs;
		std::vector<float> boneWeights;
		std::vector<int> boneIndices;
	};

	struct TexturePackage
	{
		//std::string path;
		int colorMapDataSize;
		int width;
		int height;
		// Texture format?
		// Texture?
		unsigned char* colorMapData;
	};

	struct MaterialPackage
	{
		int type = 0; //! The type of the material. 0=standard, 1=load by name, 2=new with shader by name,  3=new with shader from source, 4= .. 
		std::string name;
		std::string src;
		int materialId = -1;
		std::vector<int> textureIds;
		//std::vector<int> textureNameIds;
		std::vector<float> textureOffsets;
		std::vector<float> textureScales;
		std::vector<bool> shaderConfig;
		std::vector<int> shaderPropertyIds;
		std::vector<int> shaderPropertyTypes;
		//std::vector<char> shaderProperties; // maybe unsigned char* ?
		//std::vector<float> shaderProperties;
		std::vector<char> shaderProperties;
	};

	struct VpetHeader
	{
		float lightIntensityFactor = 1.0;
		unsigned char senderID;
		//int textureBinaryType = 0;
	};

	class SceneDistributorState
	{
	public:
		SceneDistributorState() :
			numLights(0),
			numCameras(0),
			numObjectNodes(0),
			textureBinaryType(0)
		{}

		~SceneDistributorState()
		{
			for (int i = 0; i < nodeList.size(); i++) {
				delete nodeList[i];
			}
			nodeList.clear();
		}

	public:
		// Distribution Handling
		LodMode lodMode;
		std::string lodTag;

		// Data
		VpetHeader vpetHeader;
		std::vector<Node*> nodeList;
		std::vector<NodeType> nodeTypeList;
		std::vector<ObjectPackage> objPackList;
		std::vector<TexturePackage> texPackList;
		std::vector<MaterialPackage> matPackList;
		int textureBinaryType;

		// Currently processed node
		Node* node;

		// For stats
		int numLights;
		int numCameras;
		int numObjectNodes;
	};

	// struct sizes 
	static const int sizeof_node = sizeof(Node);
	static const int sizeof_nodegeo = sizeof(NodeGeo);
	static const int sizeof_nodelight = sizeof(NodeLight);
	static const int sizeof_nodecam = sizeof(NodeCam);
}

