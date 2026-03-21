"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
  User, Layers, Briefcase, GraduationCap, Code,
  MapPin, Mail, Phone, Github, Linkedin, ExternalLink,
  ChevronRight, Download, Sparkles, Calendar, X, ArrowUpRight
} from 'lucide-react';

type Section = 'profile' | 'projects' | 'experience' | 'education' | 'skills';

const RESUME_URL = '/Satyendra_Kumar_Resume.pdf';

const PROFILE_DATA = {
  name: 'Satyendra Kumar',
  role: 'Software Developer',
  location: 'Gurugram, Haryana',
  email: 'satyendra9173@gmail.com',
  phone: '+91-9128649473',
  description:
    'Full-stack Software Developer with 2+ years of professional experience building scalable, ' +
    'AI-integrated web applications and microservices. Expert in React ecosystem, Node.js, PHP ' +
    'Laravel, and cloud infrastructure. Passionate about developer experience and product quality.',
  highlights: [
    'Designed scalable dashboards at Teleperformance with React & Next.js',
    'Reduced QA workload by 80% via Laravel/MongoDB automation at PinnacleWorks',
    'Built FlashMind — an AI study platform (multi-language, microservices)',
    'Developed Code Sync — real-time collaborative code editor with Socket.IO',
  ],
  skills: ['2+ Years Experience', 'React/Next.js', 'Node.js', 'AI Integration', 'Docker', 'Microservices'],
};

const PROJECTS = [
  {
    category: 'AI · FULL-STACK',
    title: 'FlashMind – AI Study Platform',
    color: '#00d4ff',
    desc: 'AI-powered notes, flashcards & quizzes with multi-language support.',
    stack: ['ReactJS', 'NodeJS', 'MongoDB', 'Gemini AI', 'Docker', 'Microservices'],
    details: {
      description: 'FlashMind is an AI-powered study platform that lets students create and review intelligent notes, flashcards, and take adaptive quizzes in both English and Hindi.',
      highlights: [
        'AI-generated notes, flashcards, and quizzes via Gemini API',
        'Multi-language support — English & Hindi',
        'Microservices backend with Node.js, expressive REST APIs',
        'MongoDB for flexible content storage',
        'Docker-containerised services for scalable deployment',
      ],
    },
  },
  {
    category: 'REAL-TIME · COLLAB',
    title: 'Code Sync – Collaborative Editor',
    color: '#a78bfa',
    desc: 'Real-time multi-user code editor with WebSocket sync.',
    stack: ['ReactJS', 'Socket.IO', 'NodeJS', 'ExpressJS'],
    details: {
      description: 'A real-time collaborative code editor enabling multiple users to code together in shared rooms.',
      highlights: [
        'Live multi-user code synchronisation via WebSockets',
        'Each room auto-assigned a unique ID',
        'Host-controlled sessions with member collaboration',
        'Low-latency event-driven architecture',
      ],
    },
  },
  {
    category: 'WEB APP',
    title: 'Billing Expo – Invoice Generator',
    color: '#f59e0b',
    desc: 'React invoice app with tax/discount automation & print support.',
    stack: ['React', 'JavaScript'],
    details: {
      description: 'A professional invoice generation web app built with React for small businesses.',
      highlights: [
        'Intuitive UI for customer details and multi-line items',
        'Automated tax rate and discount calculations',
        'Print-ready PDF-style invoice layout',
        'Clean, responsive React component architecture',
      ],
    },
  },
];

