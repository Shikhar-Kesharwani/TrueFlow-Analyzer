const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(express.json());

// Persistent accumulated app counts - never wiped, only grows
let appAccumulator = {};

let state = {
  totalPackets: 0,
  forwardedPackets: 0,
  droppedPackets: 0,
  activeFlows: 0,
  currentBandwidth: 0.0, // Mbps
  appBreakdown: [],
  logs: []
};

// Accept real data from Python Engine
app.post('/telemetry', (req, res) => {
  const data = req.body;
  
  if (data.action === 'log') {
    state.logs.unshift({ id: Date.now(), text: data.message, isAlert: data.isAlert });
    if (state.logs.length > 15) state.logs.pop();
  } else if (data.action === 'stats') {
    state.totalPackets = data.totalPackets;
    state.activeFlows = data.activeFlows;
    state.currentBandwidth = data.bandwidth;
    
    // Smooth Decay Algorithm: Provides a fluid, professional UI experience
    if (data.apps) {
      // 1. Decay existing values by 40% every second (smooth drain)
      for (let key in appAccumulator) {
        appAccumulator[key].packets = Math.floor(appAccumulator[key].packets * 0.6);
        // If it drops below a threshold, remove it to prevent "ghost" apps from lingering
        if (appAccumulator[key].packets < 3) {
          delete appAccumulator[key];
        }
      }

      // 2. Add the new real-time burst data
      data.apps.forEach(app => {
        let baseName = app.name.replace(/\d+$/, '').toLowerCase();
        let displayName = app.name;
        let color = '#6B7280';

        if (baseName.includes('youtube')) { displayName = 'YouTube'; color = '#FF0000'; }
        else if (baseName.includes('netflix')) { displayName = 'Netflix'; color = '#E50914'; }
        else if (baseName.includes('skype')) { displayName = 'Skype'; color = '#00AFF0'; }
        else if (baseName.includes('facebook')) { displayName = 'Facebook'; color = '#1877F2'; }
        else if (baseName.includes('instagram')) { displayName = 'Instagram'; color = '#E1306C'; }
        else if (baseName.includes('whatsapp')) { displayName = 'WhatsApp'; color = '#25D366'; }
        else if (baseName.includes('vimeo')) { displayName = 'Vimeo'; color = '#1AB7EA'; }
        else if (baseName.includes('spotify')) { displayName = 'Spotify'; color = '#1DB954'; }
        else if (baseName.includes('idle')) { displayName = 'Idle/Background'; color = '#9CA3AF'; }
        else if (baseName.includes('hangout')) { displayName = 'Google Hangouts'; color = '#0F9D58'; }
        else if (baseName.includes('scp') || baseName.includes('sftp') || baseName.includes('ftp')) { displayName = 'Secure File Transfer'; color = '#F59E0B'; }
        else if (baseName.includes('email') || baseName.includes('gmail')) { displayName = 'Email Protocol'; color = '#EA4335'; }
        else { displayName = app.name.charAt(0).toUpperCase() + app.name.slice(1); }

        if (!appAccumulator[displayName]) {
          appAccumulator[displayName] = { name: displayName, packets: 0, color: color };
        }
        
        // Boost the incoming count so active streams dominate the chart
        appAccumulator[displayName].packets += (app.count * 10);
      });

      // Build sorted breakdown from the smoothed accumulator
      state.appBreakdown = Object.values(appAccumulator)
        .sort((a, b) => b.packets - a.packets)
        .slice(0, 8); // Show top 8 only
    }
    
    // Broadcast to React
    io.emit('telemetry', {
      timestamp: Date.now(),
      stats: {
        totalPackets: state.totalPackets,
        forwardedPackets: state.totalPackets, // Simplified for Python
        droppedPackets: state.droppedPackets,
        activeFlows: state.activeFlows,
        currentBandwidth: parseFloat(state.currentBandwidth),
        pps: data.pps || 0
      },
      apps: state.appBreakdown,
      logs: state.logs
    });
  }
  
  res.sendStatus(200);
});

io.on('connection', (socket) => {
  console.log('React Dashboard connected');
});

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Real DPI Server API listening on port ${PORT}`);
});
