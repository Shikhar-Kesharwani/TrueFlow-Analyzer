const mongoose = require('mongoose');

const TrafficStatSchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now },
  totalPackets: Number,
  activeFlows: Number,
  currentBandwidth: Number, // Mbps
  pps: Number,
  topApps: [{
    name: String,
    packets: Number,
    color: String
  }]
});

module.exports = mongoose.model('TrafficStat', TrafficStatSchema);
