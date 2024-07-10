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

#include "SceneDistributor.h"
#include <iostream>
#include <fstream>


bool file_exist(const char *fileName)
{
	std::ifstream infile(fileName);
	return infile.good();
}

int main(int argc, char *argv[], char *envp[])
{
	if ((argc <= 1))
		std::cout << "No valid filepath. Please entnter a path and a filename e.g. c:\\USD\\kitchen.usda" << std::endl;
	else if (!file_exist(argv[1]))
		std::cout << "File not found." << std::endl;
	else
		VPET::SceneDistributor distributor((argv[1]));

}

