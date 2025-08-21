import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Box,
} from '@mui/material';
import {
  Dashboard,
  EventSeat,
  Analytics,
  People,
  Schedule,
  Settings,
} from '@mui/icons-material';

const DRAWER_WIDTH = 240;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Seat Layout', icon: <EventSeat />, path: '/seat-layout' },
  { text: 'Analytics', icon: <Analytics />, path: '/analytics' },
  { text: 'Users', icon: <People />, path: '/users' },
  { text: 'Sessions', icon: <Schedule />, path: '/sessions' },
  { text: 'Settings', icon: <Settings />, path: '/settings' },
];

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Drawer
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
        },
      }}
      variant="permanent"
      anchor="left"
    >
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EventSeat color="primary" />
          <Typography variant="h6" noWrap component="div" color="primary">
            SudarshanView
          </Typography>
        </Box>
      </Toolbar>
      
      <Divider />
      
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
              }}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Divider />
      
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Typography variant="caption" color="textSecondary" align="center" display="block">
          SudarshanView v1.0
        </Typography>
        <Typography variant="caption" color="textSecondary" align="center" display="block">
          CEP Project 2025
        </Typography>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
