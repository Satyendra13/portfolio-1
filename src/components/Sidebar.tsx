"use client";

import React, { useState } from 'react';
import { ChevronDown, Code, Server, Briefcase, GraduationCap, Layers, User, Download, Command, X, Menu, Mail, Phone } from 'lucide-react';
import { useReactFlow } from '@xyflow/react';

const SECTIONS = [
  {
    id: 1,
    title: 'Profile',
    icon: <User size={14} />,
    color: '#a78bfa',
    items: [
      { name: 'About Satyendra', nodeId: 'profile', sub: 'Software Developer' },
    ],
  },
  {
    id: 2,
    title: 'Projects',
    icon: <Layers size={14} />,
    color: '#00d4ff',
    items: [
      { name: 'FlashMind', nodeId: 'proj-1', sub: 'AI Study Platform' },
      { name: 'Code Sync', nodeId: 'proj-2', sub: 'Collaborative Editor' },
      { name: 'Billing Expo', nodeId: 'proj-3', sub: 'Invoice Generator' },
    ],
  },
  {
    id: 3,
    title: 'Experience',
    icon: <Briefcase size={14} />,
    color: '#f59e0b',
    items: [
      { name: 'Teleperformance', nodeId: 'exp-1', sub: 'Oct 2024 – Present' },
      { name: 'PinnacleWorks Exec', nodeId: 'exp-2', sub: 'Oct 2023 – Oct 2024' },
      { name: 'PinnacleWorks Intern', nodeId: 'exp-3', sub: 'July – Oct 2023' },
      { name: 'Cyber Flow', nodeId: 'exp-4', sub: 'Sept – Dec 2021' },
    ],
  },
  {
    id: 4,
    title: 'Education',
    icon: <GraduationCap size={14} />,
    color: '#34d399',
    items: [
      { name: 'B.Tech IT – PIET', nodeId: 'edu-1', sub: '2019 – 2023 · 76%' },
      { name: 'Higher Secondary', nodeId: 'edu-2', sub: '2017 – 2019 · 73.2%' },
      { name: 'Secondary – NVS', nodeId: 'edu-3', sub: '2016 – 2017 · CGPA 8.6' },
    ],
  },
  {
    id: 5,
    title: 'Technical Skills',
    icon: <Code size={14} />,
    color: '#00d4ff',
    items: [
      { name: 'Languages', nodeId: 'skill-langs', sub: 'JS · Python · PHP · SQL' },
      { name: 'Frameworks & Libs', nodeId: 'skill-frameworks', sub: 'React · Next · Laravel' },
      { name: 'Databases & DevOps', nodeId: 'skill-tools', sub: 'MongoDB · Docker · MySQL' },
    ],
  },
];

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
  onOpenCommand?: () => void;
}

