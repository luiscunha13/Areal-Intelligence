'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sun, Moon } from 'lucide-react';

interface NavbarProps {
  asofDate?: string;
  regime?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ asofDate }) => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const pathname = usePathname();

  useEffect(() => {
    const savedTheme = (localStorage.getItem('theme') as 'dark' | 'light') || 'dark';
    setTheme(savedTheme);
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const navItems = [
    { name: 'Macro Engine', href: '/macro' },
    { name: 'Sectors', href: '/sectors' },
    { name: 'Stock Screener', href: '/stocks' },
    { name: 'Candidates', href: '/candidates' },
    { name: 'Entry Timing', href: '/entry' },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border-color)] bg-[var(--bg-main)]/90 backdrop-blur-sm transition-colors">
      <div className="w-full flex items-center justify-between px-4 py-3 sm:px-6">
        
        {/* Brand & Navigation */}
        <div className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-2.5 group">
            <div className="h-3 w-3 rounded-full bg-blue-600 dark:bg-blue-500 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-semibold tracking-tight text-[var(--text-main)] font-mono">
              Areal Intelligence
            </span>
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-5 text-xs">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`transition-colors ${
                    isActive
                      ? 'font-bold text-[var(--text-main)]'
                      : 'font-normal text-gray-500 hover:text-[var(--text-main)] dark:text-gray-400 dark:hover:text-white'
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Controls */}
        <div className="flex items-center space-x-4 text-xs font-mono">
          {/* Theme Switcher Button */}
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-1 text-gray-500 hover:text-[var(--text-main)] dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4 text-slate-700" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

