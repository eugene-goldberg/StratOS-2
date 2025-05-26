# StratOS MVP: F1.2 "CEO's Log" - Implementation Deep Dive

**Date:** May 19, 2025
**Product:** StratOS (Strategy Operating System)
**Feature ID:** F1.2 (MVP)
**Roadmap Theme:** Strategic Foundation & CEO's Compass
**Building on:** `mvp_status.md` (Claude Code's progress) and "CEO's Log - Visual User Flow (Conversational & Mobile Update)".
**Focus:** Service layer implementation, voice-to-text integration, AI skill refinement for basic tagging, and frontend-backend interaction for the CEO's Log.

## I. Overview & MVP Scope Confirmation

The "CEO's Log" is a cornerstone for capturing Subjective (S) data. The MVP aims for:

1.  **Conversational Note Capture (Mobile-First):** CEO uses the StratOS Assistant (voice primarily) to dictate notes.
2.  **Manual Text Note Creation:** As a secondary option on both mobile and desktop.
3.  **Secure Storage & Sync:** Notes are timestamped, stored securely, and synced across devices.
4.  **Basic Viewing & Editing:** CEO can review, edit text, and delete notes.
5.  **Manual Tagging:** CEO can add free-form tags.
6.  **Manual Linking to Strategic Elements:** CEO can link notes to defined WHYs/WHATs (from F1.1 "Our North Star").
7.  **Basic AI-Suggested Tags (MVP target):** AI offers simple tag suggestions based on note content and WHY/WHAT titles.
8.  **Voice-to-Text Integration:** Using Azure AI services.

**Items from `mvp_status.md` to address in this deep dive:**
* Backend: Service implementation for `Subjective Input Router`.
* Backend: Voice-to-text processing endpoint implementation.
* Backend: AI skill prompt engineering for `ExtractTags` (part of `Subjective Skills`).
* Frontend: Connecting to backend APIs for CEO's Log.
* Frontend: Implementing voice interaction functionality (initiating recording, sending audio, receiving transcription).

## II. Refined User Interaction Flows & API Calls

Building on "CEO's Log - Visual User Flow (Conversational & Mobile Update)":

**Flow 2: Creating a New Log Entry via Conversational Interaction (MVP Primary Path)**

1.  **Activate StratOS Assistant & Initiate Note-Taking (Frontend):**
    * CEO activates Assistant (tap/click microphone icon).
    * Frontend UI indicates "listening."
    * CEO speaks: "StratOS, take a strategic note: [CEO dictates]."
    * Frontend captures audio (e.g., using Web Audio API) and begins streaming audio chunks to the backend.

2.  **Backend Audio Processing & Transcription (Backend API & Service):**
    * **API Call (Frontend to Backend):** `POST /api/v1/subjective-input/log-entries/voice-note/stream` (example endpoint)
        * Frontend sends audio chunks via WebSocket or a series of HTTP requests.
        * Session management to handle multiple chunks for one note.
    * **Service Layer (`SubjectiveInputService`):**
        * Receives audio chunks.
        * Invokes `VoiceInputSkill.ProcessAudioChunk` (Semantic Kernel) which forwards audio to Azure Cognitive Services Speech (STT) or Azure OpenAI real-time audio STT.
    * As transcription segments become available from STT, they can be streamed back to the frontend to show live transcription (Phase 2 refinement; MVP might wait for full transcription).
    * Once CEO stops speaking and frontend signals end of stream:
        * `VoiceInputSkill.FinalizeTranscription` is called.
        * The full transcribed text is returned to the `SubjectiveInputService`.
    * **API Response (Backend to Frontend):** Returns the full transcribed text.
        ```json
        {
          "transcribed_text": "The Q3 projections look challenging, especially with the new competitor product launch."
        }
        ```

3.  **Frontend Displays Transcription & CEO Confirms Save:**
    * Frontend Assistant UI displays the `transcribed_text`.
    * StratOS Assistant (simulated by frontend logic for MVP, or basic LLM call for confirmation text): "Okay, I have: '[transcribed_text]'. Save this to your CEO's Log?"
    * CEO confirms (voice "Yes" or tap "Save to Log" button).

4.  **Backend Saves Log Entry & Suggests Tags (Backend API & Service):**
    * **API Call (Frontend to Backend):** `POST /api/v1/subjective-input/log-entries/`
        * Payload:
            ```json
            {
              "content_text": "[final_transcribed_text_after_optional_edit_by_CEO_on_frontend]",
              "title": null, // Optional, can be added later
              "source": "voice_assistant" // or "manual_text"
            }
            ```
    * **Service Layer (`SubjectiveInputService`):**
        * Receives the request.
        * Calls `LogManagementSkill.CreateLogEntry` (Semantic Kernel) to save the basic note (text, timestamp, source) to Azure Cosmos DB. Gets back the new `entry_id`.
        * Calls `BasicAITaggingSkill.SuggestTagsFromText` (Semantic Kernel) with `content_text` and a list of current WHYs/WHATs (retrieved via another service, e.g., `NorthStarService`).
    * **API Response (Backend to Frontend):** Returns the created log entry details and AI-suggested tags.
        ```json
        {
          "entry_id": "xyz789",
          "title": null,
          "content_text": "The Q3 projections look challenging...",
          "created_at": "2025-05-19T10:30:00Z",
          "source": "voice_assistant",
          "tags": [], // Initially empty
          "linked_strategic_elements": [], // Initially empty
          "ai_suggested_tags": ["Q3 Projections", "Competitor Product", "Challenge"]
        }
        ```

5.  **Frontend Updates & CEO Interaction (Post-Save):**
    * Frontend Assistant UI: "Saved to your CEO's Log. AI suggested tags: [Q3 Projections], [Competitor Product], [Challenge]. You can refine this in the Log."
    * The CEO's Log list view (if open) refreshes, showing the new entry.
    * CEO can then navigate to the Log (Flow 3) to edit, add their own tags, accept AI tags, and link to WHYs/WHATs.

**Flow 3: Viewing, Editing, Tagging & Linking (Backend API & Service)**

* **Get Log Entry:** `GET /api/v1/subjective-input/log-entries/{entry_id}`
* **Update Log Entry (Saving Changes):** `PUT /api/v1/subjective-input/log-entries/{entry_id}`
    * Payload includes all editable fields: `title`, `content_text`, `user_tags` (list of strings), `linked_strategic_elements` (list of IDs of WHYs/WHATs).
    * **Service Layer (`SubjectiveInputService`):**
        * Calls `LogManagementSkill.UpdateLogEntry`.
        * If `content_text` changed significantly, it might re-invoke `BasicAITaggingSkill.SuggestTagsFromText` and return updated suggestions.
* **Delete Log Entry:** `DELETE /api/v1/subjective-input/log-entries/{entry_id}`

## III. Backend Service Layer Implementation (`SubjectiveInputService`)

This service, likely in `backend/services/subjective_input_service.py`, will orchestrate interactions between the API router, Semantic Kernel skills, and data models.

```python
# backend/services/subjective_input_service.py
# (Conceptual - Claude Code will implement fully)

from ..models.subjective_input import LogEntryCreate, LogEntryUpdate, LogEntryResponse
from ..models.strategic_foundation import NorthStar # For WHYs/WHATs
from ..ai.kernel_service import KernelService # Assumes a central SK service
# from ..services.north_star_service import NorthStarService # To get WHYs/WHATs

class SubjectiveInputService:
    def __init__(self, kernel_service: KernelService, # north_star_service: NorthStarService
                 db_client # e.g., Cosmos DB client
                ):
        self.kernel = kernel_service
        # self.north_star_service = north_star_service
        self.db = db_client # Placeholder for database interaction logic

    async def process_voice_note_stream(self, audio_chunks_stream) -> str:
        # 1. Initialize VoiceInputSkill session with Azure STT
        #    (Conceptual: SK skill might handle chunking and streaming internally)
        # voice_input_skill = self.kernel.get_skill("VoiceInputSkill")
        # transcription_result = await voice_input_skill.transcribe_stream(audio_chunks_stream)
        
        # Placeholder for direct Azure SDK usage if SK skill isn't handling full stream
        transcribed_text = ""
        # ... logic to stream chunks to Azure Speech SDK and accumulate text ...
        # This part needs robust implementation for streaming, error handling, session management.
        # Example:
        # speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        # audio_config = ... (from stream)
        # speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        # result = speech_recognizer.recognize_once_async().get()
        # transcribed_text = result.text
        # For streaming, use start_continuous_recognition_async() and events.
        
        # This is a simplified mock for now
        temp_transcription = "Simulated transcription of streamed audio. "
        async for chunk in audio_chunks_stream: # Assuming async generator for chunks
            # In reality, you'd append to a buffer and send to STT service
            temp_transcription += f" chunk_len:{len(chunk)} " 
        transcribed_text = temp_transcription.strip()

        if not transcribed_text:
            raise ValueError("Transcription failed or produced empty text.")
        return transcribed_text

    async def create_log_entry_from_voice(self, transcribed_text: str, user_id: str) -> LogEntryResponse:
        # This method is called after frontend confirms the transcription.
        log_entry_data = LogEntryCreate(content_text=transcribed_text, source="voice_assistant")
        
        # Persist basic log entry first
        # new_entry_dict = await self.db.save_log_entry(user_id, log_entry_data.dict()) 
        # This would call LogManagementSkill.CreateLogEntry in a full SK setup
        # For now, direct save simulation:
        new_entry_dict = {**log_entry_data.dict(), "id": "temp_id_123", "user_id": user_id, 
                          "created_at": "2025-05-19T11:00:00Z", "updated_at": "2025-05-19T11:00:00Z",
                          "tags": [], "linked_strategic_elements": []}


        # Get WHYs/WHATs for AI Tagging (simplified for now)
        # whys_whats = await self.north_star_service.get_all_titles(user_id)
        whys_whats_titles = ["Achieve Market Leadership", "Foster Innovation Culture"] # Mock

        # Invoke BasicAITaggingSkill
        # ai_tagging_skill = self.kernel.get_skill("BasicAITaggingSkill")
        # suggested_tags = await ai_tagging_skill.suggest_tags(
        #     text_content=transcribed_text,
        #     existing_whys_whats_list=whys_whats_titles
        # )
        
        # Simulate SK skill call for AI tagging
        llm_prompt_for_tags = self._construct_ai_tagging_prompt(transcribed_text, whys_whats_titles)
        # In reality, this call goes through Semantic Kernel to Azure OpenAI
        # raw_llm_response_tags = await self.kernel.invoke_llm(llm_prompt_for_tags) 
        # suggested_tags = self._parse_llm_tag_response(raw_llm_response_tags)
        suggested_tags = ["SimulatedTag1", "SimulatedTag2"] # Mock

        # Combine results
        response_data = {**new_entry_dict, "ai_suggested_tags": suggested_tags}
        return LogEntryResponse(**response_data)

    async def create_manual_log_entry(self, log_entry_data: LogEntryCreate, user_id: str) -> LogEntryResponse:
        # Similar to above but source is "manual_text" and tags/links might be included
        # new_entry_dict = await self.db.save_log_entry(user_id, log_entry_data.dict(exclude_unset=True))
        new_entry_dict = {**log_entry_data.dict(exclude_unset=True), "id": "temp_id_456", "user_id": user_id,
                          "created_at": "2025-05-19T11:05:00Z", "updated_at": "2025-05-19T11:05:00Z"}

        whys_whats_titles = ["Achieve Market Leadership", "Foster Innovation Culture"] # Mock
        suggested_tags = []
        if log_entry_data.content_text: # Only suggest tags if content exists
            # llm_prompt_for_tags = self._construct_ai_tagging_prompt(log_entry_data.content_text, whys_whats_titles)
            # raw_llm_response_tags = await self.kernel.invoke_llm(llm_prompt_for_tags)
            # suggested_tags = self._parse_llm_tag_response(raw_llm_response_tags)
            suggested_tags = ["ManualEntryTag1"] # Mock
        
        response_data = {**new_entry_dict, "ai_suggested_tags": suggested_tags}
        return LogEntryResponse(**response_data)

    async def update_log_entry_service(self, entry_id: str, log_update_data: LogEntryUpdate, user_id: str) -> LogEntryResponse:
        # updated_entry_dict = await self.db.update_log_entry(entry_id, user_id, log_update_data.dict(exclude_unset=True))
        # If content_text changed, re-run AI tagging if desired
        # ...
        # Mock update
        existing_entry = {"id": entry_id, "user_id": user_id, "content_text": "Old content", 
                          "tags": ["OldTag"], "linked_strategic_elements": [], 
                          "created_at": "2025-05-19T10:00:00Z"}
        updated_entry_dict = {**existing_entry, **log_update_data.dict(exclude_unset=True), 
                              "updated_at": "2025-05-19T11:10:00Z"}
        
        suggested_tags = []
        if log_update_data.content_text and log_update_data.content_text != existing_entry["content_text"]:
             whys_whats_titles = ["Achieve Market Leadership", "Foster Innovation Culture"] # Mock
            #  llm_prompt_for_tags = self._construct_ai_tagging_prompt(log_update_data.content_text, whys_whats_titles)
            #  raw_llm_response_tags = await self.kernel.invoke_llm(llm_prompt_for_tags)
            #  suggested_tags = self._parse_llm_tag_response(raw_llm_response_tags)
             suggested_tags = ["UpdatedContentTag"] # Mock

        response_data = {**updated_entry_dict, "ai_suggested_tags": suggested_tags}
        return LogEntryResponse(**response_data)

    # Helper for constructing prompt for BasicAITaggingSkill
    def _construct_ai_tagging_prompt(self, text_content: str, whys_whats_list: list[str]) -> str:
        # This refers to the LLM Grounding Strategy document
        # (stratos_llm_grounding_strategy_v1.md, Section III.1, III.2, III.3)
        predefined_elements_str = "\n- ".join(whys_whats_list)
        prompt = f"""System:
You are an AI assistant helping a CEO categorize their strategic notes. Your task is to analyze the provided text and suggest a few concise tags (1-3 words each). Focus on extracting key entities (names, companies, projects), core topics, or main sentiments.
Additionally, if the text explicitly mentions or clearly alludes to any of the following predefined strategic elements, include that element as a suggested tag.

Predefined Strategic Elements:
- {predefined_elements_str}

Provide your output as a JSON list of unique suggested string tags. Only output the JSON list.

User Note Text:
"""
{text_content}
"""

Assistant (JSON list of tags):
"""
        return prompt

    # def _parse_llm_tag_response(self, llm_response: str) -> list[str]:
    #     # Safely parse JSON from LLM response
    #     try:
    #         tags = json.loads(llm_response.strip())
    #         if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
    #             return list(set(tags)) # Ensure uniqueness
    #     except json.JSONDecodeError:
    #         pass # Handle error or return empty
    #     return []

    # ... other service methods for Get, List, Delete ...
