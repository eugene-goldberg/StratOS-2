import React from 'react';
import { Card, CardContent, Typography, Box, IconButton, Chip } from '@mui/material';
import { Close } from '@mui/icons-material';
import { AIAnalysisResult } from '../types';

interface AIAssistPanelProps {
  result: AIAnalysisResult;
  onClose: () => void;
}

const AIAssistPanel: React.FC<AIAssistPanelProps> = ({ result, onClose }) => {
  return (
    <Card 
      elevation={3}
      sx={{ 
        width: 300, 
        maxHeight: '80vh',
        overflow: 'auto',
        bgcolor: 'background.paper',
        borderLeft: '4px solid #0060FF',
      }}
    >
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          p: 1,
          bgcolor: 'primary.light',
          color: 'primary.contrastText'
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">
          AI Analysis Results
        </Typography>
        <IconButton size="small" onClick={onClose} color="inherit">
          <Close fontSize="small" />
        </IconButton>
      </Box>
      
      <CardContent>
        {/* Themes Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Identified Themes
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {result.themes.map((theme, index) => (
              <Chip 
                key={index} 
                label={theme} 
                color="primary" 
                variant="outlined" 
                size="small"
              />
            ))}
          </Box>
        </Box>
        
        {/* Summary Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Summary
          </Typography>
          <Typography variant="body2">
            {result.summary}
          </Typography>
        </Box>
        
        {/* Connections Section */}
        {result.suggestedConnections && result.suggestedConnections.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Suggested Connections
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mb: 1 }}>
              Dotted blue lines have been added to your canvas
            </Typography>
            {result.suggestedConnections.map((connection, index) => (
              <Box 
                key={index} 
                sx={{ 
                  p: 1, 
                  mb: 1, 
                  bgcolor: 'background.default',
                  borderRadius: 1,
                  border: '1px dashed #0060FF'
                }}
              >
                <Typography variant="body2">
                  {connection.label || 'Related concepts'}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AIAssistPanel;
