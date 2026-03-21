"use client";

import React, { useCallback, useState, useEffect } from 'react';
import DetailPanel from './DetailPanel';
import CommandPalette from './CommandPalette';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
  Controls,
  ConnectionLineType,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ProjectNode, ProfileNode, SkillNode, ExperienceNode } from './CustomNodes';
import { Menu, Command, Maximize2 } from 'lucide-react';

const nodeTypes = {
  project:    ProjectNode,
  profile:    ProfileNode,
  skill:      SkillNode,
  experience: ExperienceNode,
};

// ─── Nodes ────────────────────────────────────────────────────
/*
 * ──────────────────────────────────────────────────────────────
 *  LAYOUT REFERENCE (all values in px)
 *
 *  Node widths:   Profile 520  |  Project 310  |  Exp/Edu 310  |  Skill 290
 *  Est. heights:  Profile ~330 |  Project ~250 |  Exp/Edu ~130 |  Skill ~160
 *
 *          ┌──proj-1──┐       ┌──proj-2──┐       ┌──proj-3──┐
 *          │  310×250 │       │  310×250 │       │  310×250 │     y = 0
 *          x=150              x=610              x=1070
 *
 *                             ┌───profile────┐                    y = 400
 *                             │   520 × 330  │
 *                             x=505
 *
 *  ┌──edu-1──┐                ┌──exp-1──┐          ┌─skill-langs─┐
 *  │  310×130│                │  310×130│          │  290 × 120  │  y = 850
 *  x=0                        x=610                x=1220
 *
 *  ┌──edu-2──┐                ┌──exp-2──┐          ┌─skill-fw────┐
 *  y=1050                     y=1050               y=1070
 *
 *  ┌──edu-3──┐                ┌──exp-3──┐          ┌─skill-tools─┐
 *  y=1250                     y=1250               y=1290
 *
 *                             ┌──exp-4──┐
 *                             y=1450
 * ──────────────────────────────────────────────────────────────
 */

