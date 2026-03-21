"use client";

import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import RoadmapFlow from '@/components/RoadmapFlow';
import WelcomeOverlay from '@/components/WelcomeOverlay';
import { ReactFlowProvider } from '@xyflow/react';

export default function Home() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  React.useEffect(() => {
    if (window.innerWidth <= 1024) {
      setSidebarCollapsed(true);
    }
  }, []);

  return (
    <ReactFlowProvider>
      {/* Welcome Overlay */}
      {showWelcome && (
        <WelcomeOverlay onComplete={() => setShowWelcome(false)} />
      )}

      {/* Desktop / Tablet Layout */}
      <main className="portfolio-main">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          onOpenCommand={() => {
            // Dispatch Ctrl+K equivalent via keyboard event
            const event = new KeyboardEvent('keydown', {
              key: 'k',
              ctrlKey: true,
              bubbles: true,
            });
            window.dispatchEvent(event);
          }}
        />
        <RoadmapFlow
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed(false)}
        />
      </main>

      {/* Mobile Layout */}
    </ReactFlowProvider>
  );
}
