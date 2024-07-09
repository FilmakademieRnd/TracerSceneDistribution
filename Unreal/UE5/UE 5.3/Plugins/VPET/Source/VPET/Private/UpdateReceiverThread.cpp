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
#include "UpdateReceiverThread.h"


// Update receiver thread
void UpdateReceiverThread::DoWork()
{
	DOL(doLog, Warning, "[VPET2 RECV Thread] zeroMQ update receiver thread running");

	zmq::message_t message;
	std::string msgString;
	uint8_t* byteStream;
	std::vector<uint8_t> byteVector;

	std::vector<std::string> stringVect;

	while (1)
	{
		char* responseMessageContent = NULL;
		char* messageStart = NULL;
		int responseLength = 0;

		// Blocking receive
		try {
			socket->recv(&message);
		}
		catch (const zmq::error_t& e)
		{
			FString errName = FString(zmq_strerror(e.num()));
			DOL(doLog, Error, "[RECV Thread] recv exception: %s", *errName);
			return;
		}

		const char* msgPointer = static_cast<const char*>(message.data());
		if (msgPointer == NULL) {
			DOL(doLog, Error, "[RECV Thread] Error msgPointer is NULL");
		}
		else
		{
			// Shifting into std::vector
			byteVector.clear();
			byteStream = static_cast<uint8_t*>(message.data()), message.size();
			for (size_t i = 0; i < message.size(); i++)
			{
				byteVector.push_back(byteStream[i]);
			}

			// Process message 
			// Byte zero -> cID
			// Ignore message from host
			if (byteVector[0] != cID)
			{
				// Byte 1 -> time
				// Byte 2 -> Parameter update
				switch ((MessageType)byteVector[2])
				{
				case MessageType::LOCK:
				{
					//decodeLockMessage(ref input);
					UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Lock message"));
					int16_t objectID = *reinterpret_cast<int16_t*>(&byteVector[4]);
					bool lockState = *reinterpret_cast<bool*>(&byteVector[6]);
					manager->DecodeLockMessage(&objectID, &lockState);
					break;
				}
				case MessageType::SYNC:
					//if (!core.isServer)
					//	decodeSyncMessage(ref input);
					UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Sync message"));
					break;
				case MessageType::UNDOREDOADD:
					//decodeUndoRedoMessage(ref input);
					UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Undo/Redo message"));
					break;
				case MessageType::RESETOBJECT:
					//decodeResetMessage(ref input);
					UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Reset message"));
					break;
				case MessageType::PARAMETERUPDATE:
					// input[1] is time
					//m_messageBuffer[input[1]].Add(input);
					UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Parameter updated message"));
					msgQ->push_back(byteVector);
					break;
				default:
					break;
				}
			}
			else
			{
				UE_LOG(LogTemp, Log, TEXT("[VPET2 Parse] Message came from host, cID: %d"), cID);
			}
		}
	}
}
