import React from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  Briefcase, Code, Server, ExternalLink,
  GraduationCap, Mail, Phone, MapPin, Github, Linkedin,
  Sparkles, ArrowUpRight
} from 'lucide-react';

// ─── Shared pill tag ─────────────────────────────────────────
function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '4px 12px',
      borderRadius: '20px',
      fontSize: '11px',
      fontWeight: 700,
      background: `${color}18`,
      border: `1px solid ${color}44`,
      color,
      whiteSpace: 'nowrap',
      transition: 'all 0.2s',
    }}>{label}</span>
  );
}

// ─── Profile Node (Hero) ─────────────────────────────────────
export function ProfileNode({ data }: { data: any }) {
  return (
    <div style={{
      width: '520px',
      background: 'linear-gradient(180deg, #0c1018 0%, #0a0e18 100%)',
      borderRadius: '18px',
      border: '1px solid rgba(167,139,250,0.35)',
      boxShadow: '0 8px 40px rgba(0,0,0,0.6), 0 0 60px rgba(167,139,250,0.06)',
      fontFamily: "'Inter', -apple-system, sans-serif",
      overflow: 'hidden',
    }}>
      {/* Rainbow top bar */}
      <div style={{
        height: '4px',
        background: 'linear-gradient(90deg, #00d4ff 0%, #a78bfa 35%, #f59e0b 65%, #34d399 100%)',
        backgroundSize: '200% 100%',
        animation: 'gradientFlow 4s ease infinite',
      }} />

      <div style={{ padding: '22px 24px 20px' }}>
        {/* Header: avatar + name */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', marginBottom: '16px' }}>
          {/* "SK" avatar */}
          <div style={{
            width: '68px', height: '68px', borderRadius: '16px', flexShrink: 0,
            background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(167,139,250,0.12))',
            border: '1.5px solid rgba(167,139,250,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '22px', fontWeight: 900, color: '#a78bfa',
            letterSpacing: '-1px',
            boxShadow: '0 4px 20px rgba(167,139,250,0.1)',
            animation: 'float 6s ease-in-out infinite',
          }}>SK</div>

          <div style={{ flex: 1 }}>
            <div style={{
              fontSize: '24px', fontWeight: 900, lineHeight: 1.15, marginBottom: '4px',
              background: 'linear-gradient(135deg, #dce7f7 0%, #a78bfa 100%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Satyendra Kumar
            </div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#a78bfa', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={13} />
              Software Developer &nbsp;·&nbsp; Full-Stack &amp; AI Integration
            </div>
            <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#4a5a7a' }}>
                <MapPin size={11} /> Gurugram, Haryana
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#4a5a7a' }}>
                <Mail size={11} /> satyendra9173@gmail.com
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <p style={{ fontSize: '14px', color: '#6a7e9e', lineHeight: '1.65', margin: '0 0 16px' }}>
          {data.description || 'Full-stack Software Developer building scalable AI-integrated web applications.'}
        </p>

        {/* Stats row */}
        <div style={{
          display: 'flex', gap: '0', marginBottom: '14px',
          borderRadius: '10px', overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.05)',
        }}>
          {[
            { value: '2.5+', label: 'yrs exp', color: '#00d4ff' },
            { value: '4', label: 'projects', color: '#a78bfa' },
            { value: '2', label: 'companies', color: '#f59e0b' },
            { value: '10+', label: 'technologies', color: '#34d399' },
          ].map((stat, i) => (
            <div key={i} style={{
              flex: 1, textAlign: 'center', padding: '8px 4px',
              background: 'rgba(255,255,255,0.02)',
              borderRight: i < 3 ? '1px solid rgba(255,255,255,0.04)' : 'none',
            }}>
              <div style={{ fontSize: '16px', fontWeight: 800, color: stat.color, lineHeight: 1 }}>{stat.value}</div>
              <div style={{ fontSize: '9px', fontWeight: 600, color: '#4a5a7a', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: '4px' }}>{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Skill chips */}
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginBottom: '14px' }}>
          {['React/Next.js', 'Node.js', 'AI Integration', 'Microservices', 'Docker', 'MongoDB'].map(t => (
            <Pill key={t} label={t} color="#00d4ff" />
          ))}
        </div>

        {/* Contact badges */}
        <div style={{ display: 'flex', gap: '7px', flexWrap: 'wrap' }}>
          {[
            { icon: <Github size={12} />, label: 'GitHub', color: '#a78bfa' },
            { icon: <Linkedin size={12} />, label: 'LinkedIn', color: '#00d4ff' },
            { icon: <Phone size={12} />, label: '+91-9128649473', color: '#34d399' },
          ].map(({ icon, label, color }) => (
            <div key={label} style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '5px 11px', borderRadius: '8px',
              background: `${color}12`, border: `1px solid ${color}35`,
              fontSize: '10px', fontWeight: 600, color, cursor: 'pointer',
              transition: 'all 0.2s',
            }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = `${color}22`;
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = `${color}12`;
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >{icon} {label}</div>
          ))}
        </div>
      </div>

      {/* Handles — all sides */}
      <Handle type="source" position={Position.Top} id="top" style={{ background: '#a78bfa', width: 8, height: 8, border: '2px solid #060810' }} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#f59e0b', width: 8, height: 8, border: '2px solid #060810' }} />
      <Handle type="source" position={Position.Left} id="left" style={{ background: '#34d399', width: 8, height: 8, border: '2px solid #060810' }} />
      <Handle type="source" position={Position.Right} id="right" style={{ background: '#00d4ff', width: 8, height: 8, border: '2px solid #060810' }} />
    </div>
  );
}

// ─── Project Node ────────────────────────────────────────────
export function ProjectNode({ data }: { data: any }) {
  const color = data.color || '#00d4ff';
  return (
    <div style={{
      width: '340px',
      background: 'linear-gradient(180deg, #0c1018 0%, #0a0e18 100%)',
      borderRadius: '14px',
      border: `1px solid ${color}44`,
      boxShadow: `0 6px 28px rgba(0,0,0,0.5), 0 0 40px ${color}06`,
      fontFamily: "'Inter', -apple-system, sans-serif",
      overflow: 'hidden',
      transition: 'box-shadow 0.3s ease',
    }}>
      {/* Coloured banner */}
      <div style={{
        height: '95px',
        background: `linear-gradient(135deg, ${color}25 0%, ${color}08 100%)`,
        borderBottom: `1px solid ${color}25`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Grid pattern overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `linear-gradient(${color}12 1px, transparent 1px), linear-gradient(90deg, ${color}12 1px, transparent 1px)`,
          backgroundSize: '20px 20px',
        }} />
        {/* Gradient orb */}
        <div style={{
          position: 'absolute', width: '120px', height: '120px', borderRadius: '50%',
          background: `radial-gradient(circle, ${color}15 0%, transparent 70%)`,
          top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          filter: 'blur(20px)',
        }} />
        <div style={{
          width: '50px', height: '50px', borderRadius: '13px',
          background: `${color}22`, border: `1.5px solid ${color}55`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1,
          boxShadow: `0 4px 15px ${color}15`,
        }}>
          <ExternalLink color={color} size={22} />
        </div>

        {/* Category label */}
        <div style={{
          position: 'absolute', top: 10, left: 12,
          fontSize: '8px', fontWeight: 800, letterSpacing: '1.5px',
          color: color, textTransform: 'uppercase',
        }}>{data.category}</div>

        {/* Arrow link */}
        <div style={{
          position: 'absolute', top: 10, right: 12,
          width: '24px', height: '24px', borderRadius: '6px',
          background: `${color}15`, border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', transition: 'all 0.2s',
        }}>
          <ArrowUpRight size={12} color={color} />
        </div>
      </div>

      <div style={{ padding: '16px 18px 18px' }}>
        <div style={{ fontSize: '16px', fontWeight: 700, color: '#dce7f7', marginBottom: '8px', lineHeight: 1.35 }}>
          {data.title}
        </div>
        <p style={{ fontSize: '13px', color: '#6a7e9e', lineHeight: '1.65', margin: '0 0 14px' }}>
          {data.desc}
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {(data.stack || []).map((s: string) => <Pill key={s} label={s} color={color} />)}
        </div>
      </div>

      <Handle type="target" position={Position.Bottom} style={{ background: color, width: 8, height: 8, border: '2px solid #060810' }} />
      <Handle type="source" position={Position.Top} style={{ background: color, width: 8, height: 8, border: '2px solid #060810' }} />
    </div>
  );
}

// ─── Experience / Education Node (card with left accent bar) ─
export function ExperienceNode({ data }: { data: any }) {
  const isEdu = !!data.isEducation;
  const color = isEdu ? '#34d399' : '#f59e0b';
  const Icon = isEdu ? GraduationCap : Briefcase;

  return (
    <div style={{
      width: '340px',
      background: 'linear-gradient(180deg, #0c1018 0%, #0a0e18 100%)',
      borderRadius: '12px',
      border: `1px solid ${color}38`,
      boxShadow: `0 4px 20px rgba(0,0,0,0.5), 0 0 30px ${color}04`,
      fontFamily: "'Inter', -apple-system, sans-serif",
      display: 'flex',
      overflow: 'hidden',
      transition: 'border-color 0.3s ease',
    }}>
      {/* Left accent bar */}
      <div style={{
        width: '3px', flexShrink: 0,
        background: `linear-gradient(180deg, ${color} 0%, ${color}33 100%)`,
      }} />

      <div style={{ padding: '14px 16px 14px 14px', display: 'flex', gap: '12px', alignItems: 'flex-start', flex: 1 }}>
        {/* Icon box */}
        <div style={{
          width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0,
          background: `${color}14`, border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 2px 10px ${color}08`,
        }}>
          <Icon size={17} color={color} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#dce7f7', marginBottom: '4px', lineHeight: 1.3 }}>
            {data.title}
          </div>
          <div style={{ fontSize: '12px', color: '#6a7e9e', marginBottom: '10px', fontWeight: 500 }}>
            {data.company}
          </div>

          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: data.highlight ? '10px' : 0 }}>
            <Pill label={data.duration} color={color} />
            {data.grade && <Pill label={data.grade} color="#a78bfa" />}
          </div>

          {data.highlight && (
            <div style={{
              fontSize: '12px', color: '#5a6a88', lineHeight: '1.6',
              borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '10px', marginTop: '4px',
            }}>↳ {data.highlight}</div>
          )}
        </div>
      </div>

      <Handle type="target" position={Position.Top} style={{ background: color, width: 7, height: 7, border: '2px solid #060810', left: '50%' }} />
      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 7, height: 7, border: '2px solid #060810', left: '50%' }} />
      <Handle type="target" position={Position.Right} id="right" style={{ background: color, width: 7, height: 7, border: '2px solid #060810' }} />
    </div>
  );
}

// ─── Skill Category Node ────────────────────────────────────
export function SkillNode({ data }: { data: any }) {
  const color = data.color || '#00d4ff';
  const IconComp = data.iconKey === 'tech' ? Server : Code;

  return (
    <div style={{
      width: '320px',
      background: 'linear-gradient(180deg, #0c1018 0%, #0a0e18 100%)',
      borderRadius: '12px',
      border: `1px solid ${color}38`,
      boxShadow: `0 4px 20px rgba(0,0,0,0.4), 0 0 30px ${color}04`,
      fontFamily: "'Inter', -apple-system, sans-serif",
      overflow: 'hidden',
    }}>
      {/* Top accent line */}
      <div style={{
        height: '3px',
        background: `linear-gradient(90deg, ${color} 0%, ${color}33 100%)`,
      }} />

      <div style={{ padding: '13px 15px 14px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '11px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '9px', flexShrink: 0,
            background: `${color}14`, border: `1px solid ${color}30`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 2px 10px ${color}08`,
          }}>
            <IconComp size={16} color={color} />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#dce7f7' }}>{data.title}</div>
            <div style={{ fontSize: '12px', color: '#4a5a7a', marginTop: '2px' }}>{data.subtitle}</div>
          </div>
        </div>

        {/* Skill pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
          {(data.skills || []).map((s: string) => <Pill key={s} label={s} color={color} />)}
        </div>
      </div>

      <Handle type="target" position={Position.Top} id="top" style={{ background: color, width: 7, height: 7, border: '2px solid #060810' }} />
      <Handle type="target" position={Position.Left} id="left" style={{ background: color, width: 7, height: 7, border: '2px solid #060810' }} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: color, width: 7, height: 7, border: '2px solid #060810' }} />
    </div>
  );
}
