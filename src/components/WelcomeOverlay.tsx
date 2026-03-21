"use client";

import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function WelcomeOverlay({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<'intro' | 'ready' | 'exit'>('intro');

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('ready'), 800);
    return () => clearTimeout(t1);
  }, []);

  const handleEnter = () => {
    if (phase !== 'ready') return; // only allow after animation is ready
    setPhase('exit');
    setTimeout(onComplete, 700);
  };

  return (
    <div
      className={`welcome-overlay ${phase === 'exit' ? 'hidden' : ''}`}
      style={{ cursor: 'default' }}
    >
      {/* Ambient orbs */}
      <div className="ambient-orb" style={{
        width: '400px', height: '400px',
        background: 'radial-gradient(circle, rgba(0,212,255,0.12) 0%, transparent 70%)',
        top: '20%', left: '10%',
        animation: 'orbFloat1 8s ease-in-out infinite',
      }} />
      <div className="ambient-orb" style={{
        width: '350px', height: '350px',
        background: 'radial-gradient(circle, rgba(167,139,250,0.12) 0%, transparent 70%)',
        bottom: '20%', right: '15%',
        animation: 'orbFloat2 10s ease-in-out infinite',
      }} />
      <div className="ambient-orb" style={{
        width: '250px', height: '250px',
        background: 'radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        animation: 'orbFloat1 12s ease-in-out infinite reverse',
      }} />

      {/* Content */}
      <div style={{
        textAlign: 'center',
        zIndex: 1,
        animation: phase === 'intro' ? 'fadeSlideUp 0.6s ease both' : undefined,
        padding: '0 24px',
      }}>
        {/* Sparkle icon */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '64px', height: '64px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, rgba(0,212,255,0.08), rgba(167,139,250,0.08))',
          border: '1px solid rgba(167,139,250,0.25)',
          marginBottom: '24px',
          animation: phase === 'ready' ? 'float 3s ease-in-out infinite' : undefined,
        }}>
          <Sparkles size={28} color="#a78bfa" />
        </div>

        {/* Name */}
        <h1 style={{
          fontSize: 'clamp(28px, 5vw, 48px)',
          fontWeight: 900,
          marginBottom: '8px',
          letterSpacing: '-2px',
          lineHeight: 1.1,
        }}>
          <span className="gradient-text">Satyendra Kumar</span>
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: 'clamp(13px, 2vw, 16px)',
          color: '#4a5a7a',
          fontWeight: 500,
          marginBottom: '28px',
          opacity: phase === 'ready' ? 1 : 0,
          transition: 'opacity 0.5s ease 0.2s',
        }}>
          Software Developer · Full-Stack &amp; AI Integration
        </p>

        {/* Enter button */}
        <div style={{
          opacity: phase === 'ready' ? 1 : 0,
          transform: phase === 'ready' ? 'translateY(0)' : 'translateY(10px)',
          transition: 'all 0.4s ease 0.3s',
        }}>
          <button
            onClick={handleEnter}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 28px',
              borderRadius: '50px',
              background: 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(0,212,255,0.12))',
              border: '1px solid rgba(167,139,250,0.3)',
              color: '#a78bfa',
              fontSize: '14px',
              fontWeight: 600,
              fontFamily: 'Inter, sans-serif',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              letterSpacing: '0.5px',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(167,139,250,0.2), rgba(0,212,255,0.2))';
              e.currentTarget.style.borderColor = 'rgba(167,139,250,0.5)';
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 30px rgba(167,139,250,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(0,212,255,0.12))';
              e.currentTarget.style.borderColor = 'rgba(167,139,250,0.3)';
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            Explore Portfolio <ArrowRight size={16} />
          </button>

          <p style={{
            fontSize: '11px',
            color: '#2a3a58',
            marginTop: '16px',
            fontWeight: 500,
          }}>
            Click the button above to enter
          </p>
        </div>
      </div>
    </div>
  );
}
