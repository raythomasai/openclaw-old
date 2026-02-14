'use client';

import React from 'react';
import styles from './ActivityFeed.module.css';

interface Activity {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
  source?: string;
}

interface ActivityFeedProps {
  activities: Activity[];
}

const typeIcons: Record<string, string> = {
  info: '💡',
  success: '✅',
  warning: '⚠️',
  error: '❌',
};

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  return (
    <div className={`card ${styles.container}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>Activity Feed</h3>
        <span className={styles.liveIndicator}>
          <span className={styles.liveDot}></span>
          Live
        </span>
      </div>
      
      <div className={styles.feed}>
        {activities.map((activity) => (
          <div key={activity.id} className={`${styles.activity} ${styles[activity.type]}`}>
            <span className={styles.icon}>{typeIcons[activity.type]}</span>
            <div className={styles.content}>
              <p className={styles.message}>{activity.message}</p>
              <div className={styles.meta}>
                {activity.source && <span className={styles.source}>{activity.source}</span>}
                <span className={styles.timestamp}>{activity.timestamp}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
