import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

// Layout components
import Layout from './components/layout/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import NorthStar from './pages/NorthStar';
import CEOLog from './pages/CEOLog';
import StrategicCanvas from './pages/StrategicCanvas';
import ObjectiveData from './pages/ObjectiveData';
import Analysis from './pages/Analysis';
import Planning from './pages/Planning';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="north-star" element={<NorthStar />} />
          <Route path="ceo-log" element={<CEOLog />} />
          <Route path="strategic-canvas" element={<StrategicCanvas />} />
          <Route path="objective-data" element={<ObjectiveData />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="planning" element={<Planning />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Box>
  );
};

export default App;