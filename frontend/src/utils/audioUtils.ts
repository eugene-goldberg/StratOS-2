/**
 * Utility functions for audio recording and processing
 */

// Check if browser supports the necessary audio APIs
export const isAudioRecordingSupported = (): boolean => {
  return !!(navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia &&
    window.MediaRecorder &&
    window.AudioContext);
};

// Convert audio buffer to WAV format
export const audioBufferToWav = (buffer: AudioBuffer, sampleRate: number = 16000): Blob => {
  // Get channel data
  const numChannels = buffer.numberOfChannels;
  const length = buffer.length * numChannels;
  
  // Create the WAV buffer
  const wavBuffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(wavBuffer);
  
  // Write the WAV header
  // "RIFF" chunk descriptor
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true);
  writeString(view, 8, 'WAVE');
  
  // "fmt " sub-chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true); // byte rate
  view.setUint16(32, numChannels * 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  
  // "data" sub-chunk
  writeString(view, 36, 'data');
  view.setUint32(40, length * 2, true);
  
  // Write the PCM samples
  const offset = 44;
  const channelData = [];
  
  // Extract channel data
  for (let i = 0; i < numChannels; i++) {
    channelData.push(buffer.getChannelData(i));
  }
  
  // Interleave the channel data and convert to 16-bit PCM
  let index = 0;
  for (let i = 0; i < buffer.length; i++) {
    for (let channel = 0; channel < numChannels; channel++) {
      const sample = channelData[channel][i];
      // Convert float sample (-1.0 to 1.0) to 16-bit PCM
      view.setInt16(offset + index * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      index++;
    }
  }
  
  // Create the WAV Blob
  return new Blob([wavBuffer], { type: 'audio/wav' });
};

// Helper function to write a string to a DataView
const writeString = (view: DataView, offset: number, string: string): void => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};

// Convert an audio blob to a base64 string
export const blobToBase64 = async (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === 'string') {
        // Extract the base64 part (remove the data URL prefix)
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      } else {
        reject(new Error('Failed to convert blob to base64'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// Resample audio to a different sample rate
export const resampleAudio = async (
  audioBuffer: AudioBuffer,
  targetSampleRate: number
): Promise<AudioBuffer> => {
  // Create an offline audio context with the target sample rate
  const offlineCtx = new OfflineAudioContext(
    audioBuffer.numberOfChannels,
    audioBuffer.duration * targetSampleRate,
    targetSampleRate
  );
  
  // Create a buffer source
  const source = offlineCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineCtx.destination);
  
  // Start the source and render
  source.start(0);
  return offlineCtx.startRendering();
};

// Process audio data for streaming (convert to correct format)
export const processAudioForStreaming = async (
  audioChunk: Blob,
  targetSampleRate: number = 16000,
  targetBitsPerSample: number = 16,
  targetChannels: number = 1
): Promise<ArrayBuffer> => {
  // Convert blob to array buffer
  const arrayBuffer = await audioChunk.arrayBuffer();
  
  // Create audio context
  const audioContext = new AudioContext();
  
  // Decode the audio data
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  
  // Resample if needed
  const processedBuffer = audioContext.sampleRate !== targetSampleRate
    ? await resampleAudio(audioBuffer, targetSampleRate)
    : audioBuffer;
  
  // Convert to WAV
  const wavBlob = audioBufferToWav(processedBuffer, targetSampleRate);
  
  // Convert to array buffer for direct streaming
  return wavBlob.arrayBuffer();
};

export default {
  isAudioRecordingSupported,
  audioBufferToWav,
  blobToBase64,
  resampleAudio,
  processAudioForStreaming
};