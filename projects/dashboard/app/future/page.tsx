'use client';

import React, { useState, useEffect } from 'react';
import styles from './page.module.css';

interface FutureProject {
  name: string;
  status: 'Backlog' | 'In Progress' | 'Planned' | 'Idea';
  description: string;
  ideas?: string[];
  nextSteps?: string[];
}

const projects: FutureProject[] = [
  {
    name: 'google-antigravity/gemini-3-flash',
    status: 'Backlog',
    description: 'GitHub repository exploration and analysis',
    ideas: [
      'Review project structure and architecture',
      'Understand core functionality',
      'Identify potential use cases',
    ],
  },
  {
    name: 'Apple Notes Integration',
    status: 'Backlog',
    description: 'Integrate with Apple Notes via memo CLI for creating, reading, and managing notes',
    ideas: [
      'Grant Automation permissions in System Settings',
      'Create note creation workflow',
      'Implement note search and retrieval',
      'Export notes functionality',
    ],
  },
  {
    name: 'Reverse Heartbeat Feature',
    status: 'Backlog',
    description: 'System that checks on Jarvis periodically instead of Jarvis checking in',
    ideas: [
      'Wake Jarvis with prompts on a schedule',
      'Proactive status updates to user',
      'Periodic self-health checks',
    ],
  },
  {
    name: 'Browser for Nanobanana & CEO',
    status: 'Backlog',
    description: 'Research and identify browser requirements for nanobanana and CEO projects',
    ideas: [
      'Identify browser needs for each project',
      'Compare available browser options',
      'Test compatibility and performance',
    ],
  },
  {
    name: 'Reels Generator',
    status: 'Backlog',
    description: 'Create social media reels automatically - video clips, captions, music, and effects',
    ideas: [
      'Video clip extraction and editing',
      'Auto-generated captions and text overlays',
      'Music/soundtrack integration',
      'Export for Instagram, TikTok, YouTube Shorts',
    ],
  },
  {
    name: 'Calorie Counter',
    status: 'Backlog',
    description: 'Simple calorie tracking system - log meals, track daily/weekly intake',
    ideas: [
      'CLI interface for quick entry',
      'Voice memo entry support',
      'Visual dashboard of trends',
      'Apple Health sync',
    ],
    nextSteps: [
      'Define data model (meals, foods, totals)',
      'Choose storage (local JSON, sqlite, or cloud)',
      'Build basic CLI for entry/lookup',
      'Add voice memo input',
    ],
  },
  {
    name: 'eBay Posting Automation',
    status: 'Backlog',
    description: 'Automate listing items on eBay - list from photos/inventory',
    ideas: [
      'Photo upload and listing creation',
      'Template-based descriptions',
      'Schedule posts for best times',
      'Cross-post to Facebook Marketplace, Craigslist',
      'Price suggestions based on market data',
    ],
    nextSteps: [
      'Research eBay API for listing creation',
      'Design workflow for item listing',
      'Build photo upload and description generator',
      'Add scheduling and cross-posting',
    ],
  },
];

const businessIdeas = [
  {
    name: 'Distributed GPU Farming',
    description: 'Like Folding@home but for profit - lease spare GPU cycles for AI training, protein folding, rendering, or scientific compute',
  },
  {
    name: 'Distributed Storage Network',
    description: 'Peer-to-peer storage marketplace - rent out unused disk space similar to Filecoin/Storj',
  },
  {
    name: 'DTC Brands Directory',
    description: 'A curated directory of DTC companies, searchable by category',
  },
  {
    name: 'Directory of Dukes',
    description: 'A directory of people with the title "Duke" (aristocratic title)',
  },
];

export default function FuturePage() {
  const [projectsState, setProjectsState] = useState(projects);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>🚀 Future Projects</h1>
        <p>Ideas and planned projects to work on</p>
      </header>

      <main className={styles.main}>
        {/* Project Cards */}
        <section className={styles.section}>
          <h2>Active Projects</h2>
          <div className={styles.projectGrid}>
            {projectsState.map((project, index) => (
              <div key={index} className={styles.projectCard}>
                <div className={styles.projectHeader}>
                  <h3>{project.name}</h3>
                  <span className={`${styles.status} ${styles[project.status.toLowerCase().replace(' ', '-')]}`}>
                    {project.status}
                  </span>
                </div>
                <p className={styles.description}>{project.description}</p>
                
                {project.ideas && (
                  <div className={styles.ideasSection}>
                    <h4>Ideas</h4>
                    <ul>
                      {project.ideas.map((idea, i) => (
                        <li key={i}>{idea}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {project.nextSteps && (
                  <div className={styles.nextStepsSection}>
                    <h4>Next Steps</h4>
                    <ul>
                      {project.nextSteps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Business Ideas */}
        <section className={styles.section}>
          <h2>💡 Business Ideas</h2>
          <div className={styles.businessGrid}>
            {businessIdeas.map((idea, index) => (
              <div key={index} className={styles.businessCard}>
                <h3>{idea.name}</h3>
                <p>{idea.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Add New Project */}
        <section className={styles.section}>
          <h2>Add New Project</h2>
          <div className={styles.addForm}>
            <input type="text" placeholder="Project name..." className={styles.input} />
            <select className={styles.select}>
              <option>Backlog</option>
              <option>Planned</option>
              <option>Idea</option>
            </select>
            <button className={styles.button}>Add</button>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <span>Future Projects v1.0</span>
        <span>•</span>
        <span>Powered by OpenClaw</span>
      </footer>
    </div>
  );
}
