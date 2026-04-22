import React, { useState, useEffect } from 'react';
import { Shield, Activity, Lock, Terminal, Radio, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('swarm');
  const [status, setStatus] = useState({ territories: [] });

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 font-sans selection:bg-cyan-500/30">
      {/* Sidebar */}
      <nav className="fixed left-0 top-0 h-full w-20 bg-[#111114] border-r border-white/5 flex flex-col items-center py-8 space-y-8 z-50">
        <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Shield className="text-white" size={24} />
        </div>
        
        <div className="flex-1 flex flex-col space-y-6">
          <TabIcon icon={<Activity />} active={activeTab === 'swarm'} onClick={() => setActiveTab('swarm')} />
          <TabIcon icon={<Lock />} active={activeTab === 'vault'} onClick={() => setActiveTab('vault')} />
          <TabIcon icon={<Terminal />} active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} />
        </div>
        
        <Radio className="text-slate-600 animate-pulse" />
      </nav>

      {/* Main Content */}
      <main className="pl-20 pt-8 pr-8">
        <header className="mb-12 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">AgentX Command Center</h1>
            <p className="text-slate-400">Autonomous Secure Orchestration v1.0.2</p>
          </div>
          <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
            <span className="text-emerald-500 text-sm font-medium">All Agents Online</span>
          </div>
        </header>

        {activeTab === 'swarm' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <TerritoryCard name="src/prod" status="Healthy" load="2%" />
            <TerritoryCard name="src/vault" status="Secured" load="0.5%" />
            <TerritoryCard name="src/tools" status="Healing" load="45%" isHealing />
          </div>
        )}

        {/* Console / Logs Section */}
        <div className="mt-12 bg-[#111114] rounded-2xl border border-white/5 p-6 overflow-hidden">
          <div className="flex items-center space-x-2 mb-4 text-slate-500 text-sm font-mono">
            <Terminal size={14} />
            <span>LIVE_SWARM_TELEMETRY</span>
          </div>
          <div className="font-mono text-sm space-y-2 h-48 overflow-y-auto custom-scrollbar">
            <div className="text-cyan-500">[SWARM_MASTER] Dispatching agent to territory: src/prod</div>
            <div className="text-slate-400">[AGENT_01] Health check passed. System status: GREEN.</div>
            <div className="text-amber-500">[SWARM_MASTER] Warning: Integrity anomaly detected in src/tools.</div>
            <div className="text-amber-400">[AGENT_03] Initiating self-healing protocol...</div>
            <div className="text-slate-400 animate-pulse">_</div>
          </div>
        </div>
      </main>
    </div>
  );
};

const TabIcon = ({ icon, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`p-3 rounded-xl transition-all duration-300 ${active ? 'bg-white/10 text-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.1)]' : 'text-slate-600 hover:text-slate-300'}`}
  >
    {React.cloneElement(icon, { size: 20 })}
  </button>
);

const TerritoryCard = ({ name, status, load, isHealing }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`p-6 rounded-2xl border transition-all duration-500 ${isHealing ? 'bg-amber-500/5 border-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.05)]' : 'bg-[#111114] border-white/5'}`}
  >
    <div className="flex justify-between items-start mb-8">
      <div>
        <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-1">{name}</h3>
        <p className={`text-lg font-semibold ${isHealing ? 'text-amber-400' : 'text-white'}`}>{status}</p>
      </div>
      <div className={`p-2 rounded-lg ${isHealing ? 'bg-amber-500/20 text-amber-400' : 'bg-white/5 text-slate-400'}`}>
        <Activity size={18} />
      </div>
    </div>
    <div className="flex items-center justify-between">
      <div className="flex-1 mr-4 h-1 bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: load }}
          className={`h-full ${isHealing ? 'bg-amber-500' : 'bg-cyan-500'}`} 
        />
      </div>
      <span className="text-xs font-mono text-slate-500">{load}</span>
    </div>
  </motion.div>
);

export default Dashboard;
