import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const Analytics = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        📈 Analytics
      </Typography>
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="textSecondary">
          Analytics Dashboard
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          Detailed analytics and reporting features will be implemented here.
          This will include usage patterns, peak hours, and occupancy trends.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Analytics;
