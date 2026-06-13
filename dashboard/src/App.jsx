import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, Legend
} from 'recharts';
import { Activity, ShieldAlert, Zap, Network } from 'lucide-react';

const socket = io('http://localhost:3001');

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState({
    totalPackets: 0,
    forwardedPackets: 0,
    droppedPackets: 0,
    activeFlows: 0,
    currentBandwidth: 0,
    pps: 0
  });
  const [trafficHistory, setTrafficHistory] = useState([]);
  const [apps, setApps] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));
    
    socket.on('telemetry', (data) => {
      setStats(data.stats);
      setApps(data.apps);
      setLogs(data.logs);
      
      setTrafficHistory(prev => {
        const newHistory = [...prev, { time: new Date(data.timestamp).toLocaleTimeString(), pps: data.stats.pps }];
        if (newHistory.length > 20) newHistory.shift();
        return newHistory;
      });
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('telemetry');
    };
  }, []);

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="header">
        <div className="title-section">
          <h1>DPI Engine Telemetry</h1>
          <p>Real-time Encrypted Traffic Analysis & Protection</p>
        </div>
        <div className="status-badge">
          <div className="pulse-dot"></div>
          {isConnected ? 'System Online (Engine Live)' : 'Connecting to Engine...'}
        </div>
      </header>

      {/* Top Stat Cards */}
      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-info">
            <h3>Throughput</h3>
            <div className="value">{stats.currentBandwidth} Mbps</div>
          </div>
          <div className="stat-icon cyan"><Zap size={24} /></div>
        </div>
        
        <div className="card stat-card">
          <div className="stat-info">
            <h3>Packets Processed</h3>
            <div className="value">{stats.totalPackets.toLocaleString()}</div>
          </div>
          <div className="stat-icon purple"><Activity size={24} /></div>
        </div>

        <div className="card stat-card">
          <div className="stat-info">
            <h3>Threats Blocked</h3>
            <div className="value" style={{color: 'var(--accent-red)'}}>{stats.droppedPackets.toLocaleString()}</div>
          </div>
          <div className="stat-icon red"><ShieldAlert size={24} /></div>
        </div>

        <div className="card stat-card">
          <div className="stat-info">
            <h3>Active Flows</h3>
            <div className="value">{stats.activeFlows}</div>
          </div>
          <div className="stat-icon cyan"><Network size={24} /></div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="main-grid">
        {/* Line Chart: Traffic Velocity */}
        <div className="card">
          <div className="chart-header">
            <h2>Live Traffic Velocity (PPS)</h2>
            <Activity size={20} color="var(--accent-cyan)" />
          </div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={trafficHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="time" stroke="var(--text-secondary)" tick={{fontSize: 12}} />
                <YAxis stroke="var(--text-secondary)" tick={{fontSize: 12}} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#06B6D4' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="pps" 
                  name="Packets/Sec"
                  stroke="var(--accent-cyan)" 
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 6, fill: 'var(--accent-cyan)' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart: App Breakdown */}
        <div className="card">
          <div className="chart-header">
            <h2>Traffic by Application</h2>
          </div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={apps} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="var(--text-secondary)" tick={{fontSize: 12}} width={80} />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                />
                <Bar dataKey="packets" radius={[0, 4, 4, 0]}>
                  {apps.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Terminal Logs */}
      <div className="card terminal-card">
        <div className="chart-header">
          <h2>DPI Engine Live Feed</h2>
        </div>
        <div className="terminal-content">
          {logs.map((log, index) => (
            <div key={`${log.id}-${index}`} className={`log-entry ${log.isAlert ? 'alert' : ''}`}>
              <span className="timestamp">{new Date(log.id).toLocaleTimeString()}</span>
              {log.text}
            </div>
          ))}
          {logs.length === 0 && <div className="text-secondary">Waiting for Engine logs...</div>}
        </div>
      </div>

    </div>
  );
}

export default App;
