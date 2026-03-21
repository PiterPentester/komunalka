/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { motion } from 'motion/react';
import {
  Github,
  Terminal,
  Server,
  Smartphone,
  Globe,
  ShieldCheck,
  Bot,
  FileText,
  Mail,
  BarChart3,
  Cpu,
  ArrowRight
} from 'lucide-react';

const features = [
  {
    title: 'Smart Integration',
    description: 'Automatically fetches receipt emails (PDF/Images) using Gmail API or Nylas.',
    icon: <Mail className="w-6 h-6 text-cyan-400" />
  },
  {
    title: 'Advanced Data Extraction',
    description: 'Uses pdfplumber and pytesseract (OCR) with highly optimized regex for Ukrainian utility providers.',
    icon: <FileText className="w-6 h-6 text-purple-400" />
  },
  {
    title: 'Modern Dashboard',
    description: 'High-performance dashboard with Chart.js, featuring stacked area trends and synchronized color coding.',
    icon: <BarChart3 className="w-6 h-6 text-emerald-400" />
  },
  {
    title: 'Mobile Friendly',
    description: 'Specifically optimized for the Pixel 3a and other small screens.',
    icon: <Smartphone className="w-6 h-6 text-pink-400" />
  },
  {
    title: 'Internationalization',
    description: 'Complete support for Ukrainian and English (UI and service types).',
    icon: <Globe className="w-6 h-6 text-blue-400" />
  },
  {
    title: 'Secure & Production Ready',
    description: 'Optimized multi-stage Docker builds. Multi-arch support (AMD64/ARM64) for edge devices like Orange Pi.',
    icon: <ShieldCheck className="w-6 h-6 text-orange-400" />
  },
  {
    title: 'Automation',
    description: 'Daily background scans, Telegram bot notifications, and automated CI/CD pushing to GHCR.',
    icon: <Bot className="w-6 h-6 text-yellow-400" />
  },
  {
    title: 'Kubernetes Native',
    description: 'Ready for k3s deployment with PersistentVolumeClaims for SQLite and attachments.',
    icon: <Server className="w-6 h-6 text-indigo-400" />
  }
];

const techStack = [
  { name: 'Python 3.12+', icon: <Terminal className="w-8 h-8" /> },
  { name: 'FastAPI', icon: <Server className="w-8 h-8" /> },
  { name: 'Tesseract OCR', icon: <FileText className="w-8 h-8" /> },
  { name: 'Docker', icon: <ShieldCheck className="w-8 h-8" /> },
  { name: 'Kubernetes', icon: <Server className="w-8 h-8" /> },
  { name: 'Orange Pi 5', icon: <Cpu className="w-8 h-8" /> },
];

export default function App() {
  return (
    <div className="min-h-screen bg-[#050505] text-slate-300 font-sans selection:bg-cyan-500/30 overflow-x-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-900/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-900/20 blur-[120px]" />
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle at center, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-white/5 bg-black/50 backdrop-blur-md sticky top-0">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">Komunalka</span>
          </div>
          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/PiterPentester/komunalka" 
              target="_blank" 
              rel="noreferrer"
              className="text-sm font-medium hover:text-white transition-colors flex items-center gap-2"
            >
              <Github className="w-4 h-4" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-cyan-400 mb-8"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              Production Ready v1.0
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-7xl font-bold text-white tracking-tighter mb-6 leading-tight"
            >
              Automate Your <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600">
                Utility Receipts
              </span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
            >
              A full-stack Python web application to automate utility receipt tracking from Gmail/Nylas, designed with modern aesthetics and production-ready infrastructure.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <a 
                href="https://github.com/PiterPentester/komunalka"
                target="_blank"
                rel="noreferrer"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-white text-black font-semibold hover:bg-slate-200 transition-colors flex items-center justify-center gap-2"
              >
                <Github className="w-5 h-5" />
                View Repository
              </a>
              <a 
                href="#features"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-white/5 border border-white/10 text-white font-semibold hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
              >
                Explore Features
                <ArrowRight className="w-5 h-5" />
              </a>
            </motion.div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="py-24 px-6 bg-black/20 border-y border-white/5">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">Powerful Capabilities</h2>
              <p className="text-slate-400 max-w-2xl mx-auto">Built for performance, security, and ease of use on any device.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors group"
                >
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="py-24 px-6">
          <div className="max-w-7xl mx-auto text-center">
            <h2 className="text-2xl font-semibold text-white mb-12 tracking-tight">Powered by Modern Tech</h2>
            <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-60">
              {techStack.map((tech, index) => (
                <div key={index} className="flex flex-col items-center gap-3 hover:opacity-100 transition-opacity cursor-default">
                  {tech.icon}
                  <span className="text-sm font-medium font-mono">{tech.name}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Deployment & Architecture */}
        <section className="py-24 px-6 bg-gradient-to-b from-transparent to-cyan-950/20">
          <div className="max-w-5xl mx-auto">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
              >
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 tracking-tight">Built for the Edge</h2>
                <p className="text-slate-400 mb-6 leading-relaxed">
                  Komunalka is designed to run efficiently on low-power devices like the Orange Pi 5. With optimized multi-stage Docker builds and Kubernetes manifests included, deploying to your home lab is seamless.
                </p>
                <ul className="space-y-4">
                  {[
                    'Multi-arch support (AMD64/ARM64)',
                    'Memory tuned for 512Mi-1Gi limits',
                    'PersistentVolumeClaims for SQLite',
                    'Automated CI/CD via GitHub Actions'
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-3 text-sm font-medium text-slate-300">
                      <div className="w-5 h-5 rounded-full bg-cyan-500/20 flex items-center justify-center">
                        <ShieldCheck className="w-3 h-3 text-cyan-400" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="relative"
              >
                <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 blur-3xl" />
                <div className="relative rounded-2xl border border-white/10 bg-black/80 backdrop-blur-xl p-6 font-mono text-sm text-cyan-400 overflow-hidden">
                  <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-4">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <pre className="overflow-x-auto">
                    <code>
                      <span className="text-slate-500"># 1. Clone the repository</span><br/>
                      <span className="text-pink-400">git</span> clone https://github.com/PiterPentester/komunalka<br/>
                      <span className="text-pink-400">cd</span> komunalka<br/><br/>
                      <span className="text-slate-500"># 2. Build for ARM64</span><br/>
                      <span className="text-cyan-400">make</span> docker-arm64-build<br/><br/>
                      <span className="text-slate-500"># 3. Deploy to k3s</span><br/>
                      <span className="text-cyan-400">make</span> k8s-deploy
                    </code>
                  </pre>
                </div>
              </motion.div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-black/50 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-slate-500" />
            <span className="font-semibold text-slate-400">Komunalka Dashboard</span>
          </div>
          <p className="text-sm text-slate-500">
            Created by <a href="https://github.com/PiterPentester" target="_blank" rel="noreferrer" className="text-white hover:underline">PiterPentester</a>
          </p>
        </div>
      </footer>
    </div>
  );
}

