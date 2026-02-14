'use client';

import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatCard from './components/StatCard';
import SystemMetrics from './components/SystemMetrics';
import ProjectList from './components/ProjectList';
import ActivityFeed from './components/ActivityFeed';
import QuickActions from './components/QuickActions';
import styles from './page.module.css';

// Generate mock system metrics data
const generateMetricsData = () => {
  const data = [];
  const now = new Date();
  for (let i = 11; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 5 * 60000);
    data.push({
      time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      cpu: Math.floor(Math.random() * 40) + 20,
      memory: Math.floor(Math.random() * 30) + 45,
      network: Math.floor(Math.random() * 50) + 10,
    });
  }
  return data;
};

// Mock data
const projects = [
  {
    name: 'Dashboard',
    status: 'active' as const,
    progress: 75,
    lastUpdated: 'just now',
    description: 'Personal command center dashboard',
  },
  {
    name: 'Alpaca Trading',
    status: 'active' as const,
    progress: 100,
    lastUpdated: '2 hours ago',
    description: 'Automated trading system - LIVE',
  },
  {
    name: 'OpenClaw Gateway',
    status: 'active' as const,
    progress: 100,
    lastUpdated: '1 day ago',
    description: 'AI assistant infrastructure',
  },
];

const initialActivities = [
  {
    id: '1',
    type: 'success' as const,
    message: 'Dashboard deployed successfully',
    timestamp: 'just now',
    source: 'System',
  },
  {
    id: '2',
    type: 'info' as const,
    message: 'System metrics collection started',
    timestamp: '2 min ago',
    source: 'Monitoring',
  },
  {
    id: '3',
    type: 'success' as const,
    message: 'Trading daemon running',
    timestamp: '1 hour ago',
    source: 'Alpaca',
  },
  {
    id: '4',
    type: 'info' as const,
    message: 'OpenClaw gateway healthy',
    timestamp: '3 hours ago',
    source: 'Gateway',
  },
];

const quickActions = [
  { label: 'View Logs', icon: '📋', color: 'primary' as const },
  { label: 'System Status', icon: '💻', color: 'cyan' as const },
  { label: 'Trading View', icon: '📈', color: 'emerald' as const },
  { label: 'Settings', icon: '⚙️', color: 'amber' as const },
];

export default function Home() {
  const [metricsData, setMetricsData] = useState(generateMetricsData());
  const [activities] = useState(initialActivities);
  const [uptime, setUptime] = useState('0:00:00');
  const [startTime] = useState(new Date());

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setMetricsData(prev => {
        const newData = [...prev.slice(1)];
        const now = new Date();
        newData.push({
          time: now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          cpu: Math.floor(Math.random() * 40) + 20,
          memory: Math.floor(Math.random() * 30) + 45,
          network: Math.floor(Math.random() * 50) + 10,
        });
        return newData;
      });
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Update uptime
  useEffect(() => {
    const interval = setInterval(() => {
      const diff = Math.floor((Date.now() - startTime.getTime()) / 1000);
      const hours = Math.floor(diff / 3600);
      const minutes = Math.floor((diff % 3600) / 60);
      const seconds = diff % 60;
      setUptime(`${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const latestMetrics = metricsData[metricsData.length - 1];

  return (
    <div className={styles.container}>
      <Header />
      
      <main className={styles.main}>
        {/* Stats Row */}
        <section className={`${styles.statsGrid} stagger-children`}>
          <StatCard
            title="Active Projects"
            value={projects.length}
            subtitle="All systems operational"
            icon="📁"
            color="primary"
          />
          <StatCard
            title="CPU Usage"
            value={`${latestMetrics?.cpu || 0}%`}
            subtitle="Average load"
            icon="⚡"
            color="cyan"
            change={{ value: -5, label: 'vs last hour' }}
          />
          <StatCard
            title="Memory"
            value={`${latestMetrics?.memory || 0}%`}
            subtitle="8.2 GB / 16 GB"
            icon="💾"
            color="emerald"
          />
          <StatCard
            title="Uptime"
            value={uptime}
            subtitle="Session duration"
            icon="⏱️"
            color="amber"
          />
        </section>

        {/* Main Dashboard Grid */}
        <section className={styles.dashboardGrid}>
          <SystemMetrics data={metricsData} />
          <ProjectList projects={projects} />
          <ActivityFeed activities={activities} />
          <QuickActions actions={quickActions} />
        </section>
      </main>

      <footer className={styles.footer}>
        <span>Command Center v1.0</span>
        <span>•</span>
        <span>Powered by OpenClaw</span>
      </footer>
    </div>
  );
}
