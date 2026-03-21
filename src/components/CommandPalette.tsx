"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useReactFlow } from '@xyflow/react';
import {
  Search, User, Layers, Briefcase, GraduationCap, Code,
  Download, Mail, ExternalLink, Command
} from 'lucide-react';

interface CommandItem {
  id: string;
  label: string;
  hint?: string;
  icon: React.ReactNode;
  color: string;
  action: () => void;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPalette({ isOpen, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { setCenter, getNode } = useReactFlow();

  const focusNode = useCallback((nodeId: string) => {
    const node = getNode(nodeId);
    if (!node) return;
    const w = (node.measured?.width ?? 300) / 2;
    const h = (node.measured?.height ?? 120) / 2;
    setCenter(node.position.x + w, node.position.y + h, { duration: 750, zoom: 1.25 });
    onClose();
  }, [getNode, setCenter, onClose]);

  const commands: CommandItem[] = [
    { id: 'profile', label: 'Go to Profile', hint: 'About me', icon: <User size={14} />, color: '#a78bfa', action: () => focusNode('profile') },
    { id: 'proj-1',  label: 'FlashMind – AI Study Platform', hint: 'Project', icon: <Layers size={14} />, color: '#00d4ff', action: () => focusNode('proj-1') },
    { id: 'proj-2',  label: 'Code Sync – Collaborative Editor', hint: 'Project', icon: <Layers size={14} />, color: '#a78bfa', action: () => focusNode('proj-2') },
    { id: 'proj-3',  label: 'Billing Expo – Invoice Generator', hint: 'Project', icon: <Layers size={14} />, color: '#f59e0b', action: () => focusNode('proj-3') },
    { id: 'exp-1',   label: 'Teleperformance', hint: 'Experience', icon: <Briefcase size={14} />, color: '#f59e0b', action: () => focusNode('exp-1') },
    { id: 'exp-2',   label: 'PinnacleWorks Executive', hint: 'Experience', icon: <Briefcase size={14} />, color: '#f59e0b', action: () => focusNode('exp-2') },
    { id: 'edu-1',   label: 'B.Tech IT – PIET', hint: 'Education', icon: <GraduationCap size={14} />, color: '#34d399', action: () => focusNode('edu-1') },
    { id: 'skills',  label: 'Technical Skills – Languages', hint: 'Skills', icon: <Code size={14} />, color: '#00d4ff', action: () => focusNode('skill-langs') },
    {
      id: 'email', label: 'Send Email', hint: 'satyendra9173@gmail.com', icon: <Mail size={14} />, color: '#00d4ff',
      action: () => { window.location.href = 'mailto:satyendra9173@gmail.com'; onClose(); },
    },
  ];

  const filtered = query
    ? commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()) || (c.hint || '').toLowerCase().includes(query.toLowerCase()))
    : commands;

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => (i + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => (i - 1 + filtered.length) % filtered.length);
    } else if (e.key === 'Enter' && filtered[activeIndex]) {
      filtered[activeIndex].action();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-overlay" onClick={onClose}>
      <div className="command-palette" onClick={e => e.stopPropagation()}>
        {/* Search input */}
        <div style={{ display: 'flex', alignItems: 'center', padding: '0 16px', gap: '10px' }}>
          <Search size={16} color="#3a4a68" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search nodes, actions, links..."
            style={{ padding: '16px 0' }}
          />
          <span className="kbd">Esc</span>
        </div>

        {/* Results */}
        <div style={{ maxHeight: '300px', overflowY: 'auto', padding: '6px 0' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', fontSize: '13px', color: '#3a4a68' }}>
              No results found
            </div>
          ) : (
            filtered.map((cmd, i) => (
              <button
                key={cmd.id}
                className={`command-item ${i === activeIndex ? 'active' : ''}`}
                onClick={cmd.action}
                onMouseEnter={() => setActiveIndex(i)}
              >
                <div style={{
                  width: '28px', height: '28px', borderRadius: '6px',
                  background: `${cmd.color}12`, border: `1px solid ${cmd.color}25`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: cmd.color, flexShrink: 0,
                }}>{cmd.icon}</div>
                <span className="command-label">{cmd.label}</span>
                {cmd.hint && <span className="command-hint">{cmd.hint}</span>}
              </button>
            ))
          )}
        </div>

        {/* Footer hint */}
        <div style={{
          padding: '10px 16px',
          borderTop: '1px solid rgba(255,255,255,0.04)',
          display: 'flex', alignItems: 'center', gap: '12px',
          fontSize: '11px', color: '#2a3a58',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span className="kbd">↑↓</span> navigate
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span className="kbd">↵</span> select
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span className="kbd">esc</span> close
          </span>
        </div>
      </div>
    </div>
  );
}
