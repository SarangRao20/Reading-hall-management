import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import {
  People,
  EventSeat,
  TrendingUp,
  AccessTime,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import ApiService from '../services/ApiService';

const StatCard = ({ title, value, subtitle, icon, color = 'primary' }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="h6">
            {title}
          </Typography>
          <Typography variant="h4" component="h2" color={color}>
            {value}
          </Typography>
          <Typography color="textSecondary" variant="body2">
            {subtitle}
          </Typography>
        </Box>
        <Box color={`${color}.main`}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const Dashboard = () => {
  const [overview, setOverview] = useState({
    total_seats: 0,
    occupied_seats: 0,
    available_seats: 0,
    occupancy_rate: 0,
    sessions_today: 0,
    avg_duration_minutes: 0
  });
  const [activeSessions, setActiveSessions] = useState([]);
  const [usageData, setUsageData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview();
    fetchActiveSessions();
    fetchUsageData();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      fetchOverview();
      fetchActiveSessions();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchOverview = async () => {
    try {
      const data = await ApiService.getOverview();
      setOverview(data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    }
  };

  const fetchActiveSessions = async () => {
    try {
      const data = await ApiService.getActiveSessions();
      setActiveSessions(data);
    } catch (error) {
      console.error('Error fetching active sessions:', error);
    }
  };

  const fetchUsageData = async () => {
    try {
      const data = await ApiService.getUsageAnalytics(7); // Last 7 days
      const chartData = data.daily_stats.map(stat => ({
        date: format(new Date(stat.date), 'MMM dd'),
        sessions: stat.total_sessions,
        avgDuration: Math.round(stat.avg_duration || 0)
      })).reverse();
      setUsageData(chartData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching usage data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        📊 Dashboard
      </Typography>
      
      {/* Overview Statistics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Seats"
            value={overview.total_seats}
            subtitle="Reading Hall Capacity"
            icon={<EventSeat fontSize="large" />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Occupied"
            value={overview.occupied_seats}
            subtitle={`${overview.occupancy_rate}% occupancy rate`}
            icon={<People fontSize="large" />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Available"
            value={overview.available_seats}
            subtitle="Seats ready for use"
            icon={<EventSeat fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Sessions Today"
            value={overview.sessions_today}
            subtitle={`Avg ${overview.avg_duration_minutes}min duration`}
            icon={<TrendingUp fontSize="large" />}
            color="primary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Usage Trend Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              📈 Daily Usage Trend (Last 7 Days)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={usageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="sessions" 
                  stroke="#1976d2" 
                  strokeWidth={2}
                  name="Sessions"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Occupancy Rate */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: 348 }}>
            <Typography variant="h6" gutterBottom>
              🎯 Current Occupancy
            </Typography>
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="h2" color="primary" gutterBottom>
                {overview.occupancy_rate}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={overview.occupancy_rate}
                sx={{ height: 10, borderRadius: 5, mb: 2 }}
              />
              <Typography variant="body1" color="textSecondary">
                {overview.occupied_seats} of {overview.total_seats} seats occupied
              </Typography>
              
              <Box sx={{ mt: 3 }}>
                <Chip
                  label={`${overview.available_seats} Available`}
                  color="success"
                  variant="outlined"
                  sx={{ mr: 1, mb: 1 }}
                />
                <Chip
                  label={`${overview.occupied_seats} Occupied`}
                  color="error"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Active Sessions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              👥 Active Sessions ({activeSessions.length})
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Student</TableCell>
                    <TableCell>Seat Number</TableCell>
                    <TableCell>Hall</TableCell>
                    <TableCell>Check-in Time</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activeSessions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        No active sessions
                      </TableCell>
                    </TableRow>
                  ) : (
                    activeSessions.map((session) => {
                      const checkInTime = new Date(session.check_in_time);
                      const duration = Math.floor((Date.now() - checkInTime) / (1000 * 60));
                      
                      return (
                        <TableRow key={session.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {session.user_name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {session.student_id}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={session.seat_number} 
                              size="small" 
                              color="primary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{session.hall_name}</TableCell>
                          <TableCell>
                            {format(checkInTime, 'HH:mm')}
                          </TableCell>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              <AccessTime fontSize="small" sx={{ mr: 0.5 }} />
                              {duration}min
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label="Active"
                              color="success"
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
