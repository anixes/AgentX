import React, { useEffect, useState } from 'react';
import {
  Activity,
  FileText,
  Folder,
  History,
  Menu,
  MessageSquare,
  Play,
  Settings,
  Shield,
  ShieldAlert,
  Timer
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

type Territory = {
  name: string;
  status: string;
  load: string;
};

type Approval = {
  id: string;
  tool: string;
  input: Record<string, unknown>;
  command?: string;
  rootBinary?: string;
  level?: string;
  reasons: string[];
  createdAt: string;
};

type RuntimeEvent = {
  id: string;
  type: 'ALLOW' | 'ASK' | 'DENY' | 'APPROVED' | 'DENIED' | 'INFO';
  tool: string;
  message: string;
  command?: string;
  rootBinary?: string;
  level?: string;
  createdAt: string;
};

type GitCommit = {
  hash: string;
  author: string;
  time: string;
  subject: string;
};

type Baton = {
  id?: number;
  file: string;
  task?: string;
  context?: string;
  status?: string;
  stage?: string;
  progress?: number;
  last_pulse?: number;
  output?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
  history_count?: number;
  history?: Array<{
    stage?: string;
    message?: string;
    timestamp?: string;
  }>;
};

type DashboardStatus = {
  territories: Territory[];
  total_files: number;
  active_agents: number;
  safety_alerts: number;
  pending_approval: Approval | null;
  baton_count?: number;
  token_stats?: {
    total: number;
    saved: number;
    lastTurn: number;
  };
};

type RuntimeSnapshot = {
  status: DashboardStatus;
  events: RuntimeEvent[];
  diff: string;
  history: GitCommit[];
  batons: Baton[];
};

const emptyStatus: DashboardStatus = {
  territories: [],
  total_files: 0,
  active_agents: 0,
  safety_alerts: 0,
  pending_approval: null,
};

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState<'status' | 'files' | 'history' | 'settings'>('status');
  const [data, setData] = useState<DashboardStatus>(emptyStatus);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [currentDiff, setCurrentDiff] = useState('// Everything is up to date.');
  const [history, setHistory] = useState<GitCommit[]>([]);
  const [batons, setBatons] = useState<Baton[]>([]);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'deny' | null>(null);
  const [approvalMessage, setApprovalMessage] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'live' | 'offline'>('connecting');
  const [missionInput, setMissionInput] = useState('');
  const [missionStatus, setMissionStatus] = useState<string | null>(null);
  const [missionLoading, setMissionLoading] = useState(false);
  const [settingsProvider, setSettingsProvider] = useState('openrouter');
  const [settingsKey, setSettingsKey] = useState('');
  const [settingsModel, setSettingsModel] = useState('');
  const [settingsKeySet, setSettingsKeySet] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsMsg, setSettingsMsg] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/runtime/stream`);

    eventSource.onopen = () => {
      setConnectionState('live');
    };

    eventSource.onmessage = (event) => {
      try {
        const snapshot = JSON.parse(event.data) as RuntimeSnapshot;
        setData(snapshot.status ?? emptyStatus);
        setEvents(snapshot.events ?? []);
        setCurrentDiff(snapshot.diff ?? '// Everything is up to date.');
        setHistory(snapshot.history ?? []);
        setBatons(snapshot.batons ?? []);
        setConnectionState('live');
      } catch {
        setConnectionState('offline');
      }
    };

    eventSource.onerror = () => {
      setConnectionState('offline');
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    axios.get(`${API_BASE}/config`).then((res) => {
      setSettingsProvider(res.data.provider || 'openrouter');
      setSettingsModel(res.data.model || '');
      setSettingsKeySet(res.data.api_key_set || false);
    }).catch(() => {});
  }, []);

  const handleApprovalAction = async (action: 'approve' | 'deny') => {
    setApprovalAction(action);
    setApprovalMessage(null);

    try {
      const response = await axios.post(`${API_BASE}/runtime/${action}`, {}, {
        headers: {
          'Authorization': `Bearer dev-token-123`
        }
      });
      setApprovalMessage(response.data.message ?? `${action} succeeded.`);
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : `Unable to ${action} the pending approval.`;
      setApprovalMessage(String(message));
    } finally {
      setApprovalAction(null);
    }
  };

  const handleRunMission = async () => {
    if (!missionInput.trim()) return;
    setMissionLoading(true);
    setMissionStatus(null);
    try {
      const response = await axios.post(`${API_BASE}/swarm/run`, { objective: missionInput }, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      setMissionStatus(response.data.message ?? 'Mission started.');
      setMissionInput('');
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : 'Failed to start mission.';
      setMissionStatus(String(message));
    } finally {
      setMissionLoading(false);
    }
  };

  const pendingApproval = data.pending_approval;

  return (
    <div className="min-h-screen bg-[#0f1115] text-[#e0e0e0] font-sans selection:bg-cyan-500/20">
      <nav className="fixed left-0 top-0 h-full w-20 bg-[#16191f] border-r border-white/[0.03] flex flex-col items-center py-10 space-y-12 z-50">
        <div className="w-10 h-10 bg-cyan-600/20 rounded-2xl flex items-center justify-center">
          <Shield className="text-cyan-400" size={20} />
        </div>
        <div className="flex-1 flex flex-col space-y-8">
          <NavLink icon={<Activity />} active={activeTab === 'status'} onClick={() => setActiveTab('status')} />
          <NavLink icon={<Folder />} active={activeTab === 'files'} onClick={() => setActiveTab('files')} />
          <NavLink icon={<History />} active={activeTab === 'history'} onClick={() => setActiveTab('history')} />
          <NavLink icon={<Settings />} active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </div>
        <Menu className="text-slate-600 cursor-pointer hover:text-slate-400 transition-colors" size={20} />
      </nav>

      <main className="pl-20 min-h-screen flex flex-col">
        <header className="px-12 py-8 flex justify-between items-center bg-[#0f1115]/50 backdrop-blur-xl sticky top-0 z-40 border-b border-white/[0.02]">
          <div>
            <h1 className="text-lg font-medium text-white tracking-tight">Agent Dashboard</h1>
            <p className="text-sm text-slate-500 font-normal">Observe runtime, approvals, and workspace telemetry</p>
          </div>
          <div className="flex gap-6 items-center">
            <ConnectionBadge state={connectionState} />
            {data.safety_alerts > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-300 text-xs">
                <ShieldAlert size={14} />
                <span>{data.safety_alerts} Pending Approval</span>
              </div>
            )}
            <HeaderStat label="Files" value={data.total_files} />
            <HeaderStat label="Batons" value={data.baton_count ?? batons.length} highlight={(data.baton_count ?? batons.length) > 0} />
            <HeaderStat label="Agents" value={data.active_agents} highlight={data.active_agents > 0} />
            
            {data.token_stats && (
              <div className="flex gap-4 border-l border-white/[0.05] pl-6 ml-2">
                 <HeaderStat 
                    label="Tokens" 
                    value={`${(data.token_stats.total / 1000).toFixed(1)}k`} 
                 />
                 <HeaderStat 
                    label="Saved" 
                    value={`${(data.token_stats.saved / 1000).toFixed(1)}k`} 
                    highlight={data.token_stats.saved > 0}
                 />
                 <div className="flex flex-col items-end">
                    <span className="text-[10px] text-slate-600 uppercase font-bold tracking-wider">Efficiency</span>
                    <span className="text-sm font-medium text-emerald-400">
                       {data.token_stats.total > 0 
                          ? `${Math.round((data.token_stats.saved / (data.token_stats.total + data.token_stats.saved)) * 100)}%`
                          : '100%'}
                    </span>
                 </div>
              </div>
            )}
          </div>
        </header>

        <div className="flex-1 px-12 py-10">
          <AnimatePresence mode="wait">
            {activeTab === 'status' && (
              <motion.div
                key="status"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-10 max-w-7xl"
              >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {data.territories.map((territory, index) => (
                    <StatusCard
                      key={index}
                      title={territory.name.split('/').pop() ?? territory.name}
                      status={territory.status}
                      load={territory.load}
                    />
                  ))}
                </div>

                <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <Play size={16} className="text-cyan-400" />
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Run Mission</h3>
                  </div>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={missionInput}
                      onChange={(e) => setMissionInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRunMission()}
                      placeholder='e.g. "Fix all linting errors in src/"'
                      className="flex-1 bg-[#0f1115] border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/40 transition-colors"
                    />
                    <button
                      onClick={handleRunMission}
                      disabled={missionLoading || !missionInput.trim()}
                      className="px-5 py-2.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/20 rounded-xl text-cyan-300 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {missionLoading ? 'Launching...' : 'Launch'}
                    </button>
                  </div>
                  {missionStatus && (
                    <p className="mt-3 text-xs text-slate-400">{missionStatus}</p>
                  )}
                </div>

                <div className="grid grid-cols-12 gap-10">
                  <div className="col-span-12 xl:col-span-7 space-y-6">
                    <SectionTitle icon={<ShieldAlert size={16} />} title="Approval Queue" />
                    <ApprovalPanel
                      approval={pendingApproval}
                      actionInFlight={approvalAction}
                      actionMessage={approvalMessage}
                      onApprove={() => handleApprovalAction('approve')}
                      onDeny={() => handleApprovalAction('deny')}
                    />

                    <SectionTitle icon={<Activity size={16} />} title="Task Board" />
                    <BatonBoard batons={batons} />

                    <SectionTitle icon={<FileText size={16} />} title="Runtime Diff" />
                    <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 shadow-sm">
                      <pre className="text-sm text-slate-400 leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono">
                        <code>{currentDiff}</code>
                      </pre>
                    </div>
                  </div>

                  <div className="col-span-12 xl:col-span-5 space-y-6">
                    <SectionTitle icon={<MessageSquare size={16} />} title="Security Events" />
                    <div className="space-y-4 max-h-[720px] overflow-y-auto pr-2 custom-scrollbar">
                      {events.length === 0 && <p className="text-sm text-slate-600">No runtime events recorded yet.</p>}
                      {events.map((event) => (
                        <EventCard key={event.id} event={event} />
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'files' && (
              <motion.div
                key="files"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <SectionTitle icon={<Folder size={16} />} title="Territories" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {data.territories.map((territory, index) => (
                    <div
                      key={index}
                      className="bg-[#16191f] p-8 rounded-3xl border border-white/[0.03] space-y-4 hover:border-cyan-500/20 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="text-white font-medium capitalize">{territory.name.split('/').pop()}</h3>
                        <RiskPill tone={territory.status === 'healing' ? 'ask' : 'allow'}>
                          {territory.status === 'healing' ? 'Healing' : 'Stable'}
                        </RiskPill>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-slate-500">Path: {territory.name}</p>
                        <p className="text-xs text-slate-500">Reported load: {territory.load}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div
                key="history"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-3xl space-y-8"
              >
                <SectionTitle icon={<History size={16} />} title="Git History" />
                {history.map((commit) => (
                  <div key={commit.hash} className="flex gap-8 group">
                    <span className="text-xs text-slate-600 pt-1 w-24">{commit.time}</span>
                    <div className="flex-1">
                      <p className="text-sm text-white font-medium mb-1">{commit.subject}</p>
                      <p className="text-xs text-slate-500">
                        {commit.author} · {commit.hash}
                      </p>
                    </div>
                  </div>
                ))}
                {history.length === 0 && <p className="text-sm text-slate-600">No git history available.</p>}
              </motion.div>
            )}

            {activeTab === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-xl space-y-8"
              >
                <SectionTitle icon={<Settings size={16} />} title="API Configuration" />
                <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 space-y-6">
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">Provider</label>
                    <select
                      value={settingsProvider}
                      onChange={(e) => setSettingsProvider(e.target.value)}
                      className="w-full bg-[#0f1115] border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500/40 transition-colors appearance-none"
                    >
                      <option value="openrouter">OpenRouter (recommended)</option>
                      <option value="openai">OpenAI</option>
                      <option value="groq">Groq</option>
                      <option value="nvidia">NVIDIA</option>
                      <option value="together">Together</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">API Key</label>
                    <input
                      type="password"
                      value={settingsKey}
                      onChange={(e) => setSettingsKey(e.target.value)}
                      placeholder={settingsKeySet ? '(key is set - enter new to replace)' : 'Paste your API key here'}
                      className="w-full bg-[#0f1115] border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/40 transition-colors"
                    />
                    {settingsKeySet && !settingsKey && (
                      <p className="mt-1 text-xs text-emerald-400">Key is configured.</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">Model</label>
                    <input
                      type="text"
                      value={settingsModel}
                      onChange={(e) => setSettingsModel(e.target.value)}
                      placeholder={settingsProvider === 'openrouter' ? 'e.g. anthropic/claude-sonnet-4' : 'e.g. gpt-4o-mini'}
                      className="w-full bg-[#0f1115] border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/40 transition-colors"
                    />
                    {settingsProvider === 'openrouter' && (
                      <p className="mt-1 text-xs text-slate-600">Popular: anthropic/claude-sonnet-4, google/gemini-2.5-flash, meta-llama/llama-4-maverick</p>
                    )}
                  </div>
                  <div className="flex items-center gap-4 pt-2">
                    <button
                      onClick={async () => {
                        setSettingsSaving(true);
                        setSettingsMsg(null);
                        try {
                          const payload: Record<string, string> = { provider: settingsProvider, model: settingsModel };
                          if (settingsKey) payload.api_key = settingsKey;
                          await axios.post(`${API_BASE}/config`, payload, {
                            headers: { 'Authorization': `Bearer dev-token-123` }
                          });
                          setSettingsMsg('Configuration saved.');
                          setSettingsKeySet(settingsKeySet || !!settingsKey);
                          setSettingsKey('');
                        } catch {
                          setSettingsMsg('Failed to save configuration.');
                        } finally {
                          setSettingsSaving(false);
                        }
                      }}
                      disabled={settingsSaving}
                      className="px-6 py-2.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/20 rounded-xl text-cyan-300 text-sm font-medium transition-colors disabled:opacity-40"
                    >
                      {settingsSaving ? 'Saving...' : 'Save'}
                    </button>
                    {settingsMsg && <p className="text-xs text-slate-400">{settingsMsg}</p>}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
};

const SectionTitle = ({ icon, title }: { icon: React.ReactElement; title: string }) => (
  <h2 className="text-sm font-medium text-slate-400 flex items-center gap-2">
    {icon}
    {title}
  </h2>
);

const ApprovalPanel = ({
  approval,
  actionInFlight,
  actionMessage,
  onApprove,
  onDeny,
}: {
  approval: Approval | null;
  actionInFlight: 'approve' | 'deny' | null;
  actionMessage: string | null;
  onApprove: () => void;
  onDeny: () => void;
}) => {
  if (!approval) {
    return (
      <div className="bg-[#16191f] rounded-[28px] border border-white/[0.03] p-8">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-2xl bg-cyan-500/10 text-cyan-300 flex items-center justify-center">
            <Shield size={18} />
          </div>
          <div>
            <p className="text-white font-medium">No approval is waiting.</p>
            <p className="text-sm text-slate-500 mt-2">
              Risky tool calls will appear here with their command, root binary, and review reasons.
            </p>
            {actionMessage && <p className="text-sm text-cyan-300 mt-3">{actionMessage}</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[linear-gradient(180deg,rgba(245,158,11,0.12),rgba(22,25,31,0.96))] rounded-[28px] border border-amber-400/20 p-8 shadow-[0_20px_80px_rgba(0,0,0,0.2)]">
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <RiskPill tone="ask">{approval.level || 'MEDIUM'} Risk</RiskPill>
        <RiskPill tone="neutral">{approval.tool}</RiskPill>
        {approval.rootBinary && <RiskPill tone="neutral">Root: {approval.rootBinary}</RiskPill>}
      </div>

      <p className="text-white text-lg font-medium leading-snug">Manual review required before execution</p>
      <p className="text-sm text-amber-100/80 mt-2">
        Review the command below, then approve or deny it directly from the dashboard.
      </p>

      <div className="mt-6 rounded-2xl bg-black/25 border border-white/10 p-5">
        <p className="text-[10px] uppercase tracking-[0.24em] text-amber-200/60 mb-2">Command</p>
        <pre className="text-sm text-amber-50 whitespace-pre-wrap font-mono">{approval.command || 'Unknown command'}</pre>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {approval.reasons.map((reason, index) => (
          <div key={`${approval.id}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
            <p className="text-[10px] uppercase tracking-[0.18em] text-amber-200/50 mb-2">Reason {index + 1}</p>
            <p className="text-sm text-slate-100">{reason}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          onClick={onApprove}
          disabled={actionInFlight !== null}
          className="px-5 py-3 rounded-2xl bg-cyan-400 text-slate-950 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {actionInFlight === 'approve' ? 'Approving...' : 'Approve'}
        </button>
        <button
          onClick={onDeny}
          disabled={actionInFlight !== null}
          className="px-5 py-3 rounded-2xl bg-red-500/12 text-red-200 border border-red-500/20 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {actionInFlight === 'deny' ? 'Denying...' : 'Deny'}
        </button>
      </div>

      {actionMessage && <p className="text-sm text-amber-50/90 mt-4">{actionMessage}</p>}
    </div>
  );
};

