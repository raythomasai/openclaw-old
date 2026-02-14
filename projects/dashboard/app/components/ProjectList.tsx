'use client';

import React from 'react';
import styles from './ProjectList.module.css';

interface Project {
  name: string;
  status: 'active' | 'completed' | 'pending' | 'error';
  progress: number;
  lastUpdated: string;
  description?: string;
}

interface ProjectListProps {
  projects: Project[];
}

const statusColors: Record<string, string> = {
  active: 'var(--accent-emerald)',
  completed: 'var(--accent-primary)',
  pending: 'var(--accent-amber)',
  error: 'var(--accent-rose)',
};

export default function ProjectList({ projects }: ProjectListProps) {
  return (
    <div className={`card ${styles.container}`}>
      <div className={styles.header}>
        <h3 className={styles.title}>Active Projects</h3>
        <span className={styles.count}>{projects.length} projects</span>
      </div>
      
      <div className={styles.list}>
        {projects.map((project, index) => (
          <div key={index} className={styles.projectItem}>
            <div className={styles.projectHeader}>
              <div className={styles.projectInfo}>
                <span 
                  className={styles.statusDot} 
                  style={{ background: statusColors[project.status] }}
                ></span>
                <span className={styles.projectName}>{project.name}</span>
              </div>
              <span className={`${styles.badge} ${styles[project.status]}`}>
                {project.status}
              </span>
            </div>
            
            {project.description && (
              <p className={styles.description}>{project.description}</p>
            )}
            
            <div className={styles.progressSection}>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill} 
                  style={{ 
                    width: `${project.progress}%`,
                    background: statusColors[project.status]
                  }}
                ></div>
              </div>
              <span className={styles.progressText}>{project.progress}%</span>
            </div>
            
            <span className={styles.lastUpdated}>Updated {project.lastUpdated}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
