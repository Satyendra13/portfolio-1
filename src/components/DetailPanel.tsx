"use client";

import React, { useEffect, useState } from 'react';
import { X, ExternalLink, MapPin, Calendar, Phone, Mail, Github, Linkedin, ArrowUpRight } from 'lucide-react';

// ─── Full Resume Data ─────────────────────────────────────────
const DETAIL_MAP: Record<string, any> = {

  profile: {
    type: 'Profile',
    title: 'Satyendra Kumar',
    subtitle: 'Software Developer',
    color: '#a78bfa',
    location: 'Gurugram, Haryana',
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
    skills: ['JavaScript', 'Python', 'PHP', 'SQL', 'ReactJS', 'NextJS', 'Node.js', 'Laravel', 'MongoDB', 'Docker'],
    links: [
      { label: 'GitHub', url: 'https://github.com', icon: 'github', color: '#a78bfa' },
      { label: 'LinkedIn', url: 'https://linkedin.com', icon: 'linkedin', color: '#00d4ff' },
    ],
    contact: { email: 'satyendra9173@gmail.com', phone: '+91-9128649473' },
  },

  'proj-1': {
    type: 'Project',
    title: 'FlashMind – AI Study Platform',
    subtitle: 'Full-Stack AI · ReactJS · NodeJS · MongoDB · Gemini · Docker',
    color: '#00d4ff',
    description:
      'FlashMind is an AI-powered study platform that lets students create and review intelligent ' +
      'notes, flashcards, and take adaptive quizzes in both English and Hindi.',
    highlights: [
      'AI-generated notes, flashcards, and quizzes via Gemini API',
      'Multi-language support — English & Hindi',
      'Microservices backend with Node.js, expressive REST APIs',
      'MongoDB for flexible content storage with efficient querying',
      'Docker-containerised services for scalable deployment',
      'Detailed analytics dashboard and progress tracking UI',
    ],
    skills: ['ReactJS', 'JavaScript', 'MongoDB', 'NodeJS', 'ExpressJS', 'Gemini AI', 'Microservices', 'Docker'],
    links: [{ label: 'View Project', url: '#', color: '#00d4ff' }],
  },

  'proj-2': {
    type: 'Project',
    title: 'Code Sync – Collaborative Editor',
    subtitle: 'Real-Time App · ReactJS · Socket.IO · NodeJS · ExpressJS',
    color: '#a78bfa',
    description:
      'A real-time collaborative code editor enabling multiple users to code together in shared rooms.',
    highlights: [
      'Live multi-user code synchronisation via WebSockets (Socket.IO)',
      'Each room auto-assigned a unique ID for frictionless access',
      'Host-controlled sessions with member collaboration support',
      'Low-latency event-driven architecture on Node.js + Express',
    ],
    skills: ['ReactJS', 'JavaScript', 'Socket.IO', 'NodeJS', 'ExpressJS'],
    links: [{ label: 'View Project', url: '#', color: '#a78bfa' }],
  },

  'proj-3': {
    type: 'Project',
    title: 'Billing Expo – Invoice Generator',
    subtitle: 'Web App · React · JavaScript',
    color: '#f59e0b',
    description:
      'A professional invoice generation and management web app built with React for small businesses.',
    highlights: [
      'Intuitive UI for customer details and multi-line item entry',
      'Automated tax rate and discount calculations',
      'Print-ready PDF-style invoice layout',
      'Clean, responsive React component architecture',
    ],
    skills: ['React', 'JavaScript', 'HTML/CSS'],
    links: [{ label: 'View Project', url: '#', color: '#f59e0b' }],
  },

  'edu-1': {
    type: 'Education',
    title: 'Bachelor of Technology – Information Technology',
    subtitle: 'Panipat Institute of Engineering and Technology, Panipat',
    color: '#34d399',
    location: 'Panipat, Haryana',
    duration: '2019 – 2023',
    description: 'B.Tech in Information Technology with 76% aggregate. Comprehensive study of computer science fundamentals including data structures, algorithms, OS, DBMS, networking, and software engineering.',
    highlights: [
      'Core CS: Data Structures, Algorithms, Discrete Mathematics',
      'Systems: Operating Systems, Computer Networks, DBMS',
      'Web & App Development coursework',
      'Final year project in web application development',
    ],
    skills: ['Data Structures', 'Algorithms', 'DBMS', 'OS', 'Networks', 'Web Dev', 'OOP'],
  },

  'edu-2': {
    type: 'Education',
    title: 'Higher Secondary School (Science)',
    subtitle: 'B S S C College, Udakishunganj (BSEB)',
    color: '#34d399',
    location: 'Madhepura, Bihar',
    duration: '2017 – 2019',
    description: 'Completed Higher Secondary education with 73.2% marks under Bihar School Examination Board.',
    skills: ['Physics', 'Chemistry', 'Mathematics', 'Biology'],
  },

  'edu-3': {
    type: 'Education',
    title: 'Secondary School (CBSE)',
    subtitle: 'Jawahar Navodaya Vidyalaya, Madhepura',
    color: '#34d399',
    location: 'Madhepura, Bihar',
    duration: '2016 – 2017',
    description: 'Completed Secondary schooling under CBSE board with CGPA of 8.6 at a Navodaya Vidyalaya — a merit-based government residential school.',
    skills: ['Mathematics', 'Science', 'English', 'Social Studies'],
  },

  'exp-1': {
    type: 'Experience',
    title: 'Software Developer',
    subtitle: 'Teleperformance',
    color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    duration: 'Oct 2024 – Present',
    description: 'Building and maintaining scalable features enhancing platform functionality and user experience, with a focus on data-intensive dashboard development.',
    highlights: [
      'Designed React & Next.js dashboards for real-time data visualisation',
      'Built and maintained backend services with Node.js and MySQL',
      'Performance tuning and production issue resolution',
      'Contributed to Docker-based microservices architecture',
    ],
    skills: ['React', 'Next.js', 'Node.js', 'MySQL', 'Docker', 'JavaScript', 'Microservices'],
  },

  'exp-2': {
    type: 'Experience',
    title: 'Software Development Executive',
    subtitle: 'PinnacleWorks Infotech Pvt. Ltd.',
    color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    duration: 'Oct 2023 – Oct 2024',
    description: 'Led process automation and performance modernisation initiatives, significantly reducing operational overhead and improving system efficiency.',
    highlights: [
      'Automated critical portal workflows (Laravel + MongoDB) — 80% QA reduction',
      'Performance optimisation and Nginx-based system architecture',
      'Built JavaScript-based frontend components for streamlined UX',
      'Planned and executed software development lifecycle initiatives',
    ],
    skills: ['Laravel', 'PHP', 'MongoDB', 'Nginx', 'JavaScript', 'MySQL'],
  },

  'exp-3': {
    type: 'Experience',
    title: 'Software Development Intern',
    subtitle: 'PinnacleWorks Infotech Pvt. Ltd.',
    color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    duration: 'July 2023 – Oct 2023',
    description: 'Internship focused on backend development and database integration using PHP Laravel and MongoDB.',
    highlights: [
      'Developed backend modules with PHP Laravel',
      'MongoDB integration for document-based data storage',
      'Collaborated on frontend features with JavaScript',
    ],
    skills: ['PHP', 'Laravel', 'MongoDB', 'JavaScript'],
  },

  'exp-4': {
    type: 'Experience',
    title: 'Frontend Developer Intern',
    subtitle: 'Cyber Flow',
    color: '#f59e0b',
    location: 'Gurgaon, Haryana',
    duration: 'Sept 2021 – Dec 2021',
    description: 'Frontend internship building responsive UI components and learning web development fundamentals in a professional environment.',
    highlights: [
      'Built responsive UI components with HTML, CSS & JavaScript',
      'Learnt professional development workflows and version control',
    ],
    skills: ['HTML', 'CSS', 'JavaScript'],
  },

  'skill-langs': {
    type: 'Technical Skills',
    title: 'Programming Languages',
    color: '#00d4ff',
    description: 'Core programming languages used regularly across frontend, backend, and data projects.',
    skills: ['JavaScript (ES2022+)', 'Python', 'PHP', 'SQL'],
  },

  'skill-frameworks': {
    type: 'Technical Skills',
    title: 'Frameworks & Libraries',
    color: '#a78bfa',
    description: 'Frontend and backend frameworks, libraries and API integrations used in production.',
    skills: ['ReactJS', 'NextJS', 'Node.js', 'Express.js', 'Laravel', 'Socket.IO', 'AI API Integration', 'Microservices'],
  },

  'skill-tools': {
    type: 'Technical Skills',
    title: 'Databases & DevOps',
    color: '#34d399',
    description: 'Data storage, infrastructure tooling, and development environment configuration.',
    skills: ['MongoDB', 'MySQL', 'PostgreSQL', 'Docker', 'Git & GitHub', 'VS Code', 'Postman', 'Nginx'],
  },
};

