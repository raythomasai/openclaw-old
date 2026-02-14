'use client';

import React from 'react';
import styles from './StatCard.module.css';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: {
    value: number;
    label: string;
  };
  icon?: React.ReactNode;
  color?: 'primary' | 'cyan' | 'emerald' | 'amber' | 'rose';
}

export default function StatCard({ title, value, subtitle, change, icon, color = 'primary' }: StatCardProps) {
  return (
    <div className={`card ${styles.statCard}`}>
      <div className={styles.header}>
        <span className={styles.title}>{title}</span>
        {icon && <div className={`${styles.icon} ${styles[color]}`}>{icon}</div>}
      </div>
      <div className={`${styles.value} ${styles[color]}`}>{value}</div>
      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
      {change && (
        <div className={`${styles.change} ${change.value >= 0 ? styles.positive : styles.negative}`}>
          <span>{change.value >= 0 ? '↑' : '↓'} {Math.abs(change.value)}%</span>
          <span className={styles.changeLabel}>{change.label}</span>
        </div>
      )}
    </div>
  );
}
