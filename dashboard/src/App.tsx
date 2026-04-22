import React, { useState, useEffect } from 'react';
import { Code, Cpu, Layers, GitBranch, Terminal, Radio, FileCode, Box, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_BASE = "http://localhost:8000";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('factory');
  const [swarmData, setSwarmData] = useState({ territories: [], total_files: 0, active_agents: 0 });
  const [logs, setLogs] = useState([{ msg: '[ENGINE] Factory initialized...', time: new Date().toLocaleTimeString() }]);
  const [activeCode, setActiveCode] = useState("// Waiting for agent task...");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API_BASE}/status`);
        setSwarmData(res.data);
        
        const diffRes = await axios.get(`${API_BASE}/diff`);
        if (diffRes.data.diff !== activeCode) {
           setActiveCode(diffRes.data.diff);
           addLog(`[FILE] Detected refactor sync: src/prod/app.ts`);
        }
      } catch (e) {
        addLog(`[ERROR] Factory bridge link broken.`);
      }
    };
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [activeCode]);

  const addLog = (msg) => {
    setLogs(prev => [{ msg, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30));
  };

  return (
    <div className="min-h-screen bg-[#0d0f14] text-slate-300 font-mono selection:bg-emerald-500/30">
      <nav className="fixed left-0 top-0 h-full w-16 bg-[#161b22] border-r border-white/5 flex flex-col items-center py-6 space-y-8 z-50">
        <div className="w-10 h-10 bg-emerald-500/20 border border-emerald-500/40 rounded-lg flex items-center justify-center">
          <Code className="text-emerald-400" size={20} />
        </div>
        <div className="flex-1 flex flex-col space-y-6">
          <NavItem icon={<Cpu />} active={activeTab === 'factory'} onClick={() => setActiveTab('factory')} />
          <NavItem icon={<Layers />} active={activeTab === 'modules'} onClick={() => setActiveTab('modules')} />
          <NavItem icon={<GitBranch />} active={activeTab === 'git'} onClick={() => setActiveTab('git')} />
        </div>
        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]" />
      </nav>

      <main className="pl-24 pt-8 pr-8 pb-12">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-3">
               AgentX Engineering Factory <span className="text-xs font-normal text-emerald-500/50 bg-emerald-500/5 px-2 py-0.5 rounded border border-emerald-500/10">v1.0.2-LIVE</span>
            </h1>
            <p className="text-slate-500 text-xs mt-1 italic">Real-time Autonomous Development Feed</p>
          </div>
          <div className="flex gap-4">
             <StatBadge icon={<Box size={14}/>} label="Source Files" value={swarmData.total_files} />
             <StatBadge icon={<Zap size={14}/>} label="Workers" value={`${swarmData.active_agents} Active`} color="text-emerald-400" />
          </div>
        </header>

        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-7 space-y-6">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Layers size={14} /> Module Health Matrix
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {swarmData.territories.map((mod, i) => (
                <ModuleCard key={i} mod={mod} />
              ))}
            </div>

            <div className="bg-[#161b22] rounded-xl border border-white/5 overflow-hidden animate-glow">
               <div className="px-4 py-2 bg-white/5 border-b border-white/5 flex justify-between items-center">
                  <span className="text-[10px] text-slate-500 flex items-center gap-2"><FileCode size={12}/> LIVE_CODE_ORCHESTRATOR: {activeCode === "// Waiting for agent task..." ? "IDLE" : "DIFF_STREAM"}</span>
                  <div className="flex gap-1">
                     <div className="w-2 h-2 rounded-full bg-red-500/20" />
                     <div className="w-2 h-2 rounded-full bg-amber-500/20" />
                     <div className="w-2 h-2 rounded-full bg-emerald-500/20" />
                  </div>
               </div>
               <div className="p-4 h-48 overflow-y-auto custom-scrollbar bg-[#0a0c10]/50">
                  <pre className="text-[11px] text-emerald-400/80 leading-relaxed">
                    <code>{activeCode}</code>
                  </pre>
               </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-5 space-y-6">
             <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Terminal size={14} /> Autonomous Log Stream
            </h2>
            <div className="bg-[#0a0c10] border border-white/5 rounded-xl h-[450px] flex flex-col p-4">
               <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
                  {logs.map((log, i) => (
                    <div key={i} className="text-[10px] flex gap-3">
                      <span className="text-slate-600 font-mono">[{log.time}]</span>
                      <span className={`${log.msg.includes('ERROR') ? 'text-red-400' : 'text-slate-400'}`}>{log.msg}</span>
                    </div>
                  ))}
               </div>
               <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                  <span className="text-[10px] text-slate-600 uppercase">System Heartbeat: Stable</span>
               </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const NavItem = ({ icon, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`p-2 rounded-lg transition-all ${active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-600 hover:text-slate-400'}`}
  >
    {React.cloneElement(icon, { size: 18 })}
  </button>
);

const StatBadge = ({ icon, label, value, color="text-slate-400" }) => (
  <div className="px-3 py-1.5 bg-[#161b22] rounded-lg border border-white/5 flex items-center gap-2">
    {icon}
    <span className="text-[10px] font-bold text-slate-500 uppercase">{label}:</span>
    <span className={`text-[10px] font-bold ${color}`}>{value}</span>
  </div>
);

const ModuleCard = ({ mod }) => (
  <motion.div 
    className={`p-4 rounded-xl border bg-[#161b22] ${mod.status === 'healing' ? 'border-emerald-500/30' : 'border-white/5'}`}
  >
    <div className="flex justify-between items-center mb-4">
       <span className="text-[11px] font-bold text-slate-400">{mod.name}</span>
       <div className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${mod.status === 'healing' ? 'bg-emerald-500/20 text-emerald-400 animate-pulse' : 'bg-slate-500/10 text-slate-500'}`}>
         {mod.status}
       </div>
    </div>
    <div className="space-y-2">
       <div className="flex justify-between text-[10px] text-slate-500">
          <span>Worker: {mod.worker}</span>
          <span>{mod.load}</span>
       </div>
       <div className="h-1 bg-white/5 rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: mod.load }}
            className={`h-full ${mod.status === 'healing' ? 'bg-emerald-500' : 'bg-slate-600'}`}
          />
       </div>
    </div>
  </motion.div>
);

export default Dashboard;
