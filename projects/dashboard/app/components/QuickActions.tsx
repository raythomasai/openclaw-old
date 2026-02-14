'use client';

import React from 'react';
import styles from './QuickActions.module.css';

interface Action {
  label: string;
  icon: string;
  color: 'primary' | 'cyan' | 'emerald' | 'amber' | 'rose';
  onClick?: () => void;
}

interface QuickActionsProps {
  actions: Action[];
}

export default function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div className={`card ${styles.container}`}>
      <h3 className={styles.title}>Quick Actions</h3>
      <div className={styles.grid}>
        {actions.map((action, index) => (
          <button 
            key={index} 
            className={`${styles.actionButton} ${styles[action.color]}`}
            onClick={action.onClick}
          >
            <span className={styles.icon}>{action.icon}</span>
            <span className={styles.label}>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
