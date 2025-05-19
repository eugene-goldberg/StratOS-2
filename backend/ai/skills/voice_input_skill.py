import os
import logging
import tempfile
import json
import asyncio
from typing import Optional, BinaryIO, Dict, Any
import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import AudioStreamFormat

class VoiceInputSkill:
    """Semantic Kernel skill for processing voice input using Azure Speech Services."""
    
    def __init__(self):
        self.logger = logging.getLogger("voice_input_skill")
        self.setup_speech_service()
    
    def setup_speech_service(self):
        """Initialize Azure Speech Service"""
        try:
            # Get connection info from environment variables
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            speech_region = os.getenv("AZURE_SPEECH_REGION")
            
            if not speech_key or not speech_region:
                self.logger.error("Azure Speech Service credentials not found in environment variables")
                raise ValueError("Azure Speech Service credentials not found in environment variables")
            
            # Configure speech service
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, 
                region=speech_region
            )
            self.speech_config.speech_recognition_language = "en-US"
            
            self.logger.info("Azure Speech Service configured successfully")
        except Exception as e:
            self.logger.error(f"Error setting up Azure Speech Service: {str(e)}")
            raise
    
    @sk_function(
        description="Process audio file to text using Azure Speech Services",
        name="process_audio_file"
    )
    async def process_audio_file(self, audio_data: str, context: sk.SKContext) -> str:
        """
        Process audio data (Base64 encoded) to text using Azure Speech Services.
        
        Args:
            audio_data: Base64 encoded audio data
            context: SKContext with optional parameters
                - audio_format: Format of the audio (e.g., "wav", "mp3", "ogg")
                
        Returns:
            Transcribed text
        """
        try:
            import base64
            
            # Get audio format from context
            audio_format = context.variables.get("audio_format", "wav")
            
            # Decode Base64 audio data
            decoded_audio = base64.b64decode(audio_data)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
                temp_file.write(decoded_audio)
                temp_filename = temp_file.name
            
            # Configure audio input
            audio_config = speechsdk.audio.AudioConfig(filename=temp_filename)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Start recognition (create a future)
            done = asyncio.Event()
            recognized_text = ""
            
            def recognized_cb(evt):
                nonlocal recognized_text
                recognized_text = evt.result.text
                done.set()
            
            def canceled_cb(evt):
                self.logger.warning(f"Speech recognition canceled: {evt.result.reason}")
                done.set()
                
            speech_recognizer.recognized.connect(recognized_cb)
            speech_recognizer.canceled.connect(canceled_cb)
            
            # Start continuous recognition
            speech_recognizer.start_continuous_recognition()
            
            # Wait for recognition to complete with timeout
            try:
                await asyncio.wait_for(done.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                self.logger.warning("Speech recognition timed out")
            
            # Stop recognition
            speech_recognizer.stop_continuous_recognition()
            
            # Delete temporary file
            os.unlink(temp_filename)
            
            return recognized_text
        except Exception as e:
            self.logger.error(f"Error processing audio file: {str(e)}")
            return ""
    
    @sk_function(
        description="Process streaming audio chunks to text",
        name="process_streaming_audio"
    )
    async def process_streaming_audio(self, context: sk.SKContext) -> str:
        """
        Process streaming audio chunks to text.
        
        This function expects a series of audio chunks to be provided via the AudioDataStream
        that this function sets up and returns. The actual audio processing happens
        asynchronously as chunks are added to the stream.
        
        Args:
            context: SKContext with parameters:
                - sample_rate: Sample rate of the audio (default: 16000)
                - bits_per_sample: Bits per sample (default: 16)
                - channels: Number of channels (default: 1)
                
        Returns:
            JSON string with status and stream ID for subsequent chunk processing
        """
        try:
            # Get parameters from context
            sample_rate = int(context.variables.get("sample_rate", "16000"))
            bits_per_sample = int(context.variables.get("bits_per_sample", "16"))
            channels = int(context.variables.get("channels", "1"))
            
            # Create a unique ID for this streaming session
            import uuid
            stream_id = str(uuid.uuid4())
            
            # Create a push stream with the specified format
            format = AudioStreamFormat(
                samples_per_second=sample_rate,
                bits_per_sample=bits_per_sample,
                channels=channels
            )
            
            push_stream = speechsdk.audio.PushAudioInputStream(format)
            
            # Store the stream for later use
            if not hasattr(self, 'active_streams'):
                self.active_streams = {}
                
            self.active_streams[stream_id] = {
                'stream': push_stream,
                'text': "",
                'status': "initialized",
                'done': asyncio.Event()
            }
            
            # Configure audio input with the push stream
            audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Set up callbacks
            def recognized_cb(evt):
                stream_data = self.active_streams.get(stream_id)
                if stream_data:
                    stream_data['text'] += evt.result.text + " "
            
            def session_stopped_cb(evt):
                stream_data = self.active_streams.get(stream_id)
                if stream_data:
                    stream_data['status'] = "completed"
                    stream_data['done'].set()
            
            def canceled_cb(evt):
                stream_data = self.active_streams.get(stream_id)
                if stream_data:
                    stream_data['status'] = "canceled"
                    stream_data['done'].set()
            
            # Connect callbacks
            speech_recognizer.recognized.connect(recognized_cb)
            speech_recognizer.session_stopped.connect(session_stopped_cb)
            speech_recognizer.canceled.connect(canceled_cb)
            
            # Start continuous recognition
            speech_recognizer.start_continuous_recognition()
            
            # Store recognizer for later use
            self.active_streams[stream_id]['recognizer'] = speech_recognizer
            
            # Return the stream ID
            return json.dumps({
                'stream_id': stream_id,
                'status': 'initialized'
            })
        except Exception as e:
            self.logger.error(f"Error setting up streaming audio: {str(e)}")
            return json.dumps({
                'error': str(e),
                'status': 'failed'
            })
    
    @sk_function(
        description="Process a chunk of audio data for an existing stream",
        name="process_audio_chunk"
    )
    async def process_audio_chunk(self, audio_chunk: str, context: sk.SKContext) -> str:
        """
        Process a chunk of audio data for an existing stream.
        
        Args:
            audio_chunk: Base64 encoded audio chunk
            context: SKContext with parameters:
                - stream_id: ID of the stream to write to
                - is_final: Whether this is the final chunk (default: false)
                
        Returns:
            JSON string with current status
        """
        try:
            import base64
            
            # Get parameters from context
            stream_id = context.variables.get("stream_id")
            is_final = context.variables.get("is_final", "false").lower() == "true"
            
            if not stream_id:
                return json.dumps({
                    'error': "Missing stream_id parameter",
                    'status': 'failed'
                })
            
            # Check if stream exists
            if not hasattr(self, 'active_streams') or stream_id not in self.active_streams:
                return json.dumps({
                    'error': f"Stream {stream_id} not found",
                    'status': 'failed'
                })
            
            stream_data = self.active_streams[stream_id]
            push_stream = stream_data['stream']
            
            # Decode Base64 audio chunk
            decoded_chunk = base64.b64decode(audio_chunk)
            
            # Write to the stream
            push_stream.write(decoded_chunk)
            
            # If this is the final chunk, close the stream
            if is_final:
                push_stream.close()
                
                # Wait for recognition to complete (with timeout)
                try:
                    await asyncio.wait_for(stream_data['done'].wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    self.logger.warning(f"Recognition timeout for stream {stream_id}")
                    stream_data['status'] = "timeout"
                
                # Stop recognition
                recognizer = stream_data.get('recognizer')
                if recognizer:
                    recognizer.stop_continuous_recognition()
                
                # Return the final result
                result = {
                    'status': stream_data['status'],
                    'text': stream_data['text'].strip()
                }
                
                # Clean up
                self.active_streams.pop(stream_id, None)
                
                return json.dumps(result)
            else:
                # Return intermediate status
                return json.dumps({
                    'status': 'processing',
                    'stream_id': stream_id
                })
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {str(e)}")
            return json.dumps({
                'error': str(e),
                'status': 'failed'
            })
    
    @sk_function(
        description="Cancel an active streaming session",
        name="cancel_streaming"
    )
    async def cancel_streaming(self, stream_id: str) -> str:
        """
        Cancel an active streaming session.
        
        Args:
            stream_id: ID of the stream to cancel
            
        Returns:
            JSON string with status
        """
        try:
            if not hasattr(self, 'active_streams') or stream_id not in self.active_streams:
                return json.dumps({
                    'error': f"Stream {stream_id} not found",
                    'status': 'failed'
                })
            
            stream_data = self.active_streams[stream_id]
            
            # Stop recognition
            recognizer = stream_data.get('recognizer')
            if recognizer:
                recognizer.stop_continuous_recognition()
            
            # Close stream
            push_stream = stream_data.get('stream')
            if push_stream:
                push_stream.close()
            
            # Clean up
            self.active_streams.pop(stream_id, None)
            
            return json.dumps({
                'status': 'canceled',
                'stream_id': stream_id
            })
        except Exception as e:
            self.logger.error(f"Error canceling streaming: {str(e)}")
            return json.dumps({
                'error': str(e),
                'status': 'failed'
            })