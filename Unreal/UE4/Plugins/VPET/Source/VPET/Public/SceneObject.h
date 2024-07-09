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

//#include "ARTypes.h"
#include "ParameterObject.h"
#include "SceneObject.generated.h"


class AVPETModule;



UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class VPET_API USceneObject : public UParameterObject
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	USceneObject();

	// Is the sceneObject locked?
	bool _lock = false;

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	// This never gets called from the component
	//virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	// These were used for debugging - gets called after Editor interactions with the object
	//virtual void OnRegister() override;
	//virtual void OnUnregister() override;

	//AVPETModule* manager;
	

	int cID;

	Parameter<FVector>* Position_Vpet_Param;
	Parameter<FQuat>* Rotation_Vpet_Param;
	Parameter<FVector>* Scale_Vpet_Param;


	// Access to send queue
	std::vector<char*>* msgData;
	std::vector<int>* msgLen;

	

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	
	
	AActor* thisActor;

	TArray<AbstractParameter*> modifiedParameterList;


	TArray<AbstractParameter*> GetModifiedParameterList()
	{
		return modifiedParameterList;
	}

	void PrintFunction()
	{
		UE_LOG(LogTemp, Error, TEXT("PRINTINGINGING"));
	}

	void SetcID(int kID)
	{
		cID = kID;
	}

	void SetID(int kID)
	{
		ID = kID;
	}

	int GetID()
	{
		return ID;
	}

	void SetSenderQueue(std::vector<char*>* pData, std::vector<int>* pLen)
	{
		msgData = pData;
		msgLen = pLen;
	}
	
};