const EXPERIENCE = [
  {
    title: 'Software Developer', company: 'Teleperformance',
    duration: 'Oct 2024 – Present', color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    highlight: 'React/Next.js dashboards · Node.js & MySQL · Docker',
    details: {
      description: 'Building and maintaining scalable features with a focus on data-intensive dashboard development.',
      highlights: [
        'Designed React & Next.js dashboards for real-time data visualisation',
        'Built and maintained backend services with Node.js and MySQL',
        'Performance tuning and production issue resolution',
        'Contributed to Docker-based microservices architecture',
      ],
      skills: ['React', 'Next.js', 'Node.js', 'MySQL', 'Docker', 'JavaScript'],
    },
  },
  {
    title: 'Software Dev Executive', company: 'PinnacleWorks',
    duration: 'Oct 2023 – Oct 2024', color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    highlight: 'Laravel & MongoDB — 80% QA reduction · Nginx',
    details: {
      description: 'Led process automation and performance modernisation initiatives.',
      highlights: [
        'Automated critical portal workflows (Laravel + MongoDB) — 80% QA reduction',
        'Performance optimisation and Nginx-based system architecture',
        'Built JavaScript-based frontend components for streamlined UX',
      ],
      skills: ['Laravel', 'PHP', 'MongoDB', 'Nginx', 'JavaScript', 'MySQL'],
    },
  },
  {
    title: 'Software Dev Intern', company: 'PinnacleWorks',
    duration: 'Jul – Oct 2023', color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    highlight: 'PHP/Laravel · MongoDB · JavaScript',
    details: {
      description: 'Backend development and database integration using PHP Laravel and MongoDB.',
      highlights: [
        'Developed backend modules with PHP Laravel',
        'MongoDB integration for document-based data storage',
        'Collaborated on frontend features with JavaScript',
      ],
      skills: ['PHP', 'Laravel', 'MongoDB', 'JavaScript'],
    },
  },
  {
    title: 'Frontend Developer Intern', company: 'Cyber Flow',
    duration: 'Sep – Dec 2021', color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    highlight: 'HTML · CSS · JavaScript · UI development',
    details: {
      description: 'Frontend internship building responsive UI components.',
      highlights: [
        'Built responsive UI components with HTML, CSS & JavaScript',
        'Learnt professional development workflows and version control',
      ],
      skills: ['HTML', 'CSS', 'JavaScript'],
    },
  },
];

const EDUCATION = [
  {
    title: 'B.Tech – Information Technology',
    institution: 'Panipat Institute of Engg. & Technology',
    duration: '2019 – 2023', grade: '76%', color: '#34d399',
    details: {
      description: 'B.Tech in Information Technology with 76% aggregate.',
      highlights: [
        'Core CS: Data Structures, Algorithms, Discrete Mathematics',
        'Systems: Operating Systems, Computer Networks, DBMS',
        'Web & App Development coursework',
      ],
      skills: ['Data Structures', 'Algorithms', 'DBMS', 'OS', 'Web Dev'],
    },
  },
  {
    title: 'Higher Secondary School',
    institution: 'B S S C College, Udakishunganj (BSEB)',
    duration: '2017 – 2019', grade: '73.2%', color: '#34d399',
    details: {
      description: 'Completed Higher Secondary education with 73.2% marks under BSEB.',
      skills: ['Physics', 'Chemistry', 'Mathematics', 'Biology'],
    },
  },
  {
    title: 'Secondary School',
    institution: 'Jawahar Navodaya Vidyalaya, Madhepura (CBSE)',
    duration: '2016 – 2017', grade: 'CGPA 8.6', color: '#34d399',
    details: {
      description: 'Completed Secondary schooling under CBSE board at a merit-based government residential school.',
      skills: ['Mathematics', 'Science', 'English', 'Social Studies'],
    },
  },
];

const SKILLS_DATA = [
  {
    title: 'Languages', color: '#00d4ff',
    skills: ['JavaScript', 'Python', 'PHP', 'SQL'],
    description: 'Core programming languages used regularly across frontend, backend, and data projects.',
  },
  {
    title: 'Frameworks & Libraries', color: '#a78bfa',
    skills: ['ReactJS', 'NextJS', 'Node.js', 'Express', 'Laravel', 'Socket.IO', 'AI API Integration'],
    description: 'Frontend and backend frameworks, libraries and API integrations used in production.',
  },
  {
    title: 'Databases & DevOps', color: '#34d399',
    skills: ['MongoDB', 'MySQL', 'PostgreSQL', 'Docker', 'Microservices', 'Git & GitHub', 'VS Code', 'Postman'],
    description: 'Data storage, infrastructure tooling, and development environment configuration.',
  },
];

function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '4px 12px', borderRadius: '20px',
      fontSize: '11px', fontWeight: 600,
      background: `${color}18`, border: `1px solid ${color}40`, color,
    }}>{label}</span>
  );
}

