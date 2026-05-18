"use client";

import { useState, useEffect } from "react";
import { ChatInterface } from "@/components/ChatInterface";
import { Menu, X, Moon, Sun, Scale, Info } from "lucide-react";
import { checkHealth } from "@/lib/api";
import { motion } from "framer-motion";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [health, setHealth] = useState<{ status: string; collection_count: number } | null>(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "error", collection_count: 0 }));
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-2">
            <Scale className="w-6 h-6 text-primary-600" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Indian Compliance RAG
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {health && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <div
                className={`w-2 h-2 rounded-full ${
                  health.status === "healthy" ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span>{health.collection_count} documents</span>
            </div>
          )}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <motion.aside
          initial={false}
          animate={{ x: sidebarOpen ? 0 : -280 }}
          className="w-[280px] bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-4 overflow-y-auto"
        >
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Supported Laws
          </div>
          <div className="space-y-2">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                DPDPA 2023
              </h3>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                Digital Personal Data Protection Act
              </p>
            </div>
            <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <h3 className="font-medium text-purple-900 dark:text-purple-100">
                IT Act 2000
              </h3>
              <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                Information Technology Act
              </p>
            </div>
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-medium text-green-900 dark:text-green-100">
                Companies Act 2013
              </h3>
              <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                Corporate governance laws
              </p>
            </div>
          </div>

          <div className="mt-auto p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <Info className="w-4 h-4" />
              <span>Version 1.0.0</span>
            </div>
          </div>
        </motion.aside>

        <main className="flex-1 overflow-hidden">
          <ChatInterface className="h-full" />
        </main>
      </div>
    </div>
  );
}