// ─── Component ────────────────────────────────────────────────
export default function DetailPanel({ node, onClose }: { node: any; onClose: () => void }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger animation
    requestAnimationFrame(() => setIsVisible(true));
  }, [node]);

  const info = DETAIL_MAP[node.id] || {
    type: node.type ?? 'Node',
    title: node.data?.title ?? node.data?.label ?? 'Details',
    color: '#a78bfa',
    description: 'Click a node to explore details.',
    skills: [],
  };

  const accent = info.color || '#a78bfa';

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 250);
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      pointerEvents: 'none',
    }}>
      {/* Backdrop */}
      <div
        onClick={handleClose}
        style={{
          position: 'absolute', inset: 0,
          background: 'rgba(0,0,0,0.4)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          pointerEvents: 'all',
          opacity: isVisible ? 1 : 0,
          transition: 'opacity 0.25s ease',
        }}
      />

      {/* Sliding panel */}
      <div
        className="detail-panel-slide"
        style={{
          position: 'absolute',
          top: 0, left: '290px', bottom: 0,
          width: '380px',
          background: 'linear-gradient(180deg, rgba(10,14,24,0.98) 0%, rgba(8,12,20,0.99) 100%)',
          borderRight: `1px solid ${accent}18`,
          borderLeft: `3px solid ${accent}`,
          display: 'flex', flexDirection: 'column',
          overflowY: 'auto',
          pointerEvents: 'all',
          boxShadow: `6px 0 50px rgba(0,0,0,0.6), inset 1px 0 0 ${accent}08`,
          transform: isVisible ? 'translateX(0)' : 'translateX(-100%)',
          opacity: isVisible ? 1 : 0,
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease',
        }}
      >

        {/* Header */}
        <div style={{
          padding: '22px 20px 16px',
          borderBottom: `1px solid rgba(255,255,255,0.05)`,
          background: `linear-gradient(135deg, ${accent}08 0%, transparent 100%)`,
          position: 'sticky', top: 0, zIndex: 1,
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{
              fontSize: '9px', fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase',
              color: accent, background: `${accent}12`,
              padding: '4px 12px', borderRadius: '20px', border: `1px solid ${accent}30`,
            }}>{info.type}</span>
            <button onClick={handleClose} style={{
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '6px', cursor: 'pointer',
              color: '#3a4a68', padding: '5px', transition: 'all 0.2s',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
              onMouseEnter={e => {
                e.currentTarget.style.color = '#6b7fa8';
                e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.color = '#3a4a68';
                e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
              }}
            ><X size={14} /></button>
          </div>

          <h2 style={{ fontSize: '19px', fontWeight: 800, color: '#dce7f7', marginBottom: '4px', lineHeight: 1.2 }}>
            {info.title}
          </h2>
          {info.subtitle && (
            <p style={{ fontSize: '12px', color: '#4a5a7a', margin: '0 0 10px', lineHeight: 1.5 }}>{info.subtitle}</p>
          )}

          {/* Meta row */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {info.location && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#3a4a68' }}>
                <MapPin size={10} /> {info.location}
              </span>
            )}
            {info.duration && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#3a4a68' }}>
                <Calendar size={10} /> {info.duration}
              </span>
            )}
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '22px', flex: 1 }}>

          {/* Description */}
          <div style={{ animation: 'fadeSlideUp 0.3s ease 0.1s both' }}>
            <SectionLabel label="ABOUT" />
            <p style={{ fontSize: '13px', color: '#6b7fa8', lineHeight: '1.75', margin: 0 }}>
              {info.description}
            </p>
          </div>

          {/* Highlights */}
          {info.highlights && info.highlights.length > 0 && (
            <div style={{ animation: 'fadeSlideUp 0.3s ease 0.2s both' }}>
              <SectionLabel label="KEY HIGHLIGHTS" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {info.highlights.map((h: string, i: number) => (
                  <div key={i} style={{
                    display: 'flex', gap: '10px', alignItems: 'flex-start',
                    animation: `fadeSlideUp 0.3s ease ${0.25 + i * 0.05}s both`,
                  }}>
                    <div style={{
                      width: '6px', height: '6px', borderRadius: '50%', marginTop: '5px', flexShrink: 0,
                      background: accent,
                      boxShadow: `0 0 6px ${accent}40`,
                    }} />
                    <p style={{ fontSize: '12px', color: '#8a9bbf', margin: 0, lineHeight: '1.65' }}>{h}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills */}
          {info.skills && info.skills.length > 0 && (
            <div style={{ animation: 'fadeSlideUp 0.3s ease 0.3s both' }}>
              <SectionLabel label={info.type === 'Technical Skills' ? 'ALL SKILLS' : 'STACK'} />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                {info.skills.map((s: string) => (
                  <span key={s} style={{
                    padding: '5px 13px', borderRadius: '20px', fontSize: '11px', fontWeight: 600,
                    background: `${accent}12`, border: `1px solid ${accent}30`, color: accent,
                    transition: 'all 0.2s',
                    cursor: 'default',
                  }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = `${accent}22`;
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = `${accent}12`;
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Contact */}
          {info.contact && (
            <div style={{ animation: 'fadeSlideUp 0.3s ease 0.35s both' }}>
              <SectionLabel label="CONTACT" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[
                  { icon: <Mail size={13} />, text: info.contact.email, color: '#00d4ff', href: `mailto:${info.contact.email}` },
                  { icon: <Phone size={13} />, text: info.contact.phone, color: '#34d399', href: `tel:${info.contact.phone}` },
                ].map(({ icon, text, color, href }) => (
                  <a key={text} href={href} style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    fontSize: '12px', color,
                    textDecoration: 'none', padding: '8px 12px',
                    borderRadius: '8px', background: `${color}08`,
                    border: `1px solid ${color}18`,
                    transition: 'all 0.2s',
                  }}
                    onMouseEnter={(e) => e.currentTarget.style.background = `${color}15`}
                    onMouseLeave={(e) => e.currentTarget.style.background = `${color}08`}
                  >
                    {icon} {text}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Links */}
          {info.links && info.links.length > 0 && (
            <div style={{ animation: 'fadeSlideUp 0.3s ease 0.4s both' }}>
              <SectionLabel label="LINKS" />
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {info.links.map((link: any) => (
                  <a key={link.label} href={link.url} target="_blank" rel="noreferrer" style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '8px 16px', borderRadius: '10px',
                    background: `${link.color}12`, border: `1px solid ${link.color}30`,
                    fontSize: '12px', fontWeight: 600, color: link.color,
                    textDecoration: 'none', transition: 'all 0.2s',
                  }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = `${link.color}22`;
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = `0 4px 15px ${link.color}15`;
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = `${link.color}12`;
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <ArrowUpRight size={12} /> {link.label}
                  </a>
                ))}
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
      color: '#2a3a58', textTransform: 'uppercase', marginBottom: '10px',
      display: 'flex', alignItems: 'center', gap: '8px',
    }}>
      {label}
      <div style={{
        flex: 1, height: '1px',
        background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 0%, transparent 100%)',
      }} />
    </div>
  );
}