export default function Sidebar({ collapsed, onToggle, onOpenCommand }: SidebarProps) {
  const [expanded, setExpanded] = useState<number | null>(1);
  const { setCenter, getNode } = useReactFlow();

  const focusNode = (nodeId: string) => {
    const node = getNode(nodeId);
    if (!node) return;
    const w = (node.measured?.width ?? 300) / 2;
    const h = (node.measured?.height ?? 120) / 2;
    setCenter(node.position.x + w, node.position.y + h, { duration: 750, zoom: 1.25 });
  };

  return (
    <aside style={{
      width: collapsed ? '0px' : '290px',
      minWidth: collapsed ? '0px' : '290px',
      backgroundColor: 'var(--sidebar-bg)',
      borderRight: collapsed ? 'none' : '1px solid var(--border-color)',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      overflowX: 'hidden',
      flexShrink: 0,
      transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      position: 'relative',
    }}>
      {/* Brand header */}
      <div style={{
        padding: '20px 20px 16px',
        borderBottom: '1px solid var(--border-color)',
        background: 'linear-gradient(135deg, rgba(167,139,250,0.06) 0%, rgba(0,212,255,0.03) 100%)',
        flexShrink: 0,
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'end',
          marginBottom: '10px',
        }}>
          {onToggle && (
            <button
              onClick={onToggle}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#3a4a68', padding: '2px', display: 'flex',
                transition: 'color 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.color = '#6b7fa8'}
              onMouseLeave={e => e.currentTarget.style.color = '#3a4a68'}
            >
              <X size={14} />
            </button>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '44px', height: '44px', borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(167,139,250,0.12))',
            border: '1.5px solid rgba(167,139,250,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px', fontWeight: 900, color: '#a78bfa',
            boxShadow: '0 4px 15px rgba(167,139,250,0.08)',
          }}>SK</div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#dce7f7' }}>Satyendra Kumar</div>
            <div style={{ fontSize: '11px', color: '#4a5a7a', marginTop: '2px' }}>Software Developer</div>
          </div>
        </div>

        {/* Status pill */}
        <div style={{
          marginTop: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px',
          padding: '4px 10px', borderRadius: '20px',
          background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.25)',
          fontSize: '10px', fontWeight: 600, color: '#34d399',
        }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%', background: '#34d399',
            animation: 'pulse-dot 2s infinite',
          }} />
          Available for opportunities
        </div>
      </div>

      {/* Search shortcut */}
      {onOpenCommand && (
        <button
          onClick={onOpenCommand}
          style={{
            margin: '10px 12px 4px',
            padding: '8px 12px',
            display: 'flex', alignItems: 'center', gap: '8px',
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.15s',
            flexShrink: 0,
            fontFamily: 'var(--font-sans)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(167,139,250,0.06)';
            e.currentTarget.style.borderColor = 'rgba(167,139,250,0.2)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';
          }}
        >
          <Command size={12} color="#3a4a68" />
          <span style={{ fontSize: '12px', color: '#3a4a68', flex: 1, textAlign: 'left' }}>Quick navigate…</span>
          <span className="kbd" style={{ fontSize: '9px' }}>Ctrl+K</span>
        </button>
      )}

      {/* Navigation sections */}
      <nav style={{ flex: 1, padding: '4px 0', overflowY: 'auto' }}>
        {SECTIONS.map((section) => (
          <div key={section.id}>
            {/* Section header */}
            <button
              onClick={() => setExpanded(expanded === section.id ? null : section.id)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center',
                padding: '11px 18px', gap: '10px',
                background: expanded === section.id ? `${section.color}0a` : 'transparent',
                border: 'none', cursor: 'pointer',
                borderLeft: expanded === section.id ? `2px solid ${section.color}` : '2px solid transparent',
                transition: 'all 0.18s',
                fontFamily: 'var(--font-sans)',
              }}
            >
              <div style={{ color: section.color, opacity: 0.8 }}>{section.icon}</div>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#c8d5ed', flex: 1, textAlign: 'left' }}>
                {section.title}
              </span>
              <span style={{
                fontSize: '10px', fontWeight: 600, color: '#2a3a58',
                background: 'rgba(255,255,255,0.03)',
                padding: '1px 6px', borderRadius: '10px',
                marginRight: '4px',
              }}>
                {section.items.length}
              </span>
              <ChevronDown
                size={12}
                color="#3a4a68"
                style={{
                  transform: expanded === section.id ? 'rotate(180deg)' : 'rotate(0)',
                  transition: 'transform 0.2s',
                }}
              />
            </button>

            {/* Items */}
            {expanded === section.id && (
              <div style={{
                paddingBottom: '4px',
                animation: 'fadeSlideDown 0.2s ease both',
              }}>
                {section.items.map((item) => (
                  <button
                    key={item.nodeId}
                    onClick={() => focusNode(item.nodeId)}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center',
                      padding: '8px 18px 8px 40px',
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      gap: '10px', textAlign: 'left',
                      transition: 'all 0.15s',
                      fontFamily: 'var(--font-sans)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = `${section.color}0d`;
                      e.currentTarget.style.paddingLeft = '44px';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.paddingLeft = '40px';
                    }}
                  >
                    <div style={{
                      width: '5px', height: '5px', borderRadius: '50%', flexShrink: 0,
                      background: section.color, opacity: 0.5,
                      transition: 'opacity 0.15s',
                    }} />
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 500, color: '#8a9bbf' }}>{item.name}</div>
                      {item.sub && (
                        <div style={{ fontSize: '10px', color: '#3a4a68', marginTop: '1px' }}>{item.sub}</div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border-color)',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}>
        {/* Download Resume */}
        <a href="/Satyendra_Kumar_Resume.pdf" download="Satyendra_Kumar_Resume.pdf" style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
          padding: '8px 12px', borderRadius: '8px',
          background: 'linear-gradient(135deg, rgba(167,139,250,0.08), rgba(0,212,255,0.08))',
          border: '1px solid rgba(167,139,250,0.2)',
          fontSize: '11px', fontWeight: 600, color: '#a78bfa',
          textDecoration: 'none', cursor: 'pointer', transition: 'all 0.15s',
        }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(167,139,250,0.15), rgba(0,212,255,0.15))';
            e.currentTarget.style.borderColor = 'rgba(167,139,250,0.35)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(167,139,250,0.08), rgba(0,212,255,0.08))';
            e.currentTarget.style.borderColor = 'rgba(167,139,250,0.2)';
          }}
        >
          <Download size={12} /> Download Resume
        </a>
        {/* Contact row */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <a href="mailto:satyendra9173@gmail.com" style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px',
            padding: '6px', borderRadius: '6px',
            background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.15)',
            fontSize: '10px', fontWeight: 600, color: '#00d4ff',
            textDecoration: 'none', cursor: 'pointer', transition: 'all 0.15s',
          }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,212,255,0.12)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(0,212,255,0.06)'}
          >
            <Mail size={10} /> Email
          </a>
          <a href="tel:+919128649473" style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px',
            padding: '6px', borderRadius: '6px',
            background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.15)',
            fontSize: '10px', fontWeight: 600, color: '#34d399',
            textDecoration: 'none', cursor: 'pointer', transition: 'all 0.15s',
          }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(52,211,153,0.12)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(52,211,153,0.06)'}
          >
            <Phone size={10} /> Call
          </a>
        </div>
        <div style={{
          fontSize: '10px', color: '#1e2a42', textAlign: 'center',
          letterSpacing: '0.3px',
        }}>
          Built with Next.js &amp; React Flow
        </div>
      </div>
    </aside>
  );
}
