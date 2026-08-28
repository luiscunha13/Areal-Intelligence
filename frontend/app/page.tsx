'use client';

import React from 'react';
import Link from 'next/link';
import { Navbar } from '../components/Navbar';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar />

      <main className="flex flex-1 items-center px-6 py-24 sm:px-12 lg:px-16">
        <div className="max-w-6xl w-full space-y-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-3 sm:space-x-5 lg:space-x-6">
              <div className="h-8 w-8 sm:h-10 sm:w-10 md:h-12 md:w-12 lg:h-14 lg:w-14 xl:h-16 xl:w-16 rounded-full bg-blue-600 dark:bg-blue-500 flex-shrink-0" />
              <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight text-slate-900 dark:text-white leading-none whitespace-nowrap">
                Areal Intelligence
              </h1>
            </div>
            <p className="max-w-xl text-lg sm:text-xl text-gray-500 dark:text-gray-400 font-light leading-relaxed pt-2">
              Quantitative macroeconomic intelligence engine, market regime analysis, and systematic asset allocation platform.
            </p>
          </div>

          <div className="pt-2">
            <Link
              href="/macro"
              className="inline-flex items-center space-x-2 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
            >
              <span>Explore Macro Engine</span>
              <span className="text-base">→</span>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