const initialNodes: any[] = [

  // ── PROFILE (centre) ────────────────────────────────────────
  {
    id: 'profile',
    type: 'profile',
    position: { x: 505, y: 400 },
    data: {
      description:
        'Designing and shipping scalable full-stack products powered by React, Node.js and AI. ' +
        'Experienced in microservices, real-time collaboration, and cloud deployments — ' +
        'turning complex requirements into clean, performant solutions.',
    },
  },

  // ── PROJECTS (top row) ───────────────────────────────
  {
    id: 'proj-1',
    type: 'project',
    position: { x: 150, y: 0 },
    data: {
      id: 'proj-1',
      category: 'AI · FULL-STACK',
      title: 'FlashMind – AI Study Platform',
      color: '#00d4ff',
      desc: 'AI-powered notes, flashcards & quizzes with multi-language support (EN/HI).',
      stack: ['ReactJS', 'NodeJS', 'MongoDB', 'Gemini AI', 'Docker', 'Microservices'],
    },
  },
  {
    id: 'proj-2',
    type: 'project',
    position: { x: 610, y: 0 },
    data: {
      id: 'proj-2',
      category: 'REAL-TIME · COLLAB',
      title: 'Code Sync – Collaborative Editor',
      color: '#a78bfa',
      desc: 'Real-time multi-user code editor with unique room IDs and live WebSocket sync.',
      stack: ['ReactJS', 'Socket.IO', 'NodeJS', 'ExpressJS'],
    },
  },
  {
    id: 'proj-3',
    type: 'project',
    position: { x: 1070, y: 0 },
    data: {
      id: 'proj-3',
      category: 'WEB APP',
      title: 'Billing Expo – Invoice Generator',
      color: '#f59e0b',
      desc: 'React invoice app with tax/discount automation, itemisation & print support.',
      stack: ['React', 'JavaScript'],
    },
  },

  // ── EDUCATION (left branch) ──────────────────────────
  {
    id: 'edu-1',
    type: 'experience',
    position: { x: 0, y: 850 },
    data: {
      isEducation: true,
      title: 'B.Tech – Information Technology',
      company: 'Panipat Institute of Engg. & Technology',
      duration: '2019 – 2023',
      grade: '76%',
      highlight: 'Core CS, Data Structures, Web Dev, DBMS',
    },
  },
  {
    id: 'edu-2',
    type: 'experience',
    position: { x: 0, y: 1050 },
    data: {
      isEducation: true,
      title: 'Higher Secondary School',
      company: 'B S S C College, Udakishunganj (BSEB)',
      duration: '2017 – 2019',
      grade: '73.2%',
    },
  },
  {
    id: 'edu-3',
    type: 'experience',
    position: { x: 0, y: 1250 },
    data: {
      isEducation: true,
      title: 'Secondary School',
      company: 'Jawahar Navodaya Vidyalaya, Madhepura (CBSE)',
      duration: '2016 – 2017',
      grade: 'CGPA 8.6',
    },
  },

  // ── EXPERIENCE (centre‐bottom branch) ──────────────
  {
    id: 'exp-1',
    type: 'experience',
    position: { x: 610, y: 850 },
    data: {
      title: 'Software Developer',
      company: 'Teleperformance',
      duration: 'Oct 2024 – Present',
      highlight: 'React/Next.js dashboards · Node.js & MySQL · Docker microservices',
    },
  },
  {
    id: 'exp-2',
    type: 'experience',
    position: { x: 610, y: 1050 },
    data: {
      title: 'Software Development Executive',
      company: 'PinnacleWorks Infotech Pvt. Ltd.',
      duration: 'Oct 2023 – Oct 2024',
      highlight: 'Laravel & MongoDB — 80% QA reduction · Nginx performance tuning',
    },
  },
  {
    id: 'exp-3',
    type: 'experience',
    position: { x: 610, y: 1250 },
    data: {
      title: 'Software Development Intern',
      company: 'PinnacleWorks Infotech Pvt. Ltd.',
      duration: 'July 2023 – Oct 2023',
      highlight: 'PHP/Laravel · MongoDB · JavaScript frontend',
    },
  },
  {
    id: 'exp-4',
    type: 'experience',
    position: { x: 610, y: 1450 },
    data: {
      title: 'Frontend Developer Intern',
      company: 'Cyber Flow',
      duration: 'Sept 2021 – Dec 2021',
      highlight: 'HTML · CSS · JavaScript · UI development',
    },
  },

  // ── SKILLS (right branch) ──────────────────────────
  {
    id: 'skill-langs',
    type: 'skill',
    position: { x: 1220, y: 850 },
    data: {
      iconKey: 'langs',
      color: '#00d4ff',
      title: 'Languages',
      subtitle: 'Core programming languages',
      skills: ['JavaScript', 'Python', 'PHP', 'SQL'],
    },
  },
  {
    id: 'skill-frameworks',
    type: 'skill',
    position: { x: 1220, y: 1070 },
    data: {
      iconKey: 'tech',
      color: '#a78bfa',
      title: 'Frameworks & Libraries',
      subtitle: 'Frontend, backend & APIs',
      skills: ['ReactJS', 'NextJS', 'Node.js', 'Express', 'Laravel', 'Socket.IO', 'AI API Integration'],
    },
  },
  {
    id: 'skill-tools',
    type: 'skill',
    position: { x: 1220, y: 1290 },
    data: {
      iconKey: 'tech',
      color: '#34d399',
      title: 'Databases & DevOps',
      subtitle: 'Data & infrastructure tools',
      skills: ['MongoDB', 'MySQL', 'PostgreSQL', 'Docker', 'Microservices', 'Git & GitHub', 'VS Code', 'Postman'],
    },
  },
];

// Source/target just use default handles except for profile which has named handles
const edge = (
  id: string, source: string, target: string,
  color: string,
  opts: any = {}
) => ({
  id, source, target,
  animated: true,
  type: 'smoothstep',
  style: { stroke: color, strokeWidth: 2 },
  markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color },
  ...opts,
});

