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
  Timer,
  CheckCircle,
  Clock,
  Archive,
  ArrowUpRight,
  Brain,
  Zap,
  TrendingUp,
  ClipboardList
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
  commandPreview?: string;
  actionType?: string;
  rootBinary?: string;
  level?: string;
  riskLevel?: 'low' | 'medium' | 'high';
  reasons: string[];
  humanReason?: string;
  rollbackPath?: string;
  expiresAt?: string;
  requesterSource?: 'CLI' | 'dashboard' | 'Telegram' | 'swarm';
  dryRunSummary?: string;
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
  definition_of_done?: string[];
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

type Communication = {
  message_id: string;
  recipient: string;
  channel: string;
  subject: string;
  draft_content: string;
  tone_profile: string;
  approval_status: string;
  delivery_status: string;
  follow_up_required: boolean;
  follow_up_due?: string;
  related_task_id?: string;
  updated_at: string;
  created_at: string;
};

type Task = {
  task_id: string;
  title: string;
  description?: string;
  priority: string;
  urgency_score?: number;
  status: string;
  due_date?: string;
  escalation_level?: number;
  follow_up_state?: string;
  related_communication_id?: string;
  delegated_worker_status?: string;
  definition_of_done?: string[];
  created_at: string;
  updated_at: string;
};

type PrioritizedTask = Task & {
  priority_score: number;
  urgency_tier: 'critical' | 'high' | 'medium' | 'low';
  urgency_pts: number;
  stakeholder_pts: number;
  consequence_pts: number;
  intent_pts: number;
  decision_recommendation: string;
  escalation_recommendation: string;
  can_ignore: boolean;
  ignore_reason?: string;
  approval_recommendation: string;
  urgency_challenge?: string;
  days_until_due?: number;
};