// ─── Mobile Detail Modal ─────────────────────────────────────
function MobileDetailModal({ data, onClose }: { data: any; onClose: () => void }) {
  const accent = data.color || '#a78bfa';

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      display: 'flex', flexDirection: 'column',
      background: 'rgba(0,0,0,0.5)',
      backdropFilter: 'blur(4px)',
      animation: 'fadeIn 0.15s ease',
    }} onClick={onClose}>
      <div style={{
        marginTop: 'auto',
        maxHeight: '85vh',
        overflowY: 'auto',
        background: 'linear-gradient(180deg, rgba(10,14,24,0.99) 0%, rgba(8,12,20,0.99) 100%)',
        borderTop: `3px solid ${accent}`,
        borderRadius: '18px 18px 0 0',
        animation: 'slideUp 0.25s ease',
      }} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          padding: '18px 20px 14px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          position: 'sticky', top: 0, zIndex: 1,
          background: 'rgba(10,14,24,0.98)',
          backdropFilter: 'blur(12px)',
        }}>
          <div style={{ flex: 1 }}>
            {data.type && (
              <span style={{
                fontSize: '9px', fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase',
                color: accent, background: `${accent}12`,
                padding: '3px 10px', borderRadius: '20px', border: `1px solid ${accent}30`,
                display: 'inline-block', marginBottom: '8px',
              }}>{data.type}</span>
            )}
            <h2 style={{ fontSize: '17px', fontWeight: 800, color: '#dce7f7', lineHeight: 1.2, margin: 0 }}>
              {data.title}
            </h2>
            {data.subtitle && (
              <p style={{ fontSize: '12px', color: '#4a5a7a', margin: '4px 0 0', lineHeight: 1.4 }}>{data.subtitle}</p>
            )}
          </div>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '6px', cursor: 'pointer', color: '#3a4a68', padding: '5px',
            display: 'flex', alignItems: 'center',
          }}><X size={14} /></button>
        </div>

        {/* Body */}
        <div style={{ padding: '16px 20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Meta */}
          {(data.duration || data.location) && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {data.duration && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#4a5a7a' }}>
                  <Calendar size={10} /> {data.duration}
                </span>
              )}
              {data.location && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#4a5a7a' }}>
                  <MapPin size={10} /> {data.location}
                </span>
              )}
            </div>
          )}

          {/* Description */}
          {data.description && (
            <div>
              <SectionLabel label="ABOUT" />
              <p style={{ fontSize: '13px', color: '#6b7fa8', lineHeight: 1.75, margin: 0 }}>{data.description}</p>
            </div>
          )}

          {/* Highlights */}
          {data.highlights && data.highlights.length > 0 && (
            <div>
              <SectionLabel label="KEY HIGHLIGHTS" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
                {data.highlights.map((h: string, i: number) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <div style={{
                      width: '5px', height: '5px', borderRadius: '50%', marginTop: '5px', flexShrink: 0,
                      background: accent, boxShadow: `0 0 6px ${accent}40`,
                    }} />
                    <p style={{ fontSize: '12px', color: '#8a9bbf', margin: 0, lineHeight: 1.65 }}>{h}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills */}
          {data.skills && data.skills.length > 0 && (
            <div>
              <SectionLabel label="STACK" />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {data.skills.map((s: string) => <Pill key={s} label={s} color={accent} />)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div style={{
      fontSize: '9px', fontWeight: 800, letterSpacing: '2px',
      color: '#2a3a58', textTransform: 'uppercase', marginBottom: '8px',
      display: 'flex', alignItems: 'center', gap: '8px',
    }}>
      {label}
      <div style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 0%, transparent 100%)' }} />
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────
export default function MobileLayout() {
  const [activeSection, setActiveSection] = useState<Section>('profile');
  const [detailData, setDetailData] = useState<any>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) contentRef.current.scrollTop = 0;
  }, [activeSection]);

  const navItems: { id: Section; icon: React.ReactNode; label: string }[] = [
    { id: 'profile', icon: <User size={18} />, label: 'Profile' },
    { id: 'projects', icon: <Layers size={18} />, label: 'Projects' },
    { id: 'experience', icon: <Briefcase size={18} />, label: 'Work' },
    { id: 'education', icon: <GraduationCap size={18} />, label: 'Edu' },
    { id: 'skills', icon: <Code size={18} />, label: 'Skills' },
  ];

  return (
    <div className="mobile-layout">
      {/* Header */}
      <div className="mobile-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px',
            background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(167,139,250,0.12))',
            border: '1px solid rgba(167,139,250,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px', fontWeight: 900, color: '#a78bfa',
          }}>SK</div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#dce7f7' }}>Satyendra Kumar</div>
            <div style={{ fontSize: '10px', color: '#4a5a7a' }}>Software Developer</div>
          </div>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '5px',
          padding: '3px 8px', borderRadius: '20px',
          background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.25)',
          fontSize: '9px', fontWeight: 600, color: '#34d399',
        }}>
          <div style={{
            width: '5px', height: '5px', borderRadius: '50%', background: '#34d399',
            animation: 'pulse-dot 2s infinite',
          }} />
          Available
        </div>
      </div>

      {/* Content */}
      <div className="mobile-content" ref={contentRef}>
        {activeSection === 'profile' && <ProfileSection onDetail={setDetailData} />}
        {activeSection === 'projects' && <ProjectsSection onDetail={setDetailData} />}
        {activeSection === 'experience' && <ExperienceSection onDetail={setDetailData} />}
        {activeSection === 'education' && <EducationSection onDetail={setDetailData} />}
        {activeSection === 'skills' && <SkillsSection onDetail={setDetailData} />}
      </div>

      {/* Bottom Nav */}
      <div className="mobile-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`mobile-nav-item ${activeSection === item.id ? 'active' : ''}`}
            onClick={() => setActiveSection(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* Detail Modal */}
      {detailData && <MobileDetailModal data={detailData} onClose={() => setDetailData(null)} />}
    </div>
  );
}

