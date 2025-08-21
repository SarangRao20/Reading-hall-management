import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import ApiService from '../services/ApiService';

const SeatBox = ({ seat, onSeatClick }) => {
  const getSeatColor = () => {
    if (!seat.is_available) return '#9e9e9e'; // Disabled
    if (seat.is_occupied) return '#f44336'; // Occupied - Red
    return '#4caf50'; // Available - Green
  };

  return (
    <Box
      onClick={() => onSeatClick(seat)}
      sx={{
        width: 40,
        height: 40,
        backgroundColor: getSeatColor(),
        border: '2px solid #fff',
        borderRadius: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        color: 'white',
        fontSize: '10px',
        fontWeight: 'bold',
        '&:hover': {
          opacity: 0.8,
          transform: 'scale(1.1)',
        },
        transition: 'all 0.2s',
      }}
      title={`${seat.seat_number} - ${seat.is_occupied ? 'Occupied' : 'Available'}`}
    >
      {seat.seat_number.replace(/[^0-9]/g, '')}
    </Box>
  );
};

const SeatLayout = () => {
  const [halls, setHalls] = useState([]);
  const [selectedHallId, setSelectedHallId] = useState(1);
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeat, setSelectedSeat] = useState(null);

  useEffect(() => {
    fetchHalls();
  }, []);

  useEffect(() => {
    if (selectedHallId) {
      fetchSeats();
    }
  }, [selectedHallId]);

  const fetchHalls = async () => {
    try {
      const data = await ApiService.getHalls();
      setHalls(data);
      if (data.length > 0 && !selectedHallId) {
        setSelectedHallId(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching halls:', error);
    }
  };

  const fetchSeats = async () => {
    setLoading(true);
    try {
      const data = await ApiService.getHallSeats(selectedHallId);
      setSeats(data);
    } catch (error) {
      console.error('Error fetching seats:', error);
    }
    setLoading(false);
  };

  const handleSeatClick = (seat) => {
    setSelectedSeat(seat);
    console.log('Selected seat:', seat);
  };

  const handleRefresh = () => {
    fetchSeats();
  };

  // Organize seats in a grid layout (5 rows x 10 columns)
  const renderSeatGrid = () => {
    const seatGrid = [];
    const seatsPerRow = 10;
    const rows = 5;

    for (let row = 0; row < rows; row++) {
      const rowSeats = [];
      for (let col = 0; col < seatsPerRow; col++) {
        const seatNumber = `R${row + 1}S${col + 1}`;
        const seat = seats.find(s => s.seat_number === seatNumber);
        
        if (seat) {
          rowSeats.push(
            <SeatBox
              key={seat.id}
              seat={seat}
              onSeatClick={handleSeatClick}
            />
          );
        } else {
          // Empty placeholder
          rowSeats.push(
            <Box key={`empty-${row}-${col}`} sx={{ width: 40, height: 40 }} />
          );
        }
      }
      
      seatGrid.push(
        <Box key={row} sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
          {rowSeats}
        </Box>
      );
    }

    return seatGrid;
  };

  const occupiedSeats = seats.filter(s => s.is_occupied).length;
  const availableSeats = seats.filter(s => s.is_available && !s.is_occupied).length;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          🪑 Seat Layout
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Reading Hall</InputLabel>
            <Select
              value={selectedHallId}
              label="Reading Hall"
              onChange={(e) => setSelectedHallId(e.target.value)}
            >
              {halls.map((hall) => (
                <MenuItem key={hall.id} value={hall.id}>
                  {hall.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              {seats.length}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Total Seats
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="success.main">
              {availableSeats}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Available
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="error.main">
              {occupiedSeats}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Occupied
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Legend */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Chip
          label="Available"
          sx={{ backgroundColor: '#4caf50', color: 'white' }}
          size="small"
        />
        <Chip
          label="Occupied"
          sx={{ backgroundColor: '#f44336', color: 'white' }}
          size="small"
        />
        <Chip
          label="Disabled"
          sx={{ backgroundColor: '#9e9e9e', color: 'white' }}
          size="small"
        />
      </Box>

      {/* Seat Grid */}
      <Paper sx={{ p: 3, backgroundColor: '#f5f5f5' }}>
        <Typography variant="h6" align="center" sx={{ mb: 2 }}>
          📺 Projection Screen
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
          {renderSeatGrid()}
        </Box>

        <Typography variant="body2" align="center" color="textSecondary">
          🚪 Main Entrance
        </Typography>
      </Paper>

      {/* Selected Seat Info */}
      {selectedSeat && (
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Selected Seat: {selectedSeat.seat_number}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2">
                <strong>Status:</strong> {selectedSeat.is_occupied ? 'Occupied' : 'Available'}
              </Typography>
              {selectedSeat.current_user_name && (
                <Typography variant="body2">
                  <strong>Current User:</strong> {selectedSeat.current_user_name}
                </Typography>
              )}
              {selectedSeat.check_in_time && (
                <Typography variant="body2">
                  <strong>Check-in Time:</strong> {new Date(selectedSeat.check_in_time).toLocaleString()}
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2">
                <strong>Position:</strong> Row {Math.ceil(selectedSeat.seat_number.match(/\d+/)[0] / 10)}, 
                Column {selectedSeat.seat_number.match(/\d+/)[0] % 10 || 10}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default SeatLayout;