type PriorityEngine = {
  top3: PrioritizedTask[];
  all_scored: PrioritizedTask[];
  ignore_candidates: PrioritizedTask[];
  total_tasks: number;
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
  const [history, setHistory] = useState<GitCommit[]>([]);
  const [batons, setBatons] = useState<Baton[]>([]);
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [priorities, setPriorities] = useState<PriorityEngine | null>(null);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'deny' | null>(null);
  const [approvalMessage, setApprovalMessage] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'live' | 'offline'>('connecting');
  const [missionInput, setMissionInput] = useState('');
  const [missionStatus, setMissionStatus] = useState<string | null>(null);
  const [missionLoading, setMissionLoading] = useState(false);
  const [missionDod, setMissionDod] = useState('');
  const [missionDodExpanded, setMissionDodExpanded] = useState(false);
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

  const fetchCommunications = async () => {
    try {
      const res = await axios.get(`${API_BASE}/communications`, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      setCommunications(res.data.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/memory/tasks?status=pending,active,blocked,escalated`, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      // Sort tasks by priority/urgency
      const fetchedTasks = res.data.tasks || [];
      fetchedTasks.sort((a: Task, b: Task) => (b.urgency_score || 0) - (a.urgency_score || 0));
      setTasks(fetchedTasks);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchPriorities = async () => {
    try {
      const res = await axios.get(`${API_BASE}/priority/engine`, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      setPriorities(res.data);
    } catch (e) {
      console.error('Priority engine fetch failed', e);
    }
  };

  useEffect(() => {
    fetchCommunications();
    fetchTasks();
    fetchPriorities();
    const interval = setInterval(() => {
      fetchCommunications();
      fetchTasks();
      fetchPriorities();
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleCommAction = async (id: string, action: 'approve' | 'reject' | 'send') => {
    try {
      await axios.post(`${API_BASE}/communications/${id}/${action}`, {}, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      fetchCommunications();
    } catch (error) {
      console.error(`Failed to ${action} communication`, error);
    }
  };

  const handleTaskAction = async (id: string, action: 'complete' | 'archive' | 'snooze' | 'escalate') => {
    try {
      if (action === 'snooze') {
        await axios.post(`${API_BASE}/scheduler/snooze/${id}`, { until: 'tomorrow' }, {
          headers: { 'Authorization': `Bearer dev-token-123` }
        });
      } else if (action === 'escalate') {
        const task = tasks.find(t => t.task_id === id);
        const newLevel = (task?.escalation_level || 0) + 1;
        await axios.patch(`${API_BASE}/memory/tasks/${id}`, { escalation_level: newLevel }, {
          headers: { 'Authorization': `Bearer dev-token-123` }
        });
      } else {
        await axios.post(`${API_BASE}/memory/tasks/${id}/${action}`, {}, {
          headers: { 'Authorization': `Bearer dev-token-123` }
        });
      }
      fetchTasks();
    } catch (error) {
      console.error(`Failed to ${action} task`, error);
    }
  };

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
    const dodItems = missionDod.split('\n').map(l => l.trim()).filter(Boolean);
    try {
      const response = await axios.post(`${API_BASE}/swarm/run`, {
        objective: missionInput,
        definition_of_done: dodItems,
      }, {
        headers: { 'Authorization': `Bearer dev-token-123` }
      });
      const dod: string[] = response.data.definition_of_done || [];
      setMissionStatus(
        (response.data.message ?? 'Mission started.') +
        (dod.length ? `\nDoD: ${dod.length} criteria${dodItems.length === 0 ? ' (auto-generated)' : ''}` : '')
      );
      setMissionInput('');
      setMissionDod('');
      setMissionDodExpanded(false);
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
            <h1 className="text-lg font-medium text-white tracking-tight">Executive Desk</h1>
            <p className="text-sm text-slate-500 font-normal">Manage agenda, approvals, and delegations</p>
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
            <HeaderStat label="Delegations" value={data.baton_count ?? batons.length} highlight={(data.baton_count ?? batons.length) > 0} />
            <HeaderStat label="Workers" value={data.active_agents} highlight={data.active_agents > 0} />
            
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
                  <StatusCard
                    title="Urgent Tasks"
                    status={tasks.length > 0 ? 'healing' : 'stable'}
                    load={tasks.length > 0 ? '60%' : '0%'}
                    value={`${tasks.length} Tasks`}
                  />
                  <StatusCard
                    title="Pending Approvals"
                    status={pendingApproval ? 'healing' : 'stable'}
                    load={pendingApproval ? '100%' : '0%'}
                    value={pendingApproval ? '1 Pending' : '0 Pending'}
                  />
                  <StatusCard
                    title="Priority Score"
                    status={priorities && priorities.top3[0]?.urgency_tier === 'critical' ? 'healing' : 'stable'}
                    load={priorities ? `${Math.round((priorities.top3[0]?.priority_score ?? 0))}%` : '0%'}
                    value={priorities ? `${priorities.total_tasks} Scored` : 'Loading...'}
                  />
                </div>

                <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Play size={16} className="text-cyan-400" />
                      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Delegate Action</h3>
                    </div>
                    <button
                      onClick={() => setMissionDodExpanded(v => !v)}
                      className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-slate-500 hover:text-cyan-400 transition-colors"
                    >
                      <ClipboardList size={12} />
                      {missionDodExpanded ? 'Hide DoD' : 'Add Definition of Done'}
                    </button>
                  </div>

                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={missionInput}
                      onChange={(e) => setMissionInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !missionDodExpanded && handleRunMission()}
                      placeholder='e.g. "Build auth module" or "Follow up with recruiter"'
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

                  {missionDodExpanded && (
                    <div className="space-y-2">
                      <label className="text-[10px] uppercase tracking-widest text-slate-600 flex items-center gap-1.5">
                        <ClipboardList size={10} /> Definition of Done <span className="text-slate-700">(one item per line)</span>
                      </label>
                      <textarea
                        value={missionDod}
                        onChange={(e) => setMissionDod(e.target.value)}
                        rows={4}
                        placeholder={`Tests pass\nNo secret leakage\nRollback path documented\nPR summary generated`}
                        className="w-full bg-[#0f1115] border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-700 focus:outline-none focus:border-cyan-500/40 transition-colors resize-none font-mono text-xs leading-relaxed"
                      />
                      {!missionDod.trim() && (
                        <p className="text-[10px] text-violet-400/70 flex items-center gap-1">
                          <TrendingUp size={10} /> No DoD entered — AJA will auto-generate from the objective.
                        </p>
                      )}
                    </div>
                  )}

                  {!missionDodExpanded && missionInput.trim() && (
                    <p className="text-[10px] text-slate-700">
                      No DoD defined — AJA will auto-generate success criteria from the objective.
                    </p>
                  )}

                  {missionStatus && (
                    <p className="mt-1 text-xs text-slate-400 whitespace-pre-line">{missionStatus}</p>
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

                    <SectionTitle icon={<Activity size={16} />} title="Delegation Engine" />
                    <BatonBoard batons={batons} />

                    <SectionTitle icon={<Brain size={16} />} title="Top 3 Priorities Today" />
                    <Top3Panel priorities={priorities} />

                    <SectionTitle icon={<CheckCircle size={16} />} title="Urgent Tasks" />
                    <TaskBoard tasks={tasks} onAction={handleTaskAction} />

                    <SectionTitle icon={<FileText size={16} />} title="Communication Drafts" />
                    <CommunicationBoard communications={communications} onAction={handleCommAction} />
                  </div>

                  <div className="col-span-12 xl:col-span-5 space-y-6">
                    <SectionTitle icon={<MessageSquare size={16} />} title="Recent Activity" />
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
                <SectionTitle icon={<Folder size={16} />} title="System Health (Territories)" />
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
              Risky actions will appear here with command preview, expected effect, rollback path, and expiry.
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
        <RiskPill tone="neutral">{approval.actionType || approval.tool}</RiskPill>
        {approval.requesterSource && <RiskPill tone="neutral">Source: {approval.requesterSource}</RiskPill>}
        {approval.rootBinary && <RiskPill tone="neutral">Root: {approval.rootBinary}</RiskPill>}
      </div>

      <p className="text-white text-lg font-medium leading-snug">Manual review required before execution</p>
      <p className="text-sm text-amber-100/80 mt-2">
        {approval.humanReason || 'Review the full approval object, then approve or deny it directly from the dashboard.'}
      </p>

      <div className="mt-6 rounded-2xl bg-black/25 border border-white/10 p-5">
        <p className="text-[10px] uppercase tracking-[0.24em] text-amber-200/60 mb-2">Command</p>
        <pre className="text-sm text-amber-50 whitespace-pre-wrap font-mono">{approval.commandPreview || approval.command || 'Unknown command'}</pre>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <ApprovalDetail title="Request ID" body={approval.id} />
        <ApprovalDetail title="Risk" body={approval.riskLevel || approval.level || 'medium'} />
        <ApprovalDetail title="Expires" body={approval.expiresAt || 'No expiry recorded'} />
        <ApprovalDetail title="Expected Effect" body={approval.dryRunSummary || 'No dry-run summary available.'} />
        <ApprovalDetail title="Rollback" body={approval.rollbackPath || 'No rollback path known.'} />
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

const ApprovalDetail = ({ title, body }: { title: string; body: string }) => (
  <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
    <p className="text-[10px] uppercase tracking-[0.18em] text-amber-200/50 mb-2">{title}</p>
    <p className="text-sm text-slate-100 break-words">{body}</p>
  </div>
);

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
        <p className="text-white font-medium">No active delegations.</p>
        <p className="text-sm text-slate-500 mt-2">
          Orchestrated worker tasks will appear here with status, context, and any failure details.
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

            {/* Definition of Done */}
            {baton.definition_of_done && baton.definition_of_done.length > 0 && (
              <DodChecklist items={baton.definition_of_done} completed={baton.status === 'completed'} />
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
  value,
}: {
  title: string;
  status: string;
  load: string;
  value?: string;
}) => (
  <div className="bg-[#16191f] p-8 rounded-3xl border border-white/[0.03] flex flex-col space-y-6">
    <div className="flex justify-between items-start">
      <h3 className="text-slate-500 text-xs font-bold uppercase tracking-widest">{title}</h3>
      <div className={`w-2 h-2 rounded-full ${status === 'healing' ? 'bg-amber-400 animate-pulse' : 'bg-cyan-500'}`} />
    </div>
    <div className="space-y-4">
      <p className="text-2xl font-medium text-white capitalize">{value || (status === 'healing' ? 'Healing' : 'Stable')}</p>
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

function commTone(status?: string): 'allow' | 'ask' | 'deny' | 'neutral' {
  if (!status) return 'neutral';
  const normalized = status.toLowerCase();
  if (normalized === 'approved' || normalized === 'sent' || normalized === 'ready') return 'allow';
  if (normalized === 'rejected' || normalized === 'failed' || normalized === 'cancelled') return 'deny';
  if (normalized === 'pending' || normalized === 'draft') return 'ask';
  return 'neutral';
}

const CommunicationBoard = ({ communications, onAction }: { communications: Communication[], onAction: (id: string, action: 'approve' | 'reject' | 'send') => void }) => {
  if (!communications || communications.length === 0) {
    return (
      <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 shadow-sm">
        <p className="text-sm text-slate-400">No communication drafts awaiting review.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {communications.map(comm => (
        <div key={comm.message_id} className="bg-[#16191f] p-6 rounded-3xl border border-white/[0.03] flex flex-col space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-sm font-medium text-white mb-1">To: {comm.recipient} <span className="text-slate-500 ml-2">({comm.channel})</span></h3>
              <p className="text-xs text-slate-400 font-semibold">{comm.subject}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <RiskPill tone={commTone(comm.approval_status)}>Approval: {comm.approval_status}</RiskPill>
              <RiskPill tone={commTone(comm.delivery_status)}>Delivery: {comm.delivery_status}</RiskPill>
            </div>
          </div>
          
          <div className="bg-[#0f1115] p-4 rounded-xl border border-white/[0.02]">
            <p className="text-sm text-slate-300 whitespace-pre-wrap font-mono text-xs">{comm.draft_content}</p>
          </div>

          <div className="flex justify-between items-center mt-2">
            <div className="text-xs text-slate-500">
              {comm.follow_up_required && <span className="mr-3 text-amber-500/80">Follow-up: {comm.follow_up_due || 'ASAP'}</span>}
              <span>Tone: {comm.tone_profile}</span>
            </div>
            
            <div className="flex gap-2">
              {comm.approval_status === 'pending' && (
                <>
                  <button onClick={() => onAction(comm.message_id, 'approve')} className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs rounded border border-emerald-500/20 transition-colors">
                    Approve
                  </button>
                  <button onClick={() => onAction(comm.message_id, 'reject')} className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs rounded border border-red-500/20 transition-colors">
                    Reject
                  </button>
                </>
              )}
              {comm.approval_status === 'approved' && comm.delivery_status === 'ready' && (
                <button onClick={() => onAction(comm.message_id, 'send')} className="px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs rounded border border-cyan-500/20 transition-colors">
                  Send Now
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// ── DodChecklist ─────────────────────────────────────────────────────────────
const DodChecklist = ({ items, completed = false }: { items: string[]; completed?: boolean }) => (
  <div className="rounded-2xl border border-cyan-500/10 bg-cyan-500/[0.03] p-4 space-y-2">
    <p className="text-[9px] uppercase tracking-widest text-cyan-700 flex items-center gap-1.5">
      <ClipboardList size={10} /> Definition of Done
    </p>
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2">
          <div className={`mt-0.5 w-3.5 h-3.5 rounded shrink-0 border flex items-center justify-center ${
            completed ? 'bg-emerald-500/30 border-emerald-500/40' : 'border-white/[0.12] bg-white/[0.02]'
          }`}>
            {completed && <span className="text-emerald-400 text-[8px] font-bold">✓</span>}
          </div>
          <span className={`text-xs leading-tight ${
            completed ? 'text-slate-500 line-through' : 'text-slate-300'
          }`}>{item}</span>
        </li>
      ))}
    </ul>
  </div>
);

function taskTone(status?: string, priority?: string): 'allow' | 'ask' | 'deny' | 'neutral' {
  if (status === 'completed' || status === 'archived') return 'allow';
  if (priority === 'urgent' || priority === 'high') return 'deny';
  if (status === 'pending' || status === 'escalated') return 'ask';
  return 'neutral';
}

function tierTone(tier?: string): 'allow' | 'ask' | 'deny' | 'neutral' {
  if (tier === 'critical') return 'deny';
  if (tier === 'high') return 'ask';
  if (tier === 'medium') return 'allow';
  return 'neutral';
}

const Top3Panel = ({ priorities }: { priorities: PriorityEngine | null }) => {
  if (!priorities) {
    return (
      <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 shadow-sm">
        <p className="text-sm text-slate-500">Calculating priorities from AJA Brain…</p>
      </div>
    );
  }

  const { top3, ignore_candidates, total_tasks } = priorities;

  if (top3.length === 0) {
    return (
      <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 shadow-sm">
        <p className="text-sm text-slate-400">No active tasks. You're clear for now.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Top 3 cards */}
      {top3.map((task, idx) => (
        <div
          key={task.task_id}
          className={`relative bg-[#16191f] rounded-3xl border p-6 space-y-4 transition-all hover:border-white/[0.08] overflow-hidden ${
            idx === 0
              ? 'border-cyan-500/20 shadow-[0_0_30px_rgba(6,182,212,0.04)]'
              : 'border-white/[0.03]'
          }`}
        >
          {/* Rank watermark */}
          <span className="absolute top-4 right-5 text-[56px] font-black text-white/[0.03] select-none leading-none">#{idx + 1}</span>

          {/* Header row */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {idx === 0 && <Zap size={14} className="text-amber-400 shrink-0" />}
                <h3 className="text-sm font-semibold text-white truncate">{task.title}</h3>
              </div>
              {task.description && (
                <p className="text-xs text-slate-500 line-clamp-1">{task.description}</p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              <RiskPill tone={tierTone(task.urgency_tier)}>{task.urgency_tier.toUpperCase()}</RiskPill>
              <span className="text-xs font-mono font-bold text-slate-300">{task.priority_score}/100</span>
            </div>
          </div>

          {/* Score breakdown bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-[10px] text-slate-600 uppercase tracking-widest">
              <span>Score Breakdown</span>
              <span className="text-slate-500 font-mono">{task.priority_score} pts</span>
            </div>
            <div className="flex gap-0.5 h-1.5 rounded-full overflow-hidden bg-white/[0.02]">
              {/* Urgency */}
              <div
                title={`Urgency: ${task.urgency_pts}pts`}
                className="h-full bg-red-500/70 transition-all"
                style={{ width: `${(task.urgency_pts / 40) * 40}%` }}
              />
              {/* Stakeholder */}
              <div
                title={`Stakeholder: ${task.stakeholder_pts}pts`}
                className="h-full bg-amber-400/70 transition-all"
                style={{ width: `${(task.stakeholder_pts / 30) * 30}%` }}
              />
              {/* Consequence */}
              <div
                title={`Consequence: ${task.consequence_pts}pts`}
                className="h-full bg-cyan-500/70 transition-all"
                style={{ width: `${(task.consequence_pts / 20) * 20}%` }}
              />
              {/* Intent */}
              <div
                title={`Intent: ${task.intent_pts}pts`}
                className="h-full bg-violet-500/70 transition-all"
                style={{ width: `${(task.intent_pts / 10) * 10}%` }}
              />
            </div>
            <div className="flex gap-3 text-[9px] text-slate-600">
              <span><span className="text-red-400">■</span> Urgency {task.urgency_pts}</span>
              <span><span className="text-amber-400">■</span> Stakeholder {task.stakeholder_pts}</span>
              <span><span className="text-cyan-400">■</span> Consequence {task.consequence_pts}</span>
              <span><span className="text-violet-400">■</span> Intent {task.intent_pts}</span>
            </div>
          </div>

          {/* Decision layer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-[#0f1115] rounded-2xl p-3 border border-white/[0.03]">
              <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-1">AJA Recommends</p>
              <p className="text-xs text-cyan-300 font-medium">{task.decision_recommendation}</p>
            </div>
            <div className="bg-[#0f1115] rounded-2xl p-3 border border-white/[0.03]">
              <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-1">Escalation</p>
              <p className="text-xs text-slate-300">{task.escalation_recommendation}</p>
            </div>
          </div>

          {/* Approval + days */}
          <div className="flex flex-wrap items-center gap-3 text-[11px]">
            <RiskPill tone="neutral">{task.approval_recommendation}</RiskPill>
            {task.days_until_due !== undefined && task.days_until_due !== null && (
              <span className={`font-mono ${
                task.days_until_due < 0 ? 'text-red-400' :
                task.days_until_due < 1 ? 'text-amber-400' : 'text-slate-500'
              }`}>
                {task.days_until_due < 0
                  ? `${Math.abs(task.days_until_due).toFixed(1)}d overdue`
                  : `${task.days_until_due.toFixed(1)}d left`}
              </span>
            )}
          </div>

          {/* Urgency challenge — anti-inflation message */}
          {task.urgency_challenge && (
            <div className="flex items-start gap-2 bg-violet-500/5 border border-violet-500/15 rounded-2xl p-3">
              <TrendingUp size={12} className="text-violet-400 mt-0.5 shrink-0" />
              <p className="text-xs text-violet-300/80 italic">{task.urgency_challenge}</p>
            </div>
          )}

          {/* Definition of Done — shown for all ranked tasks */}
          {task.definition_of_done && task.definition_of_done.length > 0 && (
            <DodChecklist items={task.definition_of_done} completed={false} />
          )}
        </div>
      ))}

      {/* Ignore candidates summary */}
      {ignore_candidates.length > 0 && (
        <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-5 flex gap-4 items-start">
          <Archive size={16} className="text-slate-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-xs font-medium text-slate-400 mb-2">
              {ignore_candidates.length} task{ignore_candidates.length !== 1 ? 's' : ''} safe to defer this week
            </p>
            <div className="flex flex-wrap gap-2">
              {ignore_candidates.slice(0, 5).map(t => (
                <span key={t.task_id} className="text-[10px] text-slate-600 bg-white/[0.02] border border-white/[0.04] rounded-full px-3 py-1">
                  {t.title}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <p className="text-[10px] text-slate-700 text-right">
        {total_tasks} tasks scored · Updated every 8s
      </p>
    </div>
  );
};

const TaskBoard = ({ tasks, onAction }: { tasks: Task[], onAction: (id: string, action: 'complete' | 'archive' | 'snooze' | 'escalate') => void }) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="bg-[#16191f] rounded-3xl border border-white/[0.03] p-8 shadow-sm">
        <p className="text-sm text-slate-400">No urgent tasks requiring attention.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tasks.map(task => (
        <div key={task.task_id} className="bg-[#16191f] p-6 rounded-3xl border border-white/[0.03] flex flex-col space-y-4 transition-all hover:border-white/[0.08]">
          <div className="flex justify-between items-start">
            <div className="flex flex-col">
              <h3 className="text-sm font-medium text-white mb-1 flex items-center gap-2">
                {task.title}
                {(task.urgency_score ?? 0) > 70 && (
                  <span className="flex items-center gap-1 bg-red-500/20 text-red-400 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                    <ShieldAlert size={10} /> Urgent
                  </span>
                )}
              </h3>
              {task.description && <p className="text-xs text-slate-400 mt-1">{task.description}</p>}
            </div>
            <div className="flex flex-col items-end gap-2">
              <RiskPill tone={taskTone(task.status, task.priority)}>Status: {task.status}</RiskPill>
              {task.delegated_worker_status && (
                 <RiskPill tone="neutral">Worker: {task.delegated_worker_status}</RiskPill>
              )}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-4 text-[11px] text-slate-500 bg-[#0f1115] p-3 rounded-xl border border-white/[0.02]">
            <div className="flex flex-col">
              <span className="uppercase tracking-wider font-semibold mb-0.5 text-slate-600">Due Date</span>
              <span className="text-slate-300">{task.due_date || 'No due date'}</span>
            </div>
            <div className="flex flex-col border-l border-white/[0.05] pl-4">
              <span className="uppercase tracking-wider font-semibold mb-0.5 text-slate-600">Priority</span>
              <span className={task.priority === 'urgent' ? 'text-red-400' : 'text-amber-400'}>{task.priority}</span>
            </div>
            <div className="flex flex-col border-l border-white/[0.05] pl-4">
              <span className="uppercase tracking-wider font-semibold mb-0.5 text-slate-600">Escalation</span>
              <span className="text-slate-300">Level {task.escalation_level || 0}</span>
            </div>
            {(task.follow_up_state || task.related_communication_id) && (
              <div className="flex flex-col border-l border-white/[0.05] pl-4">
                <span className="uppercase tracking-wider font-semibold mb-0.5 text-slate-600">Context</span>
                <span className="text-cyan-400">{task.follow_up_state || 'Comm Linked'}</span>
              </div>
            )}
          </div>

          {/* Definition of Done */}
          {task.definition_of_done && task.definition_of_done.length > 0 && (
            <DodChecklist items={task.definition_of_done} completed={task.status === 'completed'} />
          )}

          <div className="flex justify-end gap-2 mt-2">
            <button onClick={() => onAction(task.task_id, 'complete')} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs rounded border border-emerald-500/20 transition-colors">
              <CheckCircle size={14} /> Complete
            </button>
            <button onClick={() => onAction(task.task_id, 'snooze')} className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs rounded border border-amber-500/20 transition-colors">
              <Clock size={14} /> Snooze
            </button>
            <button onClick={() => onAction(task.task_id, 'escalate')} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs rounded border border-red-500/20 transition-colors">
              <ArrowUpRight size={14} /> Escalate
            </button>
            <button onClick={() => onAction(task.task_id, 'archive')} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-500/10 hover:bg-slate-500/20 text-slate-400 text-xs rounded border border-slate-500/20 transition-colors">
              <Archive size={14} /> Archive
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Dashboard;
