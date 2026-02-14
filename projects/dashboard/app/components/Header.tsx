'use client';

import React from 'react';
import Link from 'next/link';
import styles from './Header.module.css';

export default function Header() {
  const [currentTime, setCurrentTime] = React.useState(new Date());

  React.useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <header className={styles.header}>
      <div className={styles.titleSection}>
        <div className={styles.logoContainer}>
          <div className={styles.logo}>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h1 className={styles.title}>Command Center</h1>
            <p className={styles.subtitle}>Personal Dashboard</p>
          </div>
        </div>
      </div>
      
      <nav className={styles.nav}>
        <Link href="/" className={styles.navLink}>Home</Link>
        <Link href="/todo" className={styles.navLink}>Todo</Link>
        <Link href="/scholar" className={styles.navLink}>Scholar</Link>
        <Link href="/future" className={styles.navLink}>Future</Link>
      </nav>
      
      <div className={styles.timeSection}>
        <div className={styles.time}>{formatTime(currentTime)}</div>
        <div className={styles.date}>{formatDate(currentTime)}</div>
      </div>
      <div className={styles.statusSection}>
        <div className={styles.statusItem}>
          <span className={`${styles.statusDot} ${styles.online}`}></span>
          <span>System Online</span>
        </div>
      </div>
    </header>
  );
}
