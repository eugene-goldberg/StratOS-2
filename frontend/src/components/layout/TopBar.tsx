import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Badge,
  Tooltip,
  InputBase,
  alpha,
  Popover,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Chip
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Mic as MicIcon,
  Warning as WarningIcon,
  TrendingUp as OpportunityIcon,
  Lightbulb as InsightIcon,
  CheckCircle as CheckIcon,
  CheckCircle
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { useAlertStore } from '../../store/alertStore';
import { AlertType, AlertSeverity, AlertStatus } from '../../types/alerts';
import { format } from 'date-fns';

interface TopBarProps {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.white, 0.15),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.white, 0.25),
  },
  marginRight: theme.spacing(2),
  marginLeft: 0,
  width: '100%',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto',
  },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: 'inherit',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '30ch',
    },
  },
}));

const TopBar: React.FC<TopBarProps> = ({ sidebarOpen, toggleSidebar }) => {
  const navigate = useNavigate();
  const { alerts, stats, loadAlerts, loadStats, markAsViewed } = useAlertStore();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    loadAlerts();
    loadStats();
    // Refresh alerts every minute
    const interval = setInterval(() => {
      loadAlerts();
      loadStats();
    }, 60000);
    return () => clearInterval(interval);
  }, [loadAlerts, loadStats]);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleVoiceListener = () => {
    setIsListening(!isListening);
    // Voice recognition logic would go here
  };

  const handleNotificationClick = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleAlertClick = (alertId: string) => {
    markAsViewed(alertId);
    handleNotificationClose();
    navigate('/dashboard'); // Or navigate to specific alert detail
  };

  const isMenuOpen = Boolean(anchorEl);
  const isNotificationOpen = Boolean(notificationAnchorEl);
  const menuId = 'primary-account-menu';
  const notificationId = 'notification-menu';

  // Get unread alerts
  const unreadAlerts = alerts.filter(a => a.status === AlertStatus.NEW);
  const unreadCount = stats?.unread_count || 0;

  const getAlertIcon = (type: AlertType) => {
    switch (type) {
      case AlertType.RISK:
        return <WarningIcon color="error" />;
      case AlertType.OPPORTUNITY:
        return <OpportunityIcon color="success" />;
      case AlertType.INSIGHT:
        return <InsightIcon color="info" />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL:
        return 'error';
      case AlertSeverity.HIGH:
        return 'warning';
      case AlertSeverity.MEDIUM:
        return 'info';
      default:
        return 'default';
    }
  };

  const renderMenu = (
    <Menu
      anchorEl={anchorEl}
      id={menuId}
      keepMounted
      open={isMenuOpen}
      onClose={handleMenuClose}
    >
      <MenuItem onClick={handleMenuClose}>Profile</MenuItem>
      <MenuItem onClick={handleMenuClose}>Account Settings</MenuItem>
      <MenuItem onClick={handleMenuClose}>Sign Out</MenuItem>
    </Menu>
  );

  return (
    <>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          transition: (theme) =>
            theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleSidebar}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ display: { xs: 'none', sm: 'block' } }}
          >
            StratOS
          </Typography>

          <Search>
            <SearchIconWrapper>
              <SearchIcon />
            </SearchIconWrapper>
            <StyledInputBase
              placeholder="Search…"
              inputProps={{ 'aria-label': 'search' }}
            />
          </Search>

          <Box sx={{ flexGrow: 1 }} />

          <Box sx={{ display: 'flex' }}>
            <Tooltip title={isListening ? "Stop listening" : "Start voice commands"}>
              <IconButton
                size="large"
                color={isListening ? "secondary" : "inherit"}
                onClick={toggleVoiceListener}
              >
                <MicIcon />
              </IconButton>
            </Tooltip>
            <IconButton 
              size="large" 
              color="inherit"
              onClick={handleNotificationClick}
              aria-describedby={notificationId}
            >
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls={menuId}
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
              <AccountCircle />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      {renderMenu}
      
      <Popover
        id={notificationId}
        open={isNotificationOpen}
        anchorEl={notificationAnchorEl}
        onClose={handleNotificationClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ width: 400, maxHeight: 500, overflow: 'auto' }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6">Notifications</Typography>
            {unreadCount > 0 && (
              <Typography variant="caption" color="text.secondary">
                {unreadCount} new alert{unreadCount > 1 ? 's' : ''}
              </Typography>
            )}
          </Box>
          
          {unreadAlerts.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography color="text.secondary">
                No new alerts
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {unreadAlerts.slice(0, 5).map((alert, index) => (
                <React.Fragment key={alert.id}>
                  <ListItem
                    button
                    onClick={() => handleAlertClick(alert.id)}
                    sx={{ py: 2 }}
                  >
                    <ListItemIcon>
                      {getAlertIcon(alert.alert_type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" sx={{ flexGrow: 1 }}>
                            {alert.title}
                          </Typography>
                          <Chip 
                            label={alert.severity} 
                            size="small"
                            color={getSeverityColor(alert.severity) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="caption" component="div">
                            {alert.description.substring(0, 100)}...
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(alert.created_at), 'MMM d, h:mm a')}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                  {index < unreadAlerts.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
          
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Button 
              fullWidth 
              onClick={() => {
                handleNotificationClose();
                navigate('/dashboard');
              }}
            >
              View All Alerts
            </Button>
          </Box>
        </Box>
      </Popover>
    </>
  );
};

export default TopBar;