const initialEdges: any[] = [
  // Profile → Projects (from top of profile to bottom of projects)
  edge('ep1', 'profile', 'proj-1', '#00d4ff', { sourceHandle: 'top' }),
  edge('ep2', 'profile', 'proj-2', '#a78bfa', { sourceHandle: 'top' }),
  edge('ep3', 'profile', 'proj-3', '#f59e0b', { sourceHandle: 'top' }),

  // Profile → Education (from left of profile)
  edge('ee0', 'profile', 'edu-1',  '#34d399', { sourceHandle: 'left' }),
  edge('ee1', 'edu-1',   'edu-2',  '#34d399'),
  edge('ee2', 'edu-2',   'edu-3',  '#34d399',  { style: { stroke: '#34d39977', strokeWidth: 1.5 } }),

  // Profile → Experience (from bottom of profile)
  edge('ex0', 'profile', 'exp-1', '#f59e0b', { sourceHandle: 'bottom' }),
  edge('ex1', 'exp-1',   'exp-2', '#f59e0b'),
  edge('ex2', 'exp-2',   'exp-3', '#f59e0b', { style: { stroke: '#f59e0b88', strokeWidth: 1.5 } }),
  edge('ex3', 'exp-3',   'exp-4', '#f59e0b', { style: { stroke: '#f59e0b55', strokeWidth: 1.2 } }),

  // Profile → Skills (from right of profile)
  edge('es0', 'profile',          'skill-langs',       '#00d4ff', { sourceHandle: 'right' }),
  edge('es1', 'skill-langs',      'skill-frameworks',  '#a78bfa', { sourceHandle: 'bottom', targetHandle: 'top' }),
  edge('es2', 'skill-frameworks', 'skill-tools',       '#34d399', { sourceHandle: 'bottom', targetHandle: 'top' }),
];

// ─── Component ────────────────────────────────────────────────
interface RoadmapFlowProps {
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export default function RoadmapFlow({ sidebarCollapsed, onToggleSidebar }: RoadmapFlowProps) {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [commandOpen, setCommandOpen] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const onNodeClick = useCallback((_e: React.MouseEvent, node: any) => {
    setSelectedNode(node);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setCommandOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isDev =
    process.env.NODE_ENV === 'development' ||
    process.env.NEXT_PUBLIC_NODE_ENV === 'development' ||
    process.env.NEXT_PUBLIC_NODE_ENV === 'dev';

  return (
    <div style={{ flex: 1, height: '100vh', background: 'var(--background)', position: 'relative' }}>
      {/* Ambient background orbs */}
      <div className="ambient-orb" style={{
        width: '500px', height: '500px',
        background: 'radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)',
        top: '-100px', right: '-100px',
        animation: 'orbFloat1 15s ease-in-out infinite',
      }} />
      <div className="ambient-orb" style={{
        width: '400px', height: '400px',
        background: 'radial-gradient(circle, rgba(167,139,250,0.04) 0%, transparent 70%)',
        bottom: '-50px', left: '20%',
        animation: 'orbFloat2 18s ease-in-out infinite',
      }} />

      {/* Sidebar toggle (visible when sidebar is collapsed or on tablet) */}
      {(sidebarCollapsed || !onToggleSidebar) && onToggleSidebar && (
        <button
          onClick={onToggleSidebar}
          style={{
            position: 'absolute', top: '16px', left: '16px', zIndex: 100,
            width: '38px', height: '38px', borderRadius: '10px',
            background: 'rgba(12,16,28,0.9)', border: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', color: 'var(--foreground-dim)',
            transition: 'all 0.15s',
            backdropFilter: 'blur(12px)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(167,139,250,0.1)';
            e.currentTarget.style.borderColor = 'rgba(167,139,250,0.3)';
            e.currentTarget.style.color = '#a78bfa';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(12,16,28,0.9)';
            e.currentTarget.style.borderColor = 'var(--border-color)';
            e.currentTarget.style.color = 'var(--foreground-dim)';
          }}
        >
          <Menu size={16} />
        </button>
      )}

      {/* Keyboard shortcut hint */}
      <div style={{
        position: 'absolute', bottom: '16px', left: '16px', zIndex: 50,
        display: 'flex', alignItems: 'center', gap: '6px',
        padding: '6px 12px', borderRadius: '8px',
        background: 'rgba(12,16,28,0.8)', border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(12px)',
        fontSize: '11px', color: '#3a4a68',
        animation: 'fadeIn 1s ease 1s both',
      }}>
        <Command size={11} />
        Press <span className="kbd" style={{ margin: '0 2px' }}>Ctrl+K</span> to navigate
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        minZoom={0.15}
        maxZoom={2}
        nodesDraggable={isDev}
        nodesConnectable={isDev}
        elementsSelectable
        panOnScroll
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
      >
        <Background color="#1a2035" gap={28} size={1} />
        <Controls />
      </ReactFlow>

      {selectedNode && (
        <DetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}

      <CommandPalette isOpen={commandOpen} onClose={() => setCommandOpen(false)} />
    </div>
  );
}
