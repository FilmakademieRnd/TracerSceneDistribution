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

#include "UpdateSenderThread.h"

// Update sender thread
void UpdateSenderThread::DoWork()
{
	DOL(doLog, Warning, "[VPET2 SEND Thread] zeroMQ update sender thread running");

	// Variables for socket check test
	int type;
	size_t type_size = sizeof(type);

	while (1)
	{
		// Try something using the socket just to be able to stop the thread when the socket is closed by EndPlay
		try {
			socket->getsockopt(ZMQ_TYPE, &type, &type_size);
		}
		catch (const zmq::error_t& e)
		{
			FString errName = FString(zmq_strerror(e.num()));
			DOL(doLog, Error, "[SEND Thread] socket exception: %s", *errName);
			return;
		}

		// Process messages
		int count = 0;
		for (size_t i = 0; i < msgData->size(); i++)
		{
			count++;

			// Send message
			DOL(doLog, Log, "[SEND Thread] Send message length: %d", msgLen->at(i));
			zmq::message_t responseMessage((void*)msgData->at(i), msgLen->at(i), NULL);
			try {
				socket->send(responseMessage);
			}
			catch (const zmq::error_t& e)
			{
				FString errName = FString(zmq_strerror(e.num()));
				DOL(doLog, Error, "[SEND Thread] send exception: %s", *errName);
				return;
			}
		}

		// Clean processed messages
		msgData->erase(msgData->begin(), msgData->begin() + count);
		msgLen->erase(msgLen->begin(), msgLen->begin() + count);

		// Safety halt
		// Keeps the thread from running wild
		Sleep(10);
	}
}