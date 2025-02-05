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

#include <zmq.hpp>
#include "Async/AsyncWork.h"

// Development output log macro
#define DOL(logType, logVerbosity, logString, ...) if(logType) UE_LOG(LogTemp, logVerbosity, TEXT(logString), ##__VA_ARGS__);

// Development on-screen debug message
#define OSD(debugColor, debugString, ...) if(GEngine && VerboseDisplay) GEngine->AddOnScreenDebugMessage(-1, 5.0f, debugColor, FString::Printf(TEXT(debugString), ##__VA_ARGS__));


// Update Sender thread
class UpdateSenderThread : public FNonAbandonableTask
{
	friend class FAutoDeleteAsyncTask<UpdateSenderThread>;
public:
	zmq::socket_t* socket;
	std::vector<std::vector<uint8_t>>* msgQ;
	std::vector<char*>* msgData;
	std::vector<int>* msgLen;
	bool doLog;
	uint8_t cID;

	enum class MessageType
	{
		PARAMETERUPDATE, LOCK, // node
		SYNC, PING, RESENDUPDATE, // sync
		UNDOREDOADD, RESETOBJECT // undo redo
	};

	UpdateSenderThread(zmq::socket_t* pSocket, std::vector<std::vector<uint8_t>>* pQueue, uint8_t m_ID, bool pLog, std::vector<char*>* pData, std::vector<int>* pLen) : socket(pSocket), msgQ(pQueue), cID(m_ID), doLog(pLog), msgData(pData), msgLen(pLen) { }

	void DoWork();

	FORCEINLINE TStatId GetStatId() const
	{
		RETURN_QUICK_DECLARE_CYCLE_STAT(FGenericTask, STATGROUP_TaskGraphTasks);
	}

};