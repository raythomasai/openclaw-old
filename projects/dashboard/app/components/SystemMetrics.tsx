'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import styles from './SystemMetrics.module.css';

interface MetricData {
  time: string;
  cpu: number;
  memory: number;
  network: number;
}

interface SystemMetricsProps {
  data: MetricData[];
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; dataKey: string }>; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className={styles.tooltip}>
        <p className={styles.tooltipLabel}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className={styles.tooltipValue} style={{ color: getColor(entry.dataKey) }}>
            {entry.dataKey}: {entry.value}%
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const getColor = (key: string) => {
  switch (key) {
    case 'cpu': return '#6366f1';
    case 'memory': return '#06b6d4';
    case 'network': return '#10b981';
    default: return '#8b5cf6';
  }
};

export default function SystemMetrics({ data }: SystemMetricsProps) {
  const latestData = data[data.length - 1] || { cpu: 0, memory: 0, network: 0 };

  return (
    <div className={`card ${styles.container}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>System Metrics</h3>
        <div className={styles.legend}>
          <span className={styles.legendItem}><span className={styles.dot} style={{ background: '#6366f1' }}></span>CPU</span>
          <span className={styles.legendItem}><span className={styles.dot} style={{ background: '#06b6d4' }}></span>Memory</span>
          <span className={styles.legendItem}><span className={styles.dot} style={{ background: '#10b981' }}></span>Network</span>
        </div>
      </div>
      
      <div className={styles.currentStats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>CPU</span>
          <span className={styles.statValue} style={{ color: '#6366f1' }}>{latestData.cpu}%</span>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${latestData.cpu}%`, background: '#6366f1' }}></div>
          </div>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Memory</span>
          <span className={styles.statValue} style={{ color: '#06b6d4' }}>{latestData.memory}%</span>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${latestData.memory}%`, background: '#06b6d4' }}></div>
          </div>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Network</span>
          <span className={styles.statValue} style={{ color: '#10b981' }}>{latestData.network}%</span>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${latestData.network}%`, background: '#10b981' }}></div>
          </div>
        </div>
      </div>

      <div className={styles.chartContainer}>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="networkGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="time" 
              stroke="#64748b" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="cpu" stroke="#6366f1" strokeWidth={2} fill="url(#cpuGradient)" />
            <Area type="monotone" dataKey="memory" stroke="#06b6d4" strokeWidth={2} fill="url(#memoryGradient)" />
            <Area type="monotone" dataKey="network" stroke="#10b981" strokeWidth={2} fill="url(#networkGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
