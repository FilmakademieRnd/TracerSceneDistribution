/*
-----------------------------------------------------------------------------
TRACER Scene Distribution Plugin USD
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin USD is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin USD development.
 
The TRACER Scene Distribution Plugin USD is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
USD is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin USD may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin USD Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin USD by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin USD in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
-----------------------------------------------------------------------------
*/

#ifndef SCENEDISTRIBUTOR_USD_H
#define SCENEDISTRIBUTOR_USD_H

#include <zmq.hpp>
#include "pxr/usd/usd/prim.h"
#include "pxr/usd/usd/primRange.h"
#include "SceneDistributionState.h"

#include <math.h>
#include <algorithm>
#include <fstream>

#define PI 3.14159265

PXR_NAMESPACE_USING_DIRECTIVE
namespace VPET
{
	// zeroMQ server
	static void* server(void* scene);

	class SceneDistributor
	{
	public:
		SceneDistributor(const std::string &pathName);
		~SceneDistributor();

	private:
		void start(const std::string &pathName);
		void buildLocation(UsdPrim *prim);
		void buildNode(NodeGeo *node, UsdPrim *prim);
		void buildNode(NodeCam *node, UsdPrim *prim);
		void buildNode(NodeLight *node, UsdPrim *prim);
		
		SceneDistributorState m_state;

		//! float extension: lens focal length to vertical field of view
		inline float lensToVFov(float lens, float sensorHeight = 24.0f, float focalMultiplier = 1.0f) const 
		{
			float vFov = (2 * atan((sensorHeight / focalMultiplier) / (2 * lens)) * 180 / PI);
			return vFov;
		}

		inline bool LoadMap(const std::string &i_filepath, unsigned char* &o_buffer, int* o_bufferSize) const
		{
			std::ifstream infile;
			infile.open(i_filepath.c_str(), std::ios::binary | std::ios::in);
			if (infile)
			{
				// get length of file:
				infile.seekg(0, infile.end);
				int length = infile.tellg();
				infile.seekg(0, infile.beg);

				char* buffer = new char[length];

				// read data as a block:
				infile.read(buffer, length);
				infile.close();

				o_buffer = (unsigned char*)buffer;
				*o_bufferSize = length;
				return true;
			}

			return false;
		}

		template<typename T>
		inline bool contains(std::vector<T> &v, T &e) const
		{
			if (std::find(v.begin, v.end, e) != v.end())
				return true;
			else
				return false;
		}
		
		// zeroMQ thread
	};
}

#endif  // end SCENEDISTRIBUTOR_USD_H
