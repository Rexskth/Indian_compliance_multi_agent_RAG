"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Copy, RefreshCw, Loader2, CheckCircle2 } from "lucide-react";
import { ChatMessage, Citation, QueryResponse } from "@/types";
import { sendQueryStream } from "@/lib/api";
import { cn, formatDate, getRiskColor, getRiskLabel } from "@/lib/utils";

interface StageInfo {
  stage: string;
  message: string;
  completed: boolean;
}

interface ChatInterfaceProps {
  className?: string;
}

const STAGES = [
  { key: "searching", label: "Searching documents", icon: "🔍" },
  { key: "analyzing", label: "Analyzing legal context", icon: "⚖️" },
  { key: "risk_assessment", label: "Assessing risk factors", icon: "📊" },
  { key: "validating", label: "Validating citations", icon: "✅" },
  { key: "generating", label: "Generating response", icon: "✍️" },
];

export function ChatInterface({ className }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStage, setCurrentStage] = useState<StageInfo[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const resetStages = () => {
    setCurrentStage(STAGES.map((s) => ({ stage: s.key, message: s.label, completed: false })));
  };

  const updateStage = (stageKey: string) => {
    setCurrentStage((prev) =>
      prev.map((s) => ({
        ...s,
        completed: s.stage === stageKey ? true : s.completed,
      }))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);
    resetStages();

    sendQueryStream(
      {
        query: userMessage.content,
        conversation_history: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      },
      (data) => {
        if (data.stage) {
          updateStage(data.stage);
          const stageInfo = STAGES.find((s) => s.key === data.stage);
          if (stageInfo) {
            setCurrentStage((prev) =>
              prev.map((s) =>
                s.stage === data.stage ? { ...s, message: data.message || s.message } : s
              )
            );
          }
        }
      },
      (response) => {
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.answer,
          timestamp: new Date(),
          citations: response.citations,
          risk_level: response.risk_level,
          confidence: response.confidence,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setIsLoading(false);
        setCurrentStage([]);
      },
      (err) => {
        setError(err.message);
        setIsLoading(false);
        setCurrentStage([]);
      }
    );
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className={cn("flex flex-col h-full bg-surface-light dark:bg-surface-dark", className)}>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center p-8"
            >
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Indian Compliance Assistant
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-md">
                Ask questions about DPDPA 2023, IT Act 2000, and Companies Act 2013.
                Get accurate, citation-grounded legal information.
              </p>
            </motion.div>
          )}

          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-3",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              {message.role === "assistant" && (
                <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                </div>
              )}

              <div
                className={cn(
                  "max-w-[80%] rounded-2xl p-4",
                  message.role === "user"
                    ? "bg-primary-600 text-white"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                )}
              >
                <div className="flex items-start gap-3">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <button
                    onClick={() => copyToClipboard(message.content)}
                    className="opacity-50 hover:opacity-100 transition-opacity"
                    title="Copy"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>

                {message.role === "assistant" && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    {message.citations && message.citations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Sources:
                        </p>
                        {message.citations.slice(0, 3).map((citation, idx) => (
                          <div
                            key={idx}
                            className="text-xs bg-white dark:bg-gray-900 p-2 rounded border border-gray-200 dark:border-gray-700"
                          >
                            <span className="font-medium">
                              {citation.document_name || citation.source}
                            </span>
                            {citation.section && citation.section !== "N/A" && (
                              <span> - {citation.section}</span>
                            )}
                            <span className="text-gray-500"> (p.{citation.page})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <p className="text-xs opacity-50 mt-2">
                  {formatDate(message.timestamp)}
                </p>
              </div>

              {message.role === "user" && (
                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </div>
              )}
            </motion.div>
          ))}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl p-4 min-w-[280px]">
                <div className="flex items-center gap-2 text-gray-500 mb-3">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-medium">Processing...</span>
                </div>
                <div className="space-y-2">
                  {currentStage.map((stage, idx) => (
                    <motion.div
                      key={stage.stage}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className={cn(
                        "flex items-center gap-2 text-sm",
                        stage.completed
                          ? "text-green-600 dark:text-green-400"
                          : "text-gray-500 dark:text-gray-400"
                      )}
                    >
                      {stage.completed ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : idx === currentStage.findIndex((s) => !s.completed) ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <div className="w-3 h-3" />
                      )}
                      <span>{stage.message}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-xl"
          >
            {error}
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 dark:border-gray-800 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about Indian compliance laws..."
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white rounded-xl transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}