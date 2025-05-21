import React from 'react';
import { Box } from '@mui/material';
import StrategicCanvas from '../components/canvas/StrategicCanvas';

const StrategicCanvasPage: React.FC = () => {
  return (
    <Box sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      <StrategicCanvas />
    </Box>
  );
};

export default StrategicCanvasPage;