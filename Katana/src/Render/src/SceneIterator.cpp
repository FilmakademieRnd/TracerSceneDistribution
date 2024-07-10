/*
-----------------------------------------------------------------------------
TRACER Scene Distribution Plugin Katana
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Katana is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Katana development.
 
The TRACER Scene Distribution Plugin Katana is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Katana is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Katana may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Katana Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Katana by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Katana in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
-----------------------------------------------------------------------------
*/
#include "SceneIterator.h"

#include <FnRenderOutputUtils/FnRenderOutputUtils.h>
#include <FnGeolibServices/FnXFormUtil.h>


#include <string>
#include <vector>

#include <glm/vec3.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/matrix_inverse.hpp>
#include <glm/gtx/matrix_decompose.hpp>
#include <glm/gtx/string_cast.hpp>


namespace Dreamspace
{
	namespace Katana
	{
		namespace SceneIterator
		{

			void buildLocation(FnKat::FnScenegraphIterator sgIterator, SceneDistributorPluginState* sharedState)
			{

				// Check Tag and return if not equal
				if(sharedState->lodMode == TAG)
				{
					FnAttribute::StringAttribute lodTagAttr = sgIterator.getAttribute("info.componentLodTag");
					if(lodTagAttr.isValid())
					{
						if(sharedState->lodTag != lodTagAttr.getValue("unknown", false))
						{
							return;
						}
					}
				}

				std::cout << "Build: " <<  sgIterator.getFullName() << std::endl;

				// Get scenegraph location type
				std::string type = sgIterator.getType();

				// Get transform at this location
				glm::mat4 transform = glm::mat4(1.0f);

				/*
				std::vector<FnKat::RenderOutputUtils::Transform> xFormList;
				FnKat::RenderOutputUtils::fillXFormListForLocation(xFormList, sgIterator);

				glm::mat4 singleScale = glm::mat4(1.0);
				glm::mat4 singleRotate = glm::mat4(1.0);
				glm::mat4 singleTranslate = glm::mat4(1.0);
				glm::mat4 singleMatrix = glm::mat4(1.0);
				*/

				FnAttribute::GroupAttribute xformAttr = sgIterator.getAttribute("xform");

				if(xformAttr.isValid())
				{
					FnAttribute::DoubleAttribute matrixAttr = FnGeolibServices::FnXFormUtil::CalcTransformMatrixAtTime(xformAttr, 0.0f).first;
					FnAttribute::DoubleConstVector matrixData = matrixAttr.getNearestSample(0.0);
					//      transform = glm::mat4(matrixData[ 0], matrixData[ 1], matrixData[ 2], matrixData[ 3],
					//                       matrixData[ 4], matrixData[ 5], matrixData[ 6], matrixData[ 7],
					//                       matrixData[ 8], matrixData[ 9], matrixData[10], matrixData[11],
					//                       matrixData[12], matrixData[13], matrixData[14], matrixData[15]);

					// TODO: Hardcoded handiness
					if(sharedState->nodeTypeList[sharedState->nodeTypeList.size()-1] == Dreamspace::Katana::NodeType::CAMERA || sharedState->nodeTypeList[sharedState->nodeTypeList.size()-1] == Dreamspace::Katana::NodeType::LIGHT)
					{

						transform = glm::mat4(matrixData[0], -matrixData[4], -matrixData[8], matrixData[3],
							-matrixData[1], matrixData[5], matrixData[9], matrixData[7],
							-matrixData[2], matrixData[6], matrixData[10], matrixData[11],
							-matrixData[12], matrixData[13], matrixData[14], matrixData[15]);
					}
					else
					{
						transform = glm::mat4(matrixData[0], -matrixData[4], -matrixData[8], matrixData[3],
							-matrixData[1], matrixData[5], matrixData[9], matrixData[7],
							-matrixData[2], matrixData[6], matrixData[10], matrixData[11],
							-matrixData[12], matrixData[13], matrixData[14], matrixData[15]);

					}

				}

				// Build scene graps >>
				sharedState->node = NULL;

				bool pluginFound = FnKat::RenderOutputUtils::processLocation(sgIterator, "sceneDistributor", type, sharedState, NULL);

				if(!pluginFound)
				{
					std::cout << "NO processLocation for " << sgIterator.getType() << std::endl;
					sharedState->node = new Node();
					sharedState->nodeTypeList.push_back(NodeType::GROUP);
				}

				// node name
				std::string name_str = sgIterator.getName();
				name_str = name_str.substr(0, 63);
				strcpy(sharedState->node->name, name_str.c_str());

				sharedState->node->childCount = 0;

				for(FnKat::FnScenegraphIterator child = sgIterator.getFirstChild(); child.isValid(); child = child.getNextSibling())
				{
					if(sharedState->lodMode == TAG)
					{
						FnAttribute::StringAttribute lodTagAttr = child.getAttribute("info.componentLodTag");
						if(lodTagAttr.isValid())
						{
							if(sharedState->lodTag == lodTagAttr.getValue("unknown", false))
							{
								sharedState->node->childCount++;
							}
						}
						else
						{
							sharedState->node->childCount++;
						}
					}
					else
					{
						sharedState->node->childCount++;
					}

				}

				glm::vec3 skew, position, scale;
				glm::vec4 persp;
				glm::quat _rotation;
				glm::quat rotation;

				glm::decompose(transform, scale, _rotation, position, skew, persp);
				
				if(sharedState->nodeTypeList[sharedState->nodeTypeList.size()-1] == Dreamspace::Katana::NodeType::CAMERA ||
					sharedState->nodeTypeList[sharedState->nodeTypeList.size() - 1] == Dreamspace::Katana::NodeType::LIGHT)
				{
					rotation = glm::rotate(glm::conjugate(_rotation), glm::pi<float>(), glm::vec3(0, 1, 0));
					//rotation = _rotation;
				}
				else
				{
						rotation = glm::conjugate(_rotation);
				}

				//std::cout << "pos: " << position[0] << " " << position[1] << " " << position[2] << std::endl;
				//std::cout << "rot: " << rotation[0] << " " << rotation[1] << " " << rotation[2] << " " << rotation[3] << std::endl;

				// TODO: Hardcoded handiness
				sharedState->node->position[0] = position[0];
				sharedState->node->position[1] = position[1];
				sharedState->node->position[2] = position[2];

				sharedState->node->rotation[0] = rotation[0];
				sharedState->node->rotation[1] = rotation[1];
				sharedState->node->rotation[2] = rotation[2];
				sharedState->node->rotation[3] = rotation[3];

				sharedState->node->scale[0] = scale[0];
				sharedState->node->scale[1] = scale[1];
				sharedState->node->scale[2] = scale[2];

				sharedState->node->editable=false;

				FnAttribute::IntAttribute editAttr = sgIterator.getAttribute("dreamspace.editable");
				if(editAttr.isValid())
				{
					if(1 == editAttr.getValue(0, false))
					{
						sharedState->node->editable=true;
					}
				}

				std::cout << "[INFO SceneDistributor.SceneIterator] Add Node: " << sharedState->node->name << std::endl;
				sharedState->nodeList.push_back(sharedState->node);

				// Recurse to children
				for(FnKat::FnScenegraphIterator child = sgIterator.getFirstChild(); child.isValid(); child = child.getNextSibling())
				{
					buildLocation(child, sharedState);
				}

				// Unstack pre-multiplied model matrix before returning
				//sharedState->modelMatrices.pop();
			}

		}
	}
}