const EventCard = ({ event }: { event: RuntimeEvent }) => {
  const tone =
    event.type === 'DENY' || event.type === 'DENIED'
      ? 'deny'
      : event.type === 'ASK'
        ? 'ask'
        : event.type === 'APPROVED'
          ? 'allow'
          : 'neutral';

  return (
    <div className="flex gap-4 group p-4 rounded-[24px] bg-[#16191f] border border-white/[0.03] hover:border-white/[0.08] transition-all">
      <div
        className={`mt-1 w-2.5 h-2.5 rounded-full ${
          tone === 'deny'
            ? 'bg-red-500'
            : tone === 'ask'
              ? 'bg-amber-400'
              : tone === 'allow'
                ? 'bg-cyan-400'
                : 'bg-slate-600'
        }`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 flex-wrap">
            <RiskPill tone={tone}>{event.type}</RiskPill>
            <span className="text-[11px] uppercase tracking-[0.18em] text-slate-600">{event.tool}</span>
            {event.level && <span className="text-[11px] text-slate-500">{event.level}</span>}
          </div>
          <span className="text-[11px] text-slate-700">{formatTimestamp(event.createdAt)}</span>
        </div>
        <p className="text-sm text-slate-200">{event.message}</p>
        {event.command && <p className="text-xs text-slate-500 font-mono mt-2 break-all">{event.command}</p>}
      </div>
    </div>
  );
};

const BatonBoard = ({ batons }: { batons: Baton[] }) => {
  if (batons.length === 0) {
    return (
      <div className="bg-[#16191f] rounded-[28px] border border-white/[0.03] p-8">
        <p className="text-white font-medium">No baton tasks are active.</p>
        <p className="text-sm text-slate-500 mt-2">
          Orchestrated worker tasks will appear here with status, file context, and any failure details.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      {batons.map((baton) => {
        const isLive = baton.last_pulse && (Date.now() / 1000 - baton.last_pulse) < 60;
        
        return (
          <div
            key={baton.file}
            className="bg-[#16191f] rounded-[24px] border border-white/[0.03] p-6 space-y-4 relative overflow-hidden"
          >
            {/* Live Progress Background */}
            {baton.status !== 'failed' && baton.status !== 'completed' && (
               <div className="absolute bottom-0 left-0 h-1 bg-cyan-500/20 w-full">
                  <motion.div 
                    className="h-full bg-cyan-500" 
                    initial={{ width: 0 }}
                    animate={{ width: `${baton.progress ?? 0}%` }}
                    transition={{ type: 'spring', stiffness: 50 }}
                  />
               </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="text-white font-medium">{baton.task || baton.file}</p>
                  {isLive && (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                       <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                       <span className="text-[9px] text-cyan-300 font-bold uppercase tracking-wider">Live</span>
                    </div>
                  )}
                </div>
                <p className="text-xs text-slate-500">{baton.context || baton.file}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <RiskPill tone={batonTone(baton.status)}>{baton.status || 'unknown'}</RiskPill>
                {baton.stage && <RiskPill tone="neutral">{baton.stage}</RiskPill>}
                {baton.progress !== undefined && <span className="text-[11px] font-mono text-slate-400 pt-1">{baton.progress}%</span>}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-500">
              <div>
                <p className="uppercase tracking-[0.16em] text-slate-600 mb-1">Updated</p>
                <div className="flex items-center gap-2">
                   <Timer size={12} className="text-slate-700" />
                   <p>{baton.updated_at ? formatTimestamp(baton.updated_at) : 'Unknown'}</p>
                </div>
              </div>
              <div>
                <p className="uppercase tracking-[0.16em] text-slate-600 mb-1">Pulse</p>
                <p className={isLive ? 'text-cyan-500/80' : 'text-slate-700'}>
                   {isLive ? 'Active Heartbeat' : 'Flatlined / Finished'}
                </p>
              </div>
              <div>
                <p className="uppercase tracking-[0.16em] text-slate-600 mb-1">File</p>
                <p className="truncate w-32">{baton.file}</p>
              </div>
            </div>

            {baton.error && (
              <div className="rounded-2xl border border-red-500/15 bg-red-500/8 p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-red-300/70 mb-2">Failure</p>
                <p className="text-sm text-red-100">{baton.error}</p>
              </div>
            )}
            {!baton.error && baton.output && (
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">Latest Output</p>
                <p className="text-sm text-slate-200 line-clamp-4 whitespace-pre-wrap">{baton.output}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

const NavLink = ({
  icon,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    className={`p-3 rounded-2xl transition-all ${
      active ? 'bg-white/[0.05] text-cyan-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
  </button>
);

const HeaderStat = ({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number;
  highlight?: boolean;
}) => (
  <div className="flex flex-col items-end">
    <span className="text-[10px] text-slate-600 uppercase font-bold tracking-wider">{label}</span>
    <span className={`text-sm font-medium ${highlight ? 'text-cyan-400' : 'text-white'}`}>{value}</span>
  </div>
);

const StatusCard = ({
  title,
  status,
  load,
}: {
  title: string;
  status: string;
  load: string;
}) => (
  <div className="bg-[#16191f] p-8 rounded-3xl border border-white/[0.03] flex flex-col space-y-6">
    <div className="flex justify-between items-start">
      <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest">{title}</h3>
      <div className={`w-2 h-2 rounded-full ${status === 'healing' ? 'bg-amber-400 animate-pulse' : 'bg-cyan-500'}`} />
    </div>
    <div className="space-y-4">
      <p className="text-2xl font-medium text-white capitalize">{status === 'healing' ? 'Healing' : 'Stable'}</p>
      <div className="h-1 bg-white/[0.02] rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: load }}
          className={`h-full ${status === 'healing' ? 'bg-amber-400' : 'bg-cyan-500'}`}
        />
      </div>
    </div>
  </div>
);

const RiskPill = ({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone: 'allow' | 'ask' | 'deny' | 'neutral';
}) => {
  const toneClass =
    tone === 'deny'
      ? 'bg-red-500/10 text-red-300 border-red-500/20'
      : tone === 'ask'
        ? 'bg-amber-500/10 text-amber-200 border-amber-500/20'
        : tone === 'allow'
          ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20'
          : 'bg-white/[0.04] text-slate-300 border-white/[0.06]';

  return <span className={`px-3 py-1 rounded-full border text-[11px] uppercase tracking-[0.16em] ${toneClass}`}>{children}</span>;
};

const ConnectionBadge = ({ state }: { state: 'connecting' | 'live' | 'offline' }) => {
  const toneClass =
    state === 'live'
      ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20'
      : state === 'connecting'
        ? 'bg-amber-500/10 text-amber-200 border-amber-500/20'
        : 'bg-red-500/10 text-red-300 border-red-500/20';

  const label = state === 'live' ? 'Live SSE' : state === 'connecting' ? 'Connecting' : 'Offline';

  return <span className={`px-3 py-1 rounded-full border text-[11px] uppercase tracking-[0.16em] ${toneClass}`}>{label}</span>;
};

function formatTimestamp(value: string | number): string {
  const date = typeof value === 'number' ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function batonTone(status?: string): 'allow' | 'ask' | 'deny' | 'neutral' {
  if (!status) {
    return 'neutral';
  }

  const normalized = status.toLowerCase();
  if (normalized === 'completed' || normalized === 'stable' || normalized === 'done') {
    return 'allow';
  }
  if (normalized === 'failed' || normalized === 'invalid') {
    return 'deny';
  }
  if (normalized === 'pending' || normalized === 'executing' || normalized === 'healing' || normalized === 'working') {
    return 'ask';
  }
  return 'neutral';
}



export default Dashboard;