// ─── Sections ────────────────────────────────────────────────

function ProfileSection({ onDetail }: { onDetail: (d: any) => void }) {
  return (
    <>
      {/* Hero card */}
      <div className="mobile-card" style={{ animationDelay: '0s' }}
        onClick={() => onDetail({
          type: 'Profile',
          title: PROFILE_DATA.name,
          subtitle: PROFILE_DATA.role + ' · Full-Stack & AI Integration',
          color: '#a78bfa',
          location: PROFILE_DATA.location,
          description: PROFILE_DATA.description,
          highlights: PROFILE_DATA.highlights,
          skills: ['JavaScript', 'Python', 'PHP', 'SQL', 'ReactJS', 'NextJS', 'Node.js', 'Laravel', 'MongoDB', 'Docker'],
        })}
      >
        <div style={{
          height: '4px',
          background: 'linear-gradient(90deg, #00d4ff 0%, #a78bfa 50%, #f59e0b 100%)',
        }} />
        <div style={{ padding: '20px' }}>
          <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '14px', flexShrink: 0,
              background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(167,139,250,0.12))',
              border: '1.5px solid rgba(167,139,250,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '18px', fontWeight: 900, color: '#a78bfa',
            }}>SK</div>
            <div>
              <h1 className="gradient-text" style={{
                fontSize: '22px', fontWeight: 900, marginBottom: '4px', letterSpacing: '-0.5px',
              }}>
                {PROFILE_DATA.name}
              </h1>
              <p style={{ fontSize: '12px', fontWeight: 600, color: '#a78bfa', margin: 0 }}>
                {PROFILE_DATA.role} · Full-Stack & AI
              </p>
            </div>
          </div>

          <p style={{ fontSize: '13px', color: '#5a6a88', lineHeight: 1.7, marginBottom: '14px' }}>
            {PROFILE_DATA.description}
          </p>

          {/* Contact info */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
            <a href={`mailto:${PROFILE_DATA.email}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#4a5a7a', textDecoration: 'none' }}
              onClick={e => e.stopPropagation()}>
              <Mail size={12} /> {PROFILE_DATA.email}
            </a>
            <a href={`tel:${PROFILE_DATA.phone}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#4a5a7a', textDecoration: 'none' }}
              onClick={e => e.stopPropagation()}>
              <Phone size={12} /> {PROFILE_DATA.phone}
            </a>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#4a5a7a' }}>
              <MapPin size={12} /> {PROFILE_DATA.location}
            </div>
          </div>

          {/* Highlights */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {PROFILE_DATA.skills.map(h => <Pill key={h} label={h} color="#00d4ff" />)}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mobile-card" style={{ animationDelay: '0.1s' }}>
        <div className="stats-bar">
          <div className="stat-item">
            <div className="stat-value" style={{ color: '#00d4ff' }}>2+</div>
            <div className="stat-label">Yrs Exp</div>
          </div>
          <div className="stat-item">
            <div className="stat-value" style={{ color: '#a78bfa' }}>3</div>
            <div className="stat-label">Projects</div>
          </div>
          <div className="stat-item">
            <div className="stat-value" style={{ color: '#f59e0b' }}>4</div>
            <div className="stat-label">Companies</div>
          </div>
          <div className="stat-item">
            <div className="stat-value" style={{ color: '#34d399' }}>10+</div>
            <div className="stat-label">Tech Stack</div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="mobile-card" style={{ animationDelay: '0.2s' }}>
        <div style={{ padding: '16px', display: 'flex', gap: '10px' }}>
          {[
            { icon: <Github size={16} />, label: 'GitHub', color: '#a78bfa', href: 'https://github.com/Satyendra13' },
            { icon: <Linkedin size={16} />, label: 'LinkedIn', color: '#00d4ff', href: 'https://linkedin.com/in/satyendra13' },
            { icon: <Download size={16} />, label: 'Resume', color: '#34d399', href: RESUME_URL, download: true },
          ].map(({ icon, label, color, href, download }) => (
            <a key={label} href={href} download={download ? 'Satyendra_Kumar_Resume.pdf' : undefined}
              target={download ? undefined : '_blank'} rel={download ? undefined : 'noreferrer'}
              style={{
                flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                padding: '10px 8px', borderRadius: '10px',
                background: `${color}12`, border: `1px solid ${color}30`,
                color, fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                fontFamily: 'Inter, sans-serif', transition: 'all 0.2s', textDecoration: 'none',
              }}
            >{icon} {label}</a>
          ))}
        </div>
      </div>
    </>
  );
}

function ProjectsSection({ onDetail }: { onDetail: (d: any) => void }) {
  return (
    <>
      <div style={{
        fontSize: '10px', fontWeight: 800, letterSpacing: '2px', color: '#3a4a68',
        textTransform: 'uppercase', marginBottom: '4px',
      }}>Featured Projects</div>
      {PROJECTS.map((project, i) => (
        <div key={i} className="mobile-card" style={{ animationDelay: `${i * 0.1}s`, cursor: 'pointer' }}
          onClick={() => onDetail({
            type: 'Project',
            title: project.title,
            subtitle: project.stack.join(' · '),
            color: project.color,
            description: project.details.description,
            highlights: project.details.highlights,
            skills: project.stack,
          })}
        >
          {/* Banner */}
          <div style={{
            height: '80px', position: 'relative',
            background: `linear-gradient(135deg, ${project.color}25 0%, ${project.color}08 100%)`,
            borderBottom: `1px solid ${project.color}25`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{
              position: 'absolute', inset: 0,
              backgroundImage: `linear-gradient(${project.color}12 1px, transparent 1px), linear-gradient(90deg, ${project.color}12 1px, transparent 1px)`,
              backgroundSize: '20px 20px',
            }} />
            <div style={{
              width: '40px', height: '40px', borderRadius: '10px',
              background: `${project.color}22`, border: `1px solid ${project.color}55`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1,
            }}>
              <ExternalLink color={project.color} size={18} />
            </div>
            <div style={{
              position: 'absolute', top: 10, left: 12,
              fontSize: '8px', fontWeight: 800, letterSpacing: '1.5px',
              color: project.color, textTransform: 'uppercase',
            }}>{project.category}</div>
            <div style={{
              position: 'absolute', top: 10, right: 12,
              fontSize: '9px', color: '#3a4a68', display: 'flex', alignItems: 'center', gap: '3px',
            }}>
              Tap for details <ChevronRight size={10} />
            </div>
          </div>
          <div style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#dce7f7', marginBottom: '6px' }}>
              {project.title}
            </div>
            <p style={{ fontSize: '12px', color: '#5a6a88', lineHeight: 1.6, margin: '0 0 10px' }}>
              {project.desc}
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
              {project.stack.map(s => <Pill key={s} label={s} color={project.color} />)}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

function ExperienceSection({ onDetail }: { onDetail: (d: any) => void }) {
  return (
    <>
      <div style={{
        fontSize: '10px', fontWeight: 800, letterSpacing: '2px', color: '#3a4a68',
        textTransform: 'uppercase', marginBottom: '4px',
      }}>Work Experience</div>
      {EXPERIENCE.map((exp, i) => (
        <div key={i} className="mobile-card" style={{ animationDelay: `${i * 0.1}s`, cursor: 'pointer' }}
          onClick={() => onDetail({
            type: 'Experience',
            title: exp.title,
            subtitle: exp.company,
            color: exp.color,
            duration: exp.duration,
            location: exp.location,
            description: exp.details.description,
            highlights: exp.details.highlights,
            skills: exp.details.skills,
          })}
        >
          <div style={{ display: 'flex' }}>
            <div style={{
              width: '3px', flexShrink: 0, borderRadius: '12px 0 0 12px',
              background: `linear-gradient(180deg, ${exp.color} 0%, ${exp.color}44 100%)`,
            }} />
            <div style={{ padding: '14px 16px', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <div style={{
                  width: '34px', height: '34px', borderRadius: '8px', flexShrink: 0,
                  background: `${exp.color}15`, border: `1px solid ${exp.color}30`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Briefcase size={15} color={exp.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#dce7f7' }}>{exp.title}</div>
                  <div style={{ fontSize: '11px', color: '#5a6a88', fontWeight: 500 }}>{exp.company}</div>
                </div>
                <ChevronRight size={14} color="#3a4a68" />
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                <Pill label={exp.duration} color={exp.color} />
              </div>
              {exp.highlight && (
                <div style={{
                  fontSize: '11px', color: '#4a5a7a', lineHeight: 1.6,
                  borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '8px',
                }}>↳ {exp.highlight}</div>
              )}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

function EducationSection({ onDetail }: { onDetail: (d: any) => void }) {
  return (
    <>
      <div style={{
        fontSize: '10px', fontWeight: 800, letterSpacing: '2px', color: '#3a4a68',
        textTransform: 'uppercase', marginBottom: '4px',
      }}>Education</div>
      {EDUCATION.map((edu, i) => (
        <div key={i} className="mobile-card" style={{ animationDelay: `${i * 0.1}s`, cursor: 'pointer' }}
          onClick={() => onDetail({
            type: 'Education',
            title: edu.title,
            subtitle: edu.institution,
            color: edu.color,
            duration: edu.duration,
            description: edu.details.description,
            highlights: edu.details.highlights,
            skills: edu.details.skills,
          })}
        >
          <div style={{ display: 'flex' }}>
            <div style={{
              width: '3px', flexShrink: 0, borderRadius: '12px 0 0 12px',
              background: `linear-gradient(180deg, ${edu.color} 0%, ${edu.color}44 100%)`,
            }} />
            <div style={{ padding: '14px 16px', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <div style={{
                  width: '34px', height: '34px', borderRadius: '8px', flexShrink: 0,
                  background: `${edu.color}15`, border: `1px solid ${edu.color}30`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <GraduationCap size={15} color={edu.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#dce7f7' }}>{edu.title}</div>
                  <div style={{ fontSize: '11px', color: '#5a6a88', fontWeight: 500 }}>{edu.institution}</div>
                </div>
                <ChevronRight size={14} color="#3a4a68" />
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                <Pill label={edu.duration} color={edu.color} />
                <Pill label={edu.grade} color="#a78bfa" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

function SkillsSection({ onDetail }: { onDetail: (d: any) => void }) {
  return (
    <>
      <div style={{
        fontSize: '10px', fontWeight: 800, letterSpacing: '2px', color: '#3a4a68',
        textTransform: 'uppercase', marginBottom: '4px',
      }}>Technical Skills</div>
      {SKILLS_DATA.map((group, i) => (
        <div key={i} className="mobile-card" style={{ animationDelay: `${i * 0.1}s`, cursor: 'pointer' }}
          onClick={() => onDetail({
            type: 'Technical Skills',
            title: group.title,
            color: group.color,
            description: group.description,
            skills: group.skills,
          })}
        >
          <div style={{
            height: '3px', borderRadius: '12px 12px 0 0',
            background: `linear-gradient(90deg, ${group.color} 0%, ${group.color}33 100%)`,
          }} />
          <div style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#dce7f7' }}>{group.title}</div>
              <ChevronRight size={14} color="#3a4a68" />
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {group.skills.map(s => <Pill key={s} label={s} color={group.color} />)}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
