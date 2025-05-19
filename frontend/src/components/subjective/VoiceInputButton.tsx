import React, { useState, useEffect } from 'react';
import { 
  IconButton, 
  CircularProgress, 
  Tooltip, 
  Box, 
  Popover, 
  Typography, 
  Button,
  Fade,
  Badge
} from '@mui/material';
import { 
  Mic as MicIcon, 
  Stop as StopIcon, 
  Close as CloseIcon,
  MicOff as MicOffIcon
} from '@mui/icons-material';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { useLogStore } from '../../store/logStore';

interface VoiceInputButtonProps {
  userId: string;
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' | 'default';
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  showPopover?: boolean;
  onEntryCreated?: (entryId: string) => void;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  userId,
  size = 'medium',
  color = 'primary',
  tooltipPlacement = 'bottom',
  showPopover = true,
  onEntryCreated
}) => {
  // Local state for recording duration
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  
  // Use the voice input hook
  const { 
    isRecording, 
    isTranscribing, 
    recordingError, 
    startRecording, 
    stopRecording, 
    cancelRecording 
  } = useVoiceInput({ userId });
  
  // Timer for recording duration
  useEffect(() => {
    let interval: number | null = null;
    
    if (isRecording) {
      // Reset duration when starting
      setRecordingDuration(0);
      
      // Set up interval to increment duration
      interval = window.setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      // Clear interval when not recording
      if (interval) {
        clearInterval(interval);
        interval = null;
      }
    }
    
    // Clean up on unmount
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isRecording]);
  
  // Format the recording duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Handle button click
  const handleClick = async (event: React.MouseEvent<HTMLButtonElement>) => {
    // If already recording, stop
    if (isRecording) {
      try {
        const entry = await stopRecording();
        if (entry && onEntryCreated) {
          onEntryCreated(entry.id);
        }
      } catch (error) {
        console.error('Error stopping recording:', error);
      }
      return;
    }
    
    // If not recording, check permission and start
    try {
      // Request permission if needed
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop the tracks once we have permission
      stream.getTracks().forEach(track => track.stop());
      
      // Reset permission state
      setPermissionDenied(false);
      
      // Start recording
      await startRecording();
      
      // Show popover if enabled
      if (showPopover) {
        setAnchorEl(event.currentTarget);
      }
    } catch (error) {
      console.error('Error starting recording:', error);
      setPermissionDenied(true);
    }
  };
  
  // Handle popover close
  const handlePopoverClose = () => {
    setAnchorEl(null);
  };
  
  // Handle cancel
  const handleCancel = () => {
    cancelRecording();
    handlePopoverClose();
  };
  
  // Determine button color and state
  const buttonColor = isRecording ? 'error' : (isTranscribing ? 'secondary' : color);
  const buttonIcon = isRecording ? <StopIcon /> : (isTranscribing ? <CircularProgress size={24} /> : <MicIcon />);
  const tooltipTitle = isRecording ? 'Stop recording' : (isTranscribing ? 'Transcribing...' : 'Record voice note');
  
  const popoverOpen = Boolean(anchorEl) && (isRecording || isTranscribing);
  
  return (
    <>
      <Tooltip title={permissionDenied ? 'Microphone access denied' : tooltipTitle} placement={tooltipPlacement}>
        <span>
          <IconButton
            color={buttonColor}
            onClick={handleClick}
            disabled={isTranscribing || permissionDenied}
            size={size}
            aria-label={tooltipTitle}
          >
            {permissionDenied ? <MicOffIcon /> : buttonIcon}
          </IconButton>
        </span>
      </Tooltip>
      
      {/* Recording Popover */}
      {showPopover && (
        <Popover
          open={popoverOpen}
          anchorEl={anchorEl}
          onClose={handlePopoverClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'center',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'center',
          }}
          sx={{ mt: 1 }}
        >
          <Box sx={{ p: 2, width: 300, maxWidth: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1">
                {isRecording ? 'Recording Voice Note' : 'Transcribing...'}
              </Typography>
              {isRecording && (
                <Badge
                  color="error"
                  variant="dot"
                  overlap="circular"
                  sx={{ 
                    '& .MuiBadge-badge': {
                      animation: 'pulse 1.5s infinite'
                    },
                    '@keyframes pulse': {
                      '0%': { transform: 'scale(1)' },
                      '50%': { transform: 'scale(1.2)' },
                      '100%': { transform: 'scale(1)' }
                    }
                  }}
                >
                  <Box component="span" />
                </Badge>
              )}
            </Box>
            
            {isRecording && (
              <Fade in={isRecording}>
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" fontFamily="monospace">
                    {formatDuration(recordingDuration)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Speak clearly. Tap stop when finished.
                  </Typography>
                </Box>
              </Fade>
            )}
            
            {isTranscribing && (
              <Fade in={isTranscribing}>
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={40} />
                </Box>
              </Fade>
            )}
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Button 
                variant="outlined" 
                color="error" 
                startIcon={<CloseIcon />}
                onClick={handleCancel}
              >
                Cancel
              </Button>
              
              {isRecording && (
                <Button 
                  variant="contained" 
                  color="primary" 
                  startIcon={<StopIcon />}
                  onClick={async () => {
                    const entry = await stopRecording();
                    if (entry && onEntryCreated) {
                      onEntryCreated(entry.id);
                    }
                  }}
                >
                  Stop
                </Button>
              )}
            </Box>
          </Box>
        </Popover>
      )}
    </>
  );
};

export default VoiceInputButton;