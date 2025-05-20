import React, { useState } from 'react';
import { Box, Button, Paper, TextField, Typography } from '@mui/material';
import { useAuthStore } from '../store/authStore';
import { useNavigate, Link } from 'react-router-dom';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const registerUser = useAuthStore((state) => state.register);
  const loading = useAuthStore((state) => state.loading);
  const error = useAuthStore((state) => state.error);
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await registerUser(form);
    if (!useAuthStore.getState().error) {
      navigate('/login');
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <Paper sx={{ p: 4, width: 400 }}>
        <Typography variant="h5" gutterBottom>
          Register
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            name="email"
            fullWidth
            margin="normal"
            value={form.email}
            onChange={handleChange}
          />
          <TextField
            label="Password"
            type="password"
            name="password"
            fullWidth
            margin="normal"
            value={form.password}
            onChange={handleChange}
          />
          <TextField
            label="Full Name"
            name="full_name"
            fullWidth
            margin="normal"
            value={form.full_name}
            onChange={handleChange}
          />
          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}
          <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2 }}>
            {loading ? 'Registering...' : 'Register'}
          </Button>
        </form>
        <Button component={Link} to="/login" sx={{ mt: 2 }}>
          Back to Login
        </Button>
      </Paper>
    </Box>
  );
};

export default Register